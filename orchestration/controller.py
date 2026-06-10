import time
from typing import Dict, Any, List, Optional
from federation.health import ClusterHealth, ReplicaState
from federation.consensus.leader import LeaderState
from analytics.events import AnalyticsEventType, AnalyticsEvent
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
from orchestration.metrics import OrchestrationMetricsTracker

class AutonomousController:
    """Consolidated orchestrator coordinating all self-healing, anomaly, and capacity policy subsystems."""

    def __init__(
        self,
        cluster_replicas: Dict[str, Any],
        network_simulator: Optional[Any],
        transport: Optional[Any],
        state_cache: Optional[Any] = None,
        event_bridge: Optional[Any] = None
    ):
        self.cluster_replicas = cluster_replicas
        self.network_simulator = network_simulator
        self.transport = transport
        self.state_cache = state_cache
        self.event_bridge = event_bridge
        
        self.health_monitor = HealthMonitor()
        self.anomaly_detector = AnomalyDetector()
        self.capacity_forecaster = CapacityForecaster()
        self.policy_engine = PolicyEngine()
        self.decision_engine = DecisionEngine()
        self.rebalancer = WorkloadRebalancer()
        self.healing_engine = SelfHealingEngine()
        self.journal = OrchestrationJournal()
        self.metrics = OrchestrationMetricsTracker()
        
        self.election_timestamps: List[float] = []
        self.membership_change_timestamps: List[float] = []
        self.partition_toggle_counts: Dict[str, int] = {nid: 0 for nid in cluster_replicas.keys()}
        self.active_actions: List[AutonomousAction] = []
        self.active_anomalies: List[AnomalyRecord] = []
        self.simulated_pressures: Dict[str, Dict[str, float]] = {}  # node_id -> {cpu, memory}

    def simulate_metric_override(self, node_id: str, cpu: float, memory: float) -> None:
        """Simulate metrics overrides for testing anomaly detection and policies."""
        self.simulated_pressures[node_id] = {"cpu": cpu, "memory": memory}

    def _publish_event(self, event_type: AnalyticsEventType, source: str, payload: Dict[str, Any], now: float) -> None:
        if self.event_bridge and self.event_bridge.analytics_bus:
            evt = AnalyticsEvent(
                event_id=f"evt_{event_type.value.lower()}_{int(now*1000)}",
                timestamp_ns=int(now * 1e9),
                event_type=event_type,
                source=source,
                payload=payload
            )
            self.event_bridge.analytics_bus.publish(evt)

    def run_control_loop(self, now: float) -> OrchestrationDecision:
        """
        Execute one tick of the autonomous cluster orchestration loop.
        Processes metrics, health, anomalies, forecasts, policies, and decisions.
        """
        collected_metrics: Dict[str, NodeOrchestrationMetrics] = {}
        
        # 1. Collect Metrics
        for nid, replica in self.cluster_replicas.items():
            # Determine base CPU/Memory or overrides
            cpu = 10.0
            mem = 15.0
            if nid in self.simulated_pressures:
                cpu = self.simulated_pressures[nid]["cpu"]
                mem = self.simulated_pressures[nid]["memory"]
            elif hasattr(replica, "cpu_usage"):
                cpu = replica.cpu_usage
                mem = replica.memory_usage

            # Determine replica state
            is_active = True
            if nid not in replica.active_nodes:
                is_active = False
            
            # Check partition setting in network simulator if available
            if self.network_simulator:
                # If all links to node are blocked, consider partitioned
                is_partitioned = True
                for other_id in self.cluster_replicas.keys():
                    if other_id != nid:
                        link = self.network_simulator.links.get((other_id, nid))
                        if link and not link.blocked:
                            is_partitioned = False
                            break
                if is_partitioned:
                    is_active = False

            rep_state = ReplicaState.HEALTHY
            if not is_active:
                rep_state = ReplicaState.PARTITIONED
            elif replica.leader_election.state == LeaderState.FOLLOWER:
                # Check replication lag
                lag = 0
                for r in self.cluster_replicas.values():
                    if r.leader_election.state == LeaderState.LEADER:
                        lag = r.get_replication_lag().get(nid, 0)
                        break
                if lag > 100:
                    rep_state = ReplicaState.LAGGING
                elif lag > 10:
                    rep_state = ReplicaState.SYNCING

            if not hasattr(replica, "replica_states"):
                replica.replica_states = {}
            replica.replica_states[nid] = rep_state
            
            # Calculate replication lag
            lag = 0
            if replica.leader_election.state == LeaderState.LEADER:
                lag = max(replica.get_replication_lag().values()) if replica.get_replication_lag() else 0
            else:
                for r in self.cluster_replicas.values():
                    if r.leader_election.state == LeaderState.LEADER:
                        lag = r.get_replication_lag().get(nid, 0)
                        break

            metrics = NodeOrchestrationMetrics(
                node_id=nid,
                timestamp=now,
                cpu_usage=cpu,
                memory_usage=mem,
                load=getattr(replica, "load", 0.0),
                job_count=len(getattr(replica, "jobs", [])) if hasattr(replica, "jobs") else len(replica.consensus_log.entries),
                replication_lag=lag,
                term=replica.leader_election.current_term,
                network_latency=0.0
            )
            collected_metrics[nid] = metrics
            self.health_monitor.record_metrics(metrics)

        # 2. Update Cluster Health
        # Instantiate aggregate ClusterHealth
        leader_id = None
        election_cnt = 0
        commit_idx = 0
        active_nodes_list = []
        
        for r in self.cluster_replicas.values():
            if r.leader_election.state == LeaderState.LEADER:
                leader_id = r.node_id
                commit_idx = r.commit_index
                active_nodes_list = r.active_nodes
            election_cnt = max(election_cnt, r.leader_election.current_term) # using term as proxy

        cluster_health = ClusterHealth(
            active_nodes=active_nodes_list,
            quorum_size=(len(self.cluster_replicas) // 2) + 1,
            current_leader=leader_id,
            election_count=election_cnt,
            commit_index=commit_idx,
            replica_states={nid: r.replica_states.get(nid, ReplicaState.HEALTHY) for nid, r in self.cluster_replicas.items()}
        )
        
        # Apply health monitor scoring
        self.health_monitor.update_cluster_health(cluster_health, len(self.active_anomalies))

        # Propagate health updates to replicas
        for r in self.cluster_replicas.values():
            r.replica_states = dict(cluster_health.replica_states)

        # 3. Detect Anomalies
        prev_anomalies = {a.anomaly_id: a for a in self.active_anomalies}
        
        # Track election timestamps from leader terms
        for r in self.cluster_replicas.values():
            if r.leader_election.state == LeaderState.LEADER:
                term = r.leader_election.current_term
                # Simple approximation: if term incremented, record election timestamp
                if term > len(self.election_timestamps):
                    self.election_timestamps.append(now)

        new_anomalies = self.anomaly_detector.detect_anomalies(
            self.health_monitor.metrics_history,
            self.election_timestamps,
            self.membership_change_timestamps,
            self.partition_toggle_counts,
            now
        )
        self.active_anomalies = new_anomalies
        self.metrics.active_anomalies_count = len(new_anomalies)

        # Check for newly triggered anomalies
        for a in new_anomalies:
            if a.anomaly_id not in prev_anomalies:
                self.journal.append_record("ANOMALY_DETECTED", {
                    "anomaly_id": a.anomaly_id,
                    "node_id": a.node_id,
                    "type": a.type,
                    "severity": a.severity,
                    "details": a.details
                }, now)
                
                self._publish_event(
                    AnalyticsEventType.ANOMALY_DETECTED,
                    "Orchestrator",
                    {"anomaly_id": a.anomaly_id, "node_id": a.node_id, "type": a.type},
                    now
                )

                if a.type in ("CPU_SPIKE", "MEM_PRESSURE"):
                    self._publish_event(
                        AnalyticsEventType.RESOURCE_HOTSPOT_DETECTED,
                        "Orchestrator",
                        {"node_id": a.node_id, "resource": a.type},
                        now
                    )

        # Check for cleared anomalies
        curr_ids = {a.anomaly_id for a in new_anomalies}
        for aid, a in prev_anomalies.items():
            if aid not in curr_ids:
                self.journal.append_record("ANOMALY_CLEARED", {
                    "anomaly_id": aid,
                    "node_id": a.node_id,
                    "type": a.type
                }, now)
                
                self._publish_event(
                    AnalyticsEventType.ANOMALY_CLEARED,
                    "Orchestrator",
                    {"anomaly_id": aid, "node_id": a.node_id},
                    now
                )

        # 4. Forecast Capacity
        forecasts = []
        for nid in self.cluster_replicas.keys():
            history = self.health_monitor.metrics_history.get(nid, [])
            fc = self.capacity_forecaster.forecast_capacity(nid, history, now)
            forecasts.append(fc)
            if fc.predicted_failure_risk > 0.7:
                self._publish_event(
                    AnalyticsEventType.CAPACITY_FORECAST_GENERATED,
                    "Orchestrator",
                    {"node_id": nid, "risk": fc.predicted_failure_risk},
                    now
                )

        # 5. Evaluate Policies
        violations = []
        for nid, metrics in collected_metrics.items():
            v_list = self.policy_engine.evaluate_node(metrics)
            violations.extend(v_list)

        for v in violations:
            self.metrics.record_policy_violation()
            self.journal.append_record("POLICY_VIOLATION", v, now)
            self._publish_event(
                AnalyticsEventType.POLICY_VIOLATION,
                "Orchestrator",
                v,
                now
            )

        # 6. Make Decision
        decision = self.decision_engine.make_decision(
            self.active_anomalies,
            forecasts,
            violations,
            now
        )

        if decision.recommendations:
            self.journal.append_record("ORCHESTRATION_DECISION", {
                "decision_id": decision.decision_id,
                "analysis": decision.analysis,
                "confidence_score": decision.confidence_score,
                "evidence_chain": decision.evidence_chain
            }, now)
            
            self._publish_event(
                AnalyticsEventType.ORCHESTRATION_DECISION,
                "Orchestrator",
                {"decision_id": decision.decision_id, "recommendations_count": len(decision.recommendations)},
                now
            )

            # 7. Execute Actions
            for action in decision.recommendations:
                self.journal.append_record("AUTONOMOUS_ACTION_EXECUTED", {
                    "action_id": action.action_id,
                    "node_id": action.node_id,
                    "action_type": action.action_type,
                    "explanation": action.explanation
                }, now)

                # Rebalance
                if action.action_type == "REBALANCE":
                    # Load jobs from leader cache
                    leader = None
                    for r in self.cluster_replicas.values():
                        if r.leader_election.state == LeaderState.LEADER:
                            leader = r
                            break
                    
                    if leader and hasattr(leader, "scheduler"):
                        # Re-assign jobs
                        jobs = getattr(leader, "jobs", [])
                        nodes = getattr(leader, "registry", None)
                        node_list = nodes.list_nodes() if nodes else []
                        
                        # Run rebalancing
                        rebalanced_jobs, explanation = self.rebalancer.rebalance_workload(jobs, node_list, "CAPACITY_AWARE")
                        leader.jobs = rebalanced_jobs
                        action.status = "COMPLETED"
                        action.evidence.append(explanation)
                        self.metrics.record_rebalance()
                        
                        self._publish_event(
                            AnalyticsEventType.WORKLOAD_REBALANCED,
                            "Orchestrator",
                            {"explanation": explanation},
                            now
                        )
                    else:
                        action.status = "FAILED"
                        action.evidence.append("Rebalance skipped: Leader scheduler not found.")
                
                # Self-healing Actions
                else:
                    self._publish_event(
                        AnalyticsEventType.SELF_HEAL_TRIGGERED,
                        "Orchestrator",
                        {"action_id": action.action_id, "action_type": action.action_type, "node_id": action.node_id},
                        now
                    )
                    
                    success = self.healing_engine.execute_healing_action(
                        action,
                        self.cluster_replicas,
                        self.network_simulator,
                        self.transport
                    )
                    
                    if success:
                        self.metrics.record_healing_success()
                        self._publish_event(
                            AnalyticsEventType.SELF_HEAL_COMPLETED,
                            "Orchestrator",
                            {"action_id": action.action_id, "status": "COMPLETED"},
                            now
                        )
                    else:
                        self.metrics.record_healing_failure()
                        self._publish_event(
                            AnalyticsEventType.SELF_HEAL_COMPLETED,
                            "Orchestrator",
                            {"action_id": action.action_id, "status": "FAILED"},
                            now
                        )

                self.active_actions.append(action)

        # 8. Journal health summary state
        self.journal.append_record("HEALTH_UPDATE", {
            "health_score": cluster_health.health_score,
            "cpu_pressure_score": cluster_health.cpu_pressure_score,
            "memory_pressure_score": cluster_health.memory_pressure_score,
            "node_health_states": cluster_health.node_health_states
        }, now)

        # 9. Update Dashboard Cache
        if self.state_cache:
            self.state_cache.set_federation_health({
                "status": "HEALTHY" if cluster_health.health_score >= 80.0 else "DEGRADED" if cluster_health.health_score >= 50.0 else "CRITICAL",
                "health_score": cluster_health.health_score,
                "cpu_pressure_score": cluster_health.cpu_pressure_score,
                "memory_pressure_score": cluster_health.memory_pressure_score,
                "node_count": len(self.cluster_replicas),
                "replica_states": {nid: s.value for nid, s in cluster_health.replica_states.items()},
                "anomaly_count": len(self.active_anomalies)
            })
            
            self.state_cache.set_orchestration_status({
                "status": "ACTIVE",
                "controller_active": True,
                "last_run_timestamp": now,
                "metrics": self.metrics.to_dict()
            })
            
            self.state_cache.set_orchestration_health({
                "health_score": cluster_health.health_score,
                "cpu_pressure_score": cluster_health.cpu_pressure_score,
                "memory_pressure_score": cluster_health.memory_pressure_score,
                "anomaly_count": len(self.active_anomalies),
                "node_health_states": cluster_health.node_health_states
            })
            
            self.state_cache.set_orchestration_anomalies([
                {
                    "anomaly_id": a.anomaly_id,
                    "node_id": a.node_id,
                    "type": a.type,
                    "severity": a.severity,
                    "timestamp": a.timestamp,
                    "details": a.details
                } for a in self.active_anomalies
            ])
            
            self.state_cache.set_orchestration_actions([
                {
                    "action_id": a.action_id,
                    "node_id": a.node_id,
                    "action_type": a.action_type,
                    "status": a.status,
                    "timestamp": a.timestamp,
                    "explanation": a.explanation,
                    "evidence": a.evidence
                } for a in self.active_actions
            ])
            
            self.state_cache.set_orchestration_policies([
                {
                    "policy_id": p.policy_id,
                    "name": p.name,
                    "rule_expr": p.rule_expr,
                    "action_type": p.action_type,
                    "enabled": p.enabled
                } for p in self.policy_engine.policies
            ])
            
            self.state_cache.set_orchestration_forecast({
                "forecasts": [
                    {
                        "node_id": f.node_id,
                        "predicted_cpu": f.predicted_cpu,
                        "predicted_memory": f.predicted_memory,
                        "predicted_failure_risk": f.predicted_failure_risk,
                        "bottleneck_time": f.bottleneck_time
                    } for f in forecasts
                ],
                "bottlenecks_detected": any(f.predicted_failure_risk > 0.7 for f in forecasts)
            })

        return decision
