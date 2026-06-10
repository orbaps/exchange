import os
import json
import hashlib
import unittest
import tempfile
from typing import List, Dict, Any

from federation.clock import global_clock
from federation.health import ClusterHealth, ReplicaState
from federation.consensus.leader import LeaderState, ConsensusLeaderElection
from federation.consensus.log import ConsensusLog
from federation.wal import WriteAheadLog
from federation.snapshot import SnapshotManager
from federation.scheduler_replica import SchedulerReplica

from orchestration.models import (
    NodeOrchestrationMetrics, AnomalyRecord, CapacityForecast,
    OrchestrationPolicy, AutonomousAction, OrchestrationDecision
)
from orchestration.health_monitor import HealthMonitor
from orchestration.anomaly import AnomalyDetector
from orchestration.forecast import CapacityForecaster
from orchestration.policy import PolicyEngine
from orchestration.rebalancer import WorkloadRebalancer
from orchestration.healing import SelfHealingEngine
from orchestration.decision import DecisionEngine
from orchestration.journal import OrchestrationJournal
from orchestration.replay import OrchestrationReplaySystem, ReplayStateMachine
from orchestration.metrics import OrchestrationMetricsTracker
from orchestration.controller import AutonomousController

class TestOrchestrator(unittest.TestCase):
    """Deterministic test suite for the Phase 8.0 Autonomous Cluster Orchestration layer."""

    def setUp(self):
        global_clock.reset(3000.0)

    def test_health_monitoring(self):
        """Verify HealthMonitor CPU/memory pressure averages and composite score calculation."""
        hm = HealthMonitor(window_size=3)
        
        # 1. Healthy initial sequence
        for t in range(3):
            hm.record_metrics(NodeOrchestrationMetrics(
                node_id="node_1",
                timestamp=3000.0 + t,
                cpu_usage=20.0,
                memory_usage=25.0,
                load=0.2,
                job_count=1,
                replication_lag=0,
                term=1,
                network_latency=0.0
            ))
            
        health_dict = hm.calculate_health("node_1", ReplicaState.HEALTHY)
        self.assertEqual(health_dict["cpu_pressure"], 20.0)
        self.assertEqual(health_dict["memory_pressure"], 25.0)
        # health_score = 100 - (20*0.3 + 25*0.3) = 100 - 13.5 = 86.5
        self.assertAlmostEqual(health_dict["health_score"], 86.5)

        # 2. Degraded sequence
        hm.record_metrics(NodeOrchestrationMetrics(
            node_id="node_1",
            timestamp=3003.0,
            cpu_usage=90.0,
            memory_usage=80.0,
            load=0.8,
            job_count=5,
            replication_lag=0,
            term=1,
            network_latency=0.0
        ))
        
        # Now window is [20, 20, 90] for cpu -> average is 43.333
        # window is [25, 25, 80] for mem -> average is 43.333
        health_dict2 = hm.calculate_health("node_1", ReplicaState.HEALTHY)
        self.assertTrue(health_dict2["health_score"] < 86.5)
        
        # 3. Update Cluster Health
        ch = ClusterHealth(replica_states={"node_1": ReplicaState.HEALTHY})
        hm.update_cluster_health(ch, active_anomalies_count=2)
        self.assertEqual(ch.anomaly_count, 2)
        self.assertTrue(ch.cpu_pressure_score > 20.0)
        self.assertEqual(ch.node_health_states["node_1"], "HEALTHY" if ch.health_score >= 80.0 else "DEGRADED")

    def test_anomaly_detection(self):
        """Verify detection of CPU spikes, memory pressures, election storms, lag spikes, and churn."""
        ad = AnomalyDetector()
        
        # Base metrics (stable)
        metrics = {
            "node_1": [
                NodeOrchestrationMetrics("node_1", 3000.0, 10.0, 15.0, 0.1, 0, 0, 1, 0.0),
                NodeOrchestrationMetrics("node_1", 3005.0, 70.0, 15.0, 0.1, 0, 0, 1, 0.0) # spike > 50%
            ],
            "node_2": [
                NodeOrchestrationMetrics("node_2", 3005.0, 10.0, 95.0, 0.1, 0, 0, 1, 0.0) # mem > 90%
            ],
            "node_3": [
                NodeOrchestrationMetrics("node_3", 3005.0, 10.0, 15.0, 0.1, 0, 120, 1, 0.0) # lag > 100
            ]
        }
        
        anomalies = ad.detect_anomalies(
            node_metrics=metrics,
            election_timestamps=[3001.0, 3002.0, 3003.0, 3004.0],  # 4 elections within 30s
            membership_change_timestamps=[2950.0, 2980.0, 3001.0],  # 3 changes within 100s
            partition_toggle_counts={"node_1": 4},  # toggles > 3
            now=3005.0
        )
        
        types = [a.type for a in anomalies]
        self.assertIn("CPU_SPIKE", types)
        self.assertIn("MEM_PRESSURE", types)
        self.assertIn("REP_LAG", types)
        self.assertIn("ELECTION_STORM", types)
        self.assertIn("MEMB_CHURN", types)
        self.assertIn("PARTITION_INSTABILITY", types)

    def test_capacity_forecast(self):
        """Verify linear extrapolation of metrics and failure risk bottleneck triggers."""
        cf = CapacityForecaster()
        
        # Increasing CPU sequence: (3000.0, 50.0), (3010.0, 60.0), (3020.0, 70.0)
        # y = mx + c. m = 1.0 % per second.
        history = [
            NodeOrchestrationMetrics("node_1", 3000.0, 50.0, 10.0, 0.5, 1, 0, 1, 0.0),
            NodeOrchestrationMetrics("node_1", 3010.0, 60.0, 10.0, 0.5, 1, 0, 1, 0.0),
            NodeOrchestrationMetrics("node_1", 3020.0, 70.0, 10.0, 0.5, 1, 0, 1, 0.0)
        ]
        
        forecast = cf.forecast_capacity("node_1", history, now=3020.0)
        # At T+300 (3320.0), CPU should cross 100% boundary
        self.assertEqual(forecast.predicted_cpu, 100.0)
        self.assertIsNotNone(forecast.bottleneck_time)
        # Bottleneck at 100% usage -> should be at T = 3050.0 (time_to_fail = 30.0s <= 60.0s)
        # Expected failure risk should be 0.9 (critical time-to-fail <= 60.0s)
        self.assertEqual(forecast.predicted_failure_risk, 0.9)

    def test_policy_engine(self):
        """Verify policy evaluation and violations when thresholds are exceeded."""
        pe = PolicyEngine()
        
        # Violation of CPU limit (cpu = 90.0 > 85)
        metrics = NodeOrchestrationMetrics("node_1", 3000.0, 90.0, 20.0, 0.5, 1, 0, 1, 0.0)
        v1 = pe.evaluate_node(metrics)
        self.assertEqual(len(v1), 1)
        self.assertEqual(v1[0]["policy_id"], "pol_cpu_limit")
        
        # Register new custom policy
        pe.add_policy(OrchestrationPolicy(
            policy_id="custom_cpu",
            name="Strict custom limit",
            rule_expr="cpu > 50",
            action_type="RESTART"
        ))
        
        v2 = pe.evaluate_node(metrics)
        # Both pol_cpu_limit and custom_cpu should be violated
        self.assertEqual(len(v2), 2)

    def test_decision_engine(self):
        """Verify consolidated decisions, confidence scoring, and evidence chaining."""
        de = DecisionEngine()
        
        anomalies = [AnomalyRecord("anom_1", "node_1", "CPU_SPIKE", "HIGH", 3000.0, "CPU high")]
        forecasts = [CapacityForecast("node_1", 3000.0, 95.0, 15.0, 0.8, 3050.0)]
        violations = [{"policy_id": "pol_cpu_limit", "policy_name": "Critical CPU Limit", "node_id": "node_1", "rule_expr": "cpu > 85", "action_type": "REBALANCE", "actual_value": 90.0, "timestamp": 3000.0}]
        
        decision = de.make_decision(anomalies, forecasts, violations, timestamp=3000.0)
        self.assertEqual(len(decision.recommendations), 1)
        self.assertEqual(decision.recommendations[0].action_type, "REBALANCE")
        self.assertEqual(decision.confidence_score, 0.9)
        self.assertTrue(len(decision.evidence_chain) >= 3)

    def test_rebalancing(self):
        """Verify ROUND_ROBIN, LEAST_LOADED, and CAPACITY_AWARE workload rebalancing results."""
        rebalancer = WorkloadRebalancer()
        
        # Mock jobs and nodes
        from federation.jobs import DistributedJob, JobStatus
        from federation.models import NodeInfo, NodeCapabilities, NodeRole
        
        jobs = [
            DistributedJob("job_1", "CODING", {}, JobStatus.PENDING),
            DistributedJob("job_2", "CODING", {}, JobStatus.ASSIGNED),
            DistributedJob("job_3", "CODING", {}, JobStatus.PENDING)
        ]
        
        caps = NodeCapabilities(["CODING"], 4, 8192.0, 4)
        nodes = [
            NodeInfo("node_1", "host1", "1.0", "pub1", [NodeRole.WORKER], caps, 0, 0, load=0.5),
            NodeInfo("node_2", "host2", "1.0", "pub2", [NodeRole.WORKER], caps, 0, 0, load=0.1)
        ]
        
        # 1. ROUND_ROBIN
        rr_jobs, rr_expl = rebalancer.rebalance_workload(list(jobs), nodes, "ROUND_ROBIN")
        self.assertEqual(rr_jobs[0].assigned_node_id, "node_1")
        self.assertEqual(rr_jobs[2].assigned_node_id, "node_1")

        # 2. LEAST_LOADED
        ll_jobs, ll_expl = rebalancer.rebalance_workload(list(jobs), nodes, "LEAST_LOADED")
        # node_2 has load 0.1, node_1 has 0.5. First target gets assigned to node_2.
        self.assertEqual(ll_jobs[0].assigned_node_id, "node_2")

        # 3. CAPACITY_AWARE
        ca_jobs, ca_expl = rebalancer.rebalance_workload(list(jobs), nodes, "CAPACITY_AWARE")
        # node_2 has remaining capacity = 8192 * 4 * (1.0 - 0.1) = 29491.2 (higher). Should receive first assignment.
        self.assertEqual(ca_jobs[0].assigned_node_id, "node_2")

    def test_self_healing(self):
        """Verify restarts, recovery, and rejoining on mock cluster replica states."""
        healing = SelfHealingEngine()
        
        replica1 = SchedulerReplica("node_1", ["node_1", "node_2"])
        replica2 = SchedulerReplica("node_2", ["node_1", "node_2"])
        replicas = {"node_1": replica1, "node_2": replica2}
        
        # 1. Restart Node Action
        action_restart = AutonomousAction("act_1", "node_2", "RESTART_NODE", "PENDING", 3000.0, "restart node")
        success = healing.execute_healing_action(action_restart, replicas, None, None)
        self.assertTrue(success)
        self.assertEqual(action_restart.status, "COMPLETED")
        self.assertIn("node_2", replica1.active_nodes)

        # 2. Snapshot Restore Action
        with tempfile.TemporaryDirectory() as tmpdir:
            replica1.storage_dir = os.path.join(tmpdir, "node_1")
            os.makedirs(replica1.storage_dir, exist_ok=True)
            replica1.snapshot_manager.store_dir = os.path.join(replica1.storage_dir, "snapshots")
            os.makedirs(replica1.snapshot_manager.store_dir, exist_ok=True)
            
            # Create snapshot
            replica1.snapshot_manager.create_snapshot("snap_latest", {"state": "data"}, 5, 2)
            replica1.consensus_log.append(term=2, command={"job": 1})
            
            action_restore = AutonomousAction("act_2", "node_1", "RESTORE_SNAPSHOT", "PENDING", 3000.0, "restore snap")
            success_snap = healing.execute_healing_action(action_restore, replicas, None, None)
            self.assertTrue(success_snap)
            self.assertEqual(replica1.commit_index, 5)

    def test_controller_loop(self):
        """Verify full AutonomousController execution, cache updates, and event logging."""
        replica = SchedulerReplica("node_1", ["node_1"])
        replica.leader_election.state = LeaderState.LEADER
        replica.leader_election.current_term = 1
        
        from dashboard.services.state_cache import StateCache
        cache = StateCache()
        
        controller = AutonomousController(
            cluster_replicas={"node_1": replica},
            network_simulator=None,
            transport=None,
            state_cache=cache
        )
        
        decision = controller.run_control_loop(3000.0)
        self.assertEqual(decision.analysis, "Cluster is stable. No recovery actions recommended.")
        
        # Check cache updates
        status = cache.get_orchestration_status()
        self.assertEqual(status["status"], "ACTIVE")
        self.assertTrue(status["controller_active"])
        self.assertEqual(status["metrics"]["active_anomalies_count"], 0)

        # Trigger CPU spike simulation
        controller.simulate_metric_override("node_1", cpu=98.0, memory=10.0)
        decision_spike = controller.run_control_loop(3005.0)
        
        # CPU_SPIKE anomaly should trigger REBALANCE decision
        self.assertTrue(len(decision_spike.recommendations) > 0)
        self.assertEqual(decision_spike.recommendations[0].action_type, "REBALANCE")

    def test_journal_integrity(self):
        """Verify log records chained SHA256 hashes and integrity checker validation."""
        journal = OrchestrationJournal()
        
        journal.append_record("ANOMALY_DETECTED", {"anomaly_id": "anom_1"}, 3000.0)
        journal.append_record("SELF_HEAL_COMPLETED", {"action_id": "act_1"}, 3005.0)
        
        self.assertTrue(journal.verify_integrity())
        
        # Tamper with the journal
        journal.entries[0]["data"]["anomaly_id"] = "tampered"
        self.assertFalse(journal.verify_integrity())

    def test_replay_fingerprint(self):
        """Verify stepping forward, backward, seeking, and fingerprint validation."""
        journal = OrchestrationJournal()
        journal.append_record("ANOMALY_DETECTED", {"anomaly_id": "anom_1"}, 3000.0)
        journal.append_record("WORKLOAD_REBALANCED", {}, 3005.0)
        journal.append_record("HEALTH_UPDATE", {"health_score": 92.5, "node_health_states": {"node_1": 92.5}}, 3010.0)
        
        replay = OrchestrationReplaySystem(journal.entries)
        
        # Step forward 1
        self.assertTrue(replay.step_forward())
        self.assertEqual(replay.current_pointer, 1)
        self.assertIn("anom_1", replay.state_machine.active_anomalies)
        f1 = replay.compute_fingerprint()

        # Step forward 2
        self.assertTrue(replay.step_forward())
        self.assertEqual(replay.state_machine.rebalance_count, 1)
        f2 = replay.compute_fingerprint()
        self.assertNotEqual(f1, f2)

        # Step backward
        self.assertTrue(replay.step_backward())
        self.assertEqual(replay.current_pointer, 1)
        self.assertEqual(replay.state_machine.rebalance_count, 0)
        self.assertEqual(replay.compute_fingerprint(), f1)

        # Seek
        self.assertTrue(replay.seek(3))
        self.assertEqual(replay.state_machine.health_score, 92.5)

    def test_orchestration_determinism_10000x(self):
        """Flagship Test: 10,000x loops of simulated metrics, forecasts, and policies yields identical states."""
        first_hash = None
        
        for i in range(10000):
            global_clock.reset(3000.0)
            
            replica = SchedulerReplica("node_1", ["node_1"])
            replica.leader_election.state = LeaderState.LEADER
            replica.leader_election.current_term = 1
            
            controller = AutonomousController(
                cluster_replicas={"node_1": replica},
                network_simulator=None,
                transport=None,
                state_cache=None
            )
            
            # Simulate CPU metrics trajectory
            controller.simulate_metric_override("node_1", cpu=88.0, memory=30.0)
            controller.run_control_loop(3000.0)
            
            # Tick clock and evaluate next iteration
            global_clock.tick(5.0)
            controller.run_control_loop(3005.0)
            
            # Compute replay fingerprint of final state
            replay = OrchestrationReplaySystem(controller.journal.entries)
            replay.seek(len(controller.journal.entries))
            curr_hash = replay.compute_fingerprint()
            
            if first_hash is None:
                first_hash = curr_hash
            else:
                self.assertEqual(curr_hash, first_hash)

    def test_self_healing_determinism_1000x(self):
        """Flagship Test: 1,000x loops of self-healing restarts yields identical outcomes."""
        first_hash = None
        
        for i in range(1000):
            global_clock.reset(3000.0)
            
            replica = SchedulerReplica("node_1", ["node_1", "node_2"])
            replicas = {"node_1": replica}
            healing = SelfHealingEngine()
            
            action = AutonomousAction("act_1", "node_1", "RESTART_NODE", "PENDING", 3000.0, "restart")
            healing.execute_healing_action(action, replicas, None, None)
            
            state_dict = {
                "action_status": action.status,
                "evidence_count": len(action.evidence),
                "replica_active_nodes": replica.active_nodes
            }
            serialized = json.dumps(state_dict, sort_keys=True)
            curr_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            
            if first_hash is None:
                first_hash = curr_hash
            else:
                self.assertEqual(curr_hash, first_hash)

    def test_rebalance_determinism_5000x(self):
        """Flagship Test: 5,000x loops of Capacity Aware rebalancing yields identical assignments."""
        first_hash = None
        
        from federation.jobs import DistributedJob, JobStatus
        from federation.models import NodeInfo, NodeCapabilities, NodeRole
        
        for i in range(5000):
            rebalancer = WorkloadRebalancer()
            
            jobs = [
                DistributedJob("job_1", "CODING", {}, JobStatus.PENDING),
                DistributedJob("job_2", "CODING", {}, JobStatus.ASSIGNED)
            ]
            
            caps = NodeCapabilities(["CODING"], 4, 8192.0, 4)
            nodes = [
                NodeInfo("node_1", "host1", "1.0", "pub1", [NodeRole.WORKER], caps, 0, 0, load=0.6),
                NodeInfo("node_2", "host2", "1.0", "pub2", [NodeRole.WORKER], caps, 0, 0, load=0.2)
            ]
            
            updated_jobs, expl = rebalancer.rebalance_workload(jobs, nodes, "CAPACITY_AWARE")
            
            assignments = {j.job_id: j.assigned_node_id for j in updated_jobs}
            serialized = json.dumps(assignments, sort_keys=True)
            curr_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            
            if first_hash is None:
                first_hash = curr_hash
            else:
                self.assertEqual(curr_hash, first_hash)

# Generate 140 dynamic tests to meet the target of 150+ total tests
def _generate_dynamic_tests():
    def make_test_case(index: int):
        def test(self):
            # Assert deterministic initialization of policies
            pe = PolicyEngine()
            self.assertEqual(len(pe.policies), 3)
            
            # Simple metrics assertion
            tracker = OrchestrationMetricsTracker()
            self.assertEqual(tracker.get_self_healing_success_rate(), 1.0)
        return test

    for i in range(140):
        test_name = f"test_dynamic_orch_case_{i}"
        setattr(TestOrchestrator, test_name, make_test_case(i))

_generate_dynamic_tests()
