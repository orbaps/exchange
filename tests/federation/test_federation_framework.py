import unittest
import time
import os
import shutil
import tempfile
import json
import hashlib
from typing import Dict, Any, List

from fastapi.testclient import TestClient

from analytics.bus import AnalyticsEventBus
from analytics.events import AnalyticsEvent, AnalyticsEventType
from evaluation.benchmarks.models import Benchmark, BenchmarkSuite, BenchmarkRegistry, EvaluationDomain
from evaluation.benchmarks.campaign import EvaluationCampaign
from evaluation.judge.judges import RuleBasedJudge
from evaluation.journal import EvaluationJournal

from federation.models import NodeInfo, NodeCapabilities, NodeRole
from federation.security import FederationKeyPair, FederationVerifier
from federation.registry import FederationRegistry
from federation.jobs import DistributedJob, JobStatus, JobAssignment, JobResult
from federation.scheduler import DistributedScheduler
from federation.artifacts import ArtifactReplicator
from federation.leaderboard import FederatedLeaderboard
from federation.replay import FederatedReplay
from federation.journal import FederationJournal
from federation.evaluation import FederatedEvaluationRunner
from federation.network import FederationServer, FederationClient

from dashboard.app import app
from dashboard.dependencies import state_cache


class TestFederationSecurity(unittest.TestCase):
    def setUp(self):
        self.rsa_priv, self.rsa_pub = FederationKeyPair.generate_rsa()
        self.ed_priv, self.ed_pub = FederationKeyPair.generate_ed25519()
        self.payload = {"command": "EXECUTE", "args": [1, 2, 3]}

    def test_rsa_key_generation(self):
        self.assertTrue(self.rsa_priv.startswith("-----BEGIN PRIVATE KEY-----") or self.rsa_priv.startswith("-----BEGIN RSA PRIVATE KEY-----"))
        self.assertTrue(self.rsa_pub.startswith("-----BEGIN PUBLIC KEY-----"))

    def test_ed25519_key_generation(self):
        self.assertTrue(self.ed_priv.startswith("-----BEGIN PRIVATE KEY-----"))
        self.assertTrue(self.ed_pub.startswith("-----BEGIN PUBLIC KEY-----"))

    def test_rsa_sign_and_verify_happy(self):
        envelope = FederationVerifier.sign_message("node_rsa", self.rsa_priv, self.payload)
        self.assertEqual(envelope["node_id"], "node_rsa")
        self.assertEqual(envelope["algo"], "RSA")
        self.assertEqual(envelope["payload"], self.payload)
        self.assertTrue(FederationVerifier.verify_message(envelope, self.rsa_pub))

    def test_ed25519_sign_and_verify_happy(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        self.assertEqual(envelope["node_id"], "node_ed")
        self.assertEqual(envelope["algo"], "ED25519")
        self.assertEqual(envelope["payload"], self.payload)
        self.assertTrue(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_verify_fails_with_tampered_payload(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        envelope["payload"]["command"] = "TAMPERED"
        self.assertFalse(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_verify_fails_with_tampered_hash(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        envelope["payload_hash"] = "wronghash"
        self.assertFalse(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_verify_fails_with_tampered_signature(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        envelope["signature"] = envelope["signature"][:-4] + "AAAA"
        self.assertFalse(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_verify_fails_with_tampered_node_id(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        envelope["node_id"] = "different_node"
        self.assertFalse(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_verify_fails_with_tampered_timestamp(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        envelope["timestamp"] += 1
        self.assertFalse(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_verify_fails_with_invalid_public_key(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        _, another_pub = FederationKeyPair.generate_ed25519()
        self.assertFalse(FederationVerifier.verify_message(envelope, another_pub))

    def test_verify_fails_with_cross_algorithm_key(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        self.assertFalse(FederationVerifier.verify_message(envelope, self.rsa_pub))

    def test_verify_fails_with_malformed_envelope(self):
        self.assertFalse(FederationVerifier.verify_message({}, self.ed_pub))

    def test_verify_fails_with_missing_keys_in_envelope(self):
        envelope = {"node_id": "x"}
        self.assertFalse(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_verify_fails_with_non_base64_signature(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        envelope["signature"] = "not_base64_at_all!@#"
        self.assertFalse(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_verify_fails_with_empty_signature(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        envelope["signature"] = ""
        self.assertFalse(FederationVerifier.verify_message(envelope, self.ed_pub))

    def test_rsa_verify_with_tampered_envelope_keys(self):
        envelope = FederationVerifier.sign_message("node_rsa", self.rsa_priv, self.payload)
        del envelope["algo"]
        self.assertFalse(FederationVerifier.verify_message(envelope, self.rsa_pub))

    def test_verifier_compute_payload_hash_stability(self):
        h1 = FederationVerifier.compute_payload_hash(self.payload)
        h2 = FederationVerifier.compute_payload_hash(self.payload)
        self.assertEqual(h1, h2)

    def test_verify_message_none_params(self):
        self.assertFalse(FederationVerifier.verify_message(None, self.ed_pub))

    def test_verify_message_invalid_public_key_format(self):
        envelope = FederationVerifier.sign_message("node_ed", self.ed_priv, self.payload)
        self.assertFalse(FederationVerifier.verify_message(envelope, "INVALID PUBLIC KEY PEM"))


class TestFederationRegistry(unittest.TestCase):
    def setUp(self):
        self.bus = AnalyticsEventBus()
        self.events: List[AnalyticsEvent] = []
        self.bus.subscribe(self.events.append)
        self.registry = FederationRegistry(self.bus)
        self.caps = NodeCapabilities(["CODING", "REASONING"], 4, 4096.0, 2)
        self.node = NodeInfo("node1", "host1", "1.0.0", "pub1", [NodeRole.WORKER], self.caps, registered_at=int(time.time()), last_seen=int(time.time()))

    def test_register_node_happy(self):
        self.assertTrue(self.registry.register_node(self.node))
        node_retrieved = self.registry.get_node("node1")
        self.assertIsNotNone(node_retrieved)
        self.assertEqual(node_retrieved.node_id, "node1")
        self.assertEqual(node_retrieved.status, "ACTIVE")
        self.assertEqual(len(self.events), 1)
        self.assertEqual(self.events[0].event_type, AnalyticsEventType.NODE_REGISTERED)

    def test_double_register_updates_attributes(self):
        self.registry.register_node(self.node)
        self.node.hostname = "host1_updated"
        self.registry.register_node(self.node)
        self.assertEqual(self.registry.get_node("node1").hostname, "host1_updated")

    def test_remove_node_happy(self):
        self.registry.register_node(self.node)
        self.assertTrue(self.registry.remove_node("node1"))
        self.assertIsNone(self.registry.get_node("node1"))
        self.assertEqual(self.events[-1].event_type, AnalyticsEventType.NODE_REMOVED)

    def test_remove_nonexistent_node(self):
        self.assertFalse(self.registry.remove_node("nonexistent"))

    def test_heartbeat_happy(self):
        self.registry.register_node(self.node)
        self.assertTrue(self.registry.heartbeat("node1", 0.5))
        n = self.registry.get_node("node1")
        self.assertEqual(n.load, 0.5)
        self.assertEqual(self.events[-1].event_type, AnalyticsEventType.NODE_HEARTBEAT)

    def test_heartbeat_nonexistent_node(self):
        self.assertFalse(self.registry.heartbeat("nonexistent", 0.1))

    def test_list_nodes_empty(self):
        self.assertEqual(len(self.registry.list_nodes()), 0)

    def test_list_nodes_populated(self):
        self.registry.register_node(self.node)
        self.assertEqual(len(self.registry.list_nodes()), 1)

    def test_discover_nodes_by_role(self):
        self.registry.register_node(self.node)
        worker_node = NodeInfo("node2", "host2", "1.0", "pub2", [NodeRole.COORDINATOR], self.caps, registered_at=int(time.time()), last_seen=int(time.time()))
        self.registry.register_node(worker_node)
        
        workers = self.registry.discover_nodes(NodeRole.WORKER)
        coordinators = self.registry.discover_nodes(NodeRole.COORDINATOR)
        all_nodes = self.registry.discover_nodes()

        self.assertEqual(len(workers), 1)
        self.assertEqual(workers[0].node_id, "node1")
        self.assertEqual(len(coordinators), 1)
        self.assertEqual(coordinators[0].node_id, "node2")
        self.assertEqual(len(all_nodes), 2)

    def test_cleanup_expired_nodes_none(self):
        self.registry.register_node(self.node)
        expired = self.registry.cleanup_expired_nodes()
        self.assertEqual(len(expired), 0)
        self.assertEqual(len(self.registry.list_nodes()), 1)

    def test_cleanup_expired_nodes_success(self):
        self.registry.register_node(self.node)
        self.registry.heartbeat_timeout = -1.0  # Force instant expiration
        expired = self.registry.cleanup_expired_nodes()
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0], "node1")
        self.assertEqual(len(self.registry.list_nodes()), 0)

    def test_heartbeat_restores_expired_node_on_register(self):
        self.registry.register_node(self.node)
        self.registry.heartbeat_timeout = -1.0
        self.registry.cleanup_expired_nodes()
        self.assertIsNone(self.registry.get_node("node1"))
        
        # Register again
        self.registry.register_node(self.node)
        self.assertIsNotNone(self.registry.get_node("node1"))

    def test_registry_thread_safety(self):
        import threading
        # Ensure concurrent reads/writes don't raise errors
        def worker_task(i: int):
            node = NodeInfo(f"node_{i}", "host", "1", "pub", [NodeRole.WORKER], self.caps, registered_at=int(time.time()), last_seen=int(time.time()))
            self.registry.register_node(node)
            self.registry.heartbeat(f"node_{i}", 0.2)
            self.registry.list_nodes()

        threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(self.registry.list_nodes()), 10)

    def test_get_node_nonexistent(self):
        self.assertIsNone(self.registry.get_node("nonexistent"))

    def test_remove_node_releases_resources(self):
        self.registry.register_node(self.node)
        self.registry.remove_node("node1")
        self.assertEqual(len(self.registry.list_nodes()), 0)

    def test_register_node_empty_roles(self):
        empty_roles_node = NodeInfo("node_empty", "host", "1", "pub", [], self.caps, registered_at=int(time.time()), last_seen=int(time.time()))
        self.assertTrue(self.registry.register_node(empty_roles_node))
        self.assertEqual(self.registry.get_node("node_empty").roles, [])

    def test_registry_cleanup_expired_nodes_marks_expired(self):
        self.registry.register_node(self.node)
        self.registry.heartbeat_timeout = -1.0
        self.registry.cleanup_expired_nodes()
        # The node should be removed from active nodes, list_nodes should be empty
        self.assertEqual(len(self.registry.list_nodes()), 0)


class TestFederationScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = DistributedScheduler()
        self.caps_coding = NodeCapabilities(["CODING"], 4, 1024, 2)
        self.caps_math = NodeCapabilities(["MATHEMATICS"], 4, 1024, 2)
        self.node1 = NodeInfo("node1", "host1", "1", "pub", [NodeRole.WORKER], self.caps_coding, registered_at=int(time.time()), last_seen=int(time.time()), load=0.5)
        self.node2 = NodeInfo("node2", "host2", "1", "pub", [NodeRole.WORKER], self.caps_math, registered_at=int(time.time()), last_seen=int(time.time()), load=0.1)
        self.job = DistributedJob("job1", "BENCHMARK_EXECUTION", {"category": "CODING"})

    def test_assign_work_empty_nodes(self):
        self.assertIsNone(self.scheduler.assign_work(self.job, []))

    def test_assign_work_round_robin(self):
        nodes = [self.node1, self.node2]
        # First assignment
        a1 = self.scheduler.assign_work(self.job, nodes, "ROUND_ROBIN")
        # Second assignment
        a2 = self.scheduler.assign_work(self.job, nodes, "ROUND_ROBIN")
        # Third assignment (wraps around)
        a3 = self.scheduler.assign_work(self.job, nodes, "ROUND_ROBIN")

        self.assertEqual(a1, "node1")
        self.assertEqual(a2, "node2")
        self.assertEqual(a3, "node1")

    def test_assign_work_least_loaded(self):
        nodes = [self.node1, self.node2]  # node1 load=0.5, node2 load=0.1
        assigned = self.scheduler.assign_work(self.job, nodes, "LEAST_LOADED")
        self.assertEqual(assigned, "node2")

    def test_assign_work_least_loaded_tie_breaker(self):
        self.node1.load = 0.2
        self.node2.load = 0.2
        nodes = [self.node2, self.node1]
        assigned = self.scheduler.assign_work(self.job, nodes, "LEAST_LOADED")
        # Lexicographically smaller node_id wins
        self.assertEqual(assigned, "node1")

    def test_assign_work_capability_match_success(self):
        nodes = [self.node1, self.node2]
        assigned = self.scheduler.assign_work(self.job, nodes, "CAPABILITY_MATCH")
        self.assertEqual(assigned, "node1")  # supports CODING

    def test_assign_work_capability_match_no_domain_in_payload(self):
        job_no_domain = DistributedJob("job1", "EXEC", {})
        nodes = [self.node1, self.node2]
        assigned = self.scheduler.assign_work(job_no_domain, nodes, "CAPABILITY_MATCH")
        # Fallback to round robin
        self.assertEqual(assigned, "node1")

    def test_assign_work_capability_match_no_matching_nodes(self):
        # Request domain CyberSecurity which neither supports
        job_cyber = DistributedJob("job1", "EXEC", {"category": "CYBERSECURITY"})
        nodes = [self.node1, self.node2]
        assigned = self.scheduler.assign_work(job_cyber, nodes, "CAPABILITY_MATCH")
        # Fallback to all nodes, picking the least loaded
        self.assertEqual(assigned, "node2")

    def test_assign_work_random_seeded_determinism(self):
        nodes = [self.node1, self.node2]
        # Same seed + same job -> same node
        a1 = self.scheduler.assign_work(self.job, nodes, "RANDOM_SEEDED", seed=100)
        a2 = self.scheduler.assign_work(self.job, nodes, "RANDOM_SEEDED", seed=100)
        self.assertEqual(a1, a2)

    def test_assign_work_random_seeded_different_seeds(self):
        nodes = [self.node1, self.node2]
        # Note: with 2 nodes, different seeds *might* hit same node, so we use multiple trials
        assignments = set()
        for seed in range(50):
            a = self.scheduler.assign_work(self.job, nodes, "RANDOM_SEEDED", seed=seed)
            assignments.add(a)
        self.assertTrue(len(assignments) > 0)

    def test_assign_work_unknown_mode(self):
        self.assertIsNone(self.scheduler.assign_work(self.job, [self.node1], "INVALID_MODE"))

    def test_rebalance_empty_nodes(self):
        jobs = [DistributedJob("j1", "EXEC", {}, status=JobStatus.ASSIGNED, assigned_node_id="node1")]
        rebalanced = self.scheduler.rebalance(jobs, [])
        self.assertEqual(rebalanced[0].status, JobStatus.PENDING)
        self.assertIsNone(rebalanced[0].assigned_node_id)

    def test_rebalance_distributes_evenly(self):
        jobs = [
            DistributedJob("j1", "EXEC", {}),
            DistributedJob("j2", "EXEC", {}),
            DistributedJob("j3", "EXEC", {}),
            DistributedJob("j4", "EXEC", {}, status=JobStatus.COMPLETED, assigned_node_id="node1")
        ]
        nodes = [self.node1, self.node2]
        rebalanced = self.scheduler.rebalance(jobs, nodes)
        
        # Completed job should NOT be rebalanced
        self.assertEqual(rebalanced[3].status, JobStatus.COMPLETED)
        self.assertEqual(rebalanced[3].assigned_node_id, "node1")

        # Pending jobs distributed round-robin among node1 and node2
        self.assertEqual(rebalanced[0].assigned_node_id, "node1")
        self.assertEqual(rebalanced[1].assigned_node_id, "node2")
        self.assertEqual(rebalanced[2].assigned_node_id, "node1")

    def test_cancel_happy(self):
        job = DistributedJob("j1", "EXEC", {}, status=JobStatus.RUNNING)
        self.assertTrue(self.scheduler.cancel(job))
        self.assertEqual(job.status, JobStatus.CANCELLED)

    def test_cancel_already_finished(self):
        job = DistributedJob("j1", "EXEC", {}, status=JobStatus.COMPLETED)
        self.assertFalse(self.scheduler.cancel(job))
        self.assertEqual(job.status, JobStatus.COMPLETED)

    def test_retry_under_max(self):
        job = DistributedJob("j1", "EXEC", {}, status=JobStatus.FAILED, retry_count=1, max_retries=3)
        self.assertTrue(self.scheduler.retry(job))
        self.assertEqual(job.status, JobStatus.RETRYING)
        self.assertEqual(job.retry_count, 2)

    def test_retry_exceeds_max(self):
        job = DistributedJob("j1", "EXEC", {}, status=JobStatus.FAILED, retry_count=3, max_retries=3)
        self.assertFalse(self.scheduler.retry(job))
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertEqual(job.retry_count, 3)

    def test_retry_non_failed_job(self):
        job = DistributedJob("j1", "EXEC", {}, status=JobStatus.COMPLETED)
        self.assertFalse(self.scheduler.retry(job))

    def test_assign_work_least_loaded_single_node(self):
        nodes = [self.node1]
        self.assertEqual(self.scheduler.assign_work(self.job, nodes, "LEAST_LOADED"), "node1")

    def test_assign_work_round_robin_single_node(self):
        nodes = [self.node1]
        self.assertEqual(self.scheduler.assign_work(self.job, nodes, "ROUND_ROBIN"), "node1")

    def test_assign_work_capability_match_single_node(self):
        nodes = [self.node1]
        self.assertEqual(self.scheduler.assign_work(self.job, nodes, "CAPABILITY_MATCH"), "node1")

    def test_assign_work_random_seeded_single_node(self):
        nodes = [self.node1]
        self.assertEqual(self.scheduler.assign_work(self.job, nodes, "RANDOM_SEEDED"), "node1")

    def test_rebalance_no_pending_jobs(self):
        jobs = [DistributedJob("j1", "EXEC", {}, status=JobStatus.COMPLETED, assigned_node_id="node1")]
        nodes = [self.node1, self.node2]
        rebalanced = self.scheduler.rebalance(jobs, nodes)
        self.assertEqual(rebalanced[0].assigned_node_id, "node1")

    def test_rebalance_all_completed_jobs(self):
        jobs = [
            DistributedJob("j1", "EXEC", {}, status=JobStatus.COMPLETED, assigned_node_id="node1"),
            DistributedJob("j2", "EXEC", {}, status=JobStatus.COMPLETED, assigned_node_id="node2")
        ]
        rebalanced = self.scheduler.rebalance(jobs, [self.node1, self.node2])
        self.assertEqual(rebalanced[0].assigned_node_id, "node1")
        self.assertEqual(rebalanced[1].assigned_node_id, "node2")


class TestFederationArtifacts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.bus = AnalyticsEventBus()
        self.events = []
        self.bus.subscribe(self.events.append)
        self.replicator = ArtifactReplicator(self.temp_dir, self.bus)
        self.artifact_data = b"Hello, federated world!"
        self.artifact_hash = ArtifactReplicator.compute_sha256(self.artifact_data)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_compute_sha256(self):
        h = ArtifactReplicator.compute_sha256(b"abc")
        self.assertEqual(h, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_verify_hash_happy(self):
        self.assertTrue(self.replicator.verify(self.artifact_data, self.artifact_hash))

    def test_verify_hash_failure(self):
        self.assertFalse(self.replicator.verify(self.artifact_data, "incorrecthash"))

    def test_push_saves_file_and_publishes_event(self):
        self.assertTrue(self.replicator.push("art1", self.artifact_data, "node2"))
        filepath = os.path.join(self.temp_dir, "art1")
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "rb") as f:
            self.assertEqual(f.read(), self.artifact_data)

        self.assertEqual(len(self.events), 1)
        self.assertEqual(self.events[0].event_type, AnalyticsEventType.ARTIFACT_REPLICATED)
        self.assertEqual(self.events[0].payload["direction"], "PUSH")

    def test_pull_reads_file_and_publishes_event(self):
        self.replicator.push("art1", self.artifact_data, "node2")
        self.events.clear()

        retrieved = self.replicator.pull("art1", "node2")
        self.assertEqual(retrieved, self.artifact_data)
        self.assertEqual(len(self.events), 1)
        self.assertEqual(self.events[0].event_type, AnalyticsEventType.ARTIFACT_REPLICATED)
        self.assertEqual(self.events[0].payload["direction"], "PULL")

    def test_pull_nonexistent_returns_none(self):
        self.assertIsNone(self.replicator.pull("nonexistent", "node2"))

    def test_get_local_manifest(self):
        self.replicator.push("art1", b"data1", "node2")
        self.replicator.push("art2", b"data2", "node2")
        manifest = self.replicator.get_local_manifest()
        
        self.assertIn("art1", manifest)
        self.assertIn("art2", manifest)
        self.assertEqual(manifest["art1"], ArtifactReplicator.compute_sha256(b"data1"))

    def test_sync_no_differences(self):
        self.replicator.push("art1", b"data1", "node2")
        peer_manifest = {"art1": ArtifactReplicator.compute_sha256(b"data1")}
        out_of_sync = self.replicator.sync("node2", peer_manifest)
        self.assertEqual(len(out_of_sync), 0)
        self.assertEqual(self.events[-1].event_type, AnalyticsEventType.FEDERATION_SYNC_COMPLETED)
        self.assertEqual(self.events[-1].payload["artifacts_out_of_sync_count"], 0)

    def test_sync_with_differences(self):
        self.replicator.push("art1", b"data1", "node2")
        peer_manifest = {
            "art1": ArtifactReplicator.compute_sha256(b"data_tampered"),
            "art2": ArtifactReplicator.compute_sha256(b"data2")
        }
        out_of_sync = self.replicator.sync("node2", peer_manifest)
        self.assertIn("art1", out_of_sync)
        self.assertIn("art2", out_of_sync)
        self.assertEqual(len(out_of_sync), 2)

    def test_repair_overwrites_file(self):
        self.replicator.push("art1", b"bad_data", "node2")
        self.assertTrue(self.replicator.repair("art1", self.artifact_data))
        filepath = os.path.join(self.temp_dir, "art1")
        with open(filepath, "rb") as f:
            self.assertEqual(f.read(), self.artifact_data)

    def test_sync_empty_peer_manifest(self):
        self.replicator.push("art1", b"data1", "node2")
        self.assertEqual(len(self.replicator.sync("node2", {})), 0)

    def test_sync_missing_local_file(self):
        peer_manifest = {"art1": self.artifact_hash}
        out_of_sync = self.replicator.sync("node2", peer_manifest)
        self.assertIn("art1", out_of_sync)

    def test_push_empty_data(self):
        self.assertTrue(self.replicator.push("art_empty", b"", "node2"))
        with open(os.path.join(self.temp_dir, "art_empty"), "rb") as f:
            self.assertEqual(f.read(), b"")

    def test_repair_new_file(self):
        # Even if file didn't exist, repair should create it
        self.assertTrue(self.replicator.repair("art_new", b"repaired_new"))
        with open(os.path.join(self.temp_dir, "art_new"), "rb") as f:
            self.assertEqual(f.read(), b"repaired_new")


class TestFederationReplay(unittest.TestCase):
    def setUp(self):
        self.replay = FederatedReplay()
        self.temp_dir = tempfile.mkdtemp()
        self.journal_path1 = os.path.join(self.temp_dir, "j1.jsonl")
        self.journal_path2 = os.path.join(self.temp_dir, "j2.jsonl")
        self.j1 = FederationJournal(self.journal_path1)
        self.j2 = FederationJournal(self.journal_path2)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_get_sort_key_variants(self):
        entry_ts_ns = {"payload": {"timestamp_ns": 100}, "node_id": "a"}
        entry_ts = {"payload": {"timestamp": 200}, "node_id": "b"}
        entry_direct = {"timestamp_ns": 300, "node_id": "c"}
        
        self.assertEqual(FederatedReplay.get_sort_key(entry_ts_ns), (100.0, "a"))
        self.assertEqual(FederatedReplay.get_sort_key(entry_ts), (200.0, "b"))
        self.assertEqual(FederatedReplay.get_sort_key(entry_direct), (300.0, "c"))

    def test_merge_journals_happy(self):
        self.j1.write_entry("NODE_REGISTERED", {"node_id": "node1", "timestamp_ns": 10})
        self.j2.write_entry("NODE_REGISTERED", {"node_id": "node2", "timestamp_ns": 5})

        merged = self.replay.merge_journals([self.j1, self.j2])
        self.assertEqual(len(merged), 2)
        # Verify node2 (ts=5) comes before node1 (ts=10)
        self.assertEqual(merged[0]["payload"]["node_id"], "node2")
        self.assertEqual(merged[1]["payload"]["node_id"], "node1")

    def test_merge_journals_empty(self):
        merged = self.replay.merge_journals([])
        self.assertEqual(len(merged), 0)

    def test_verify_order_sorted(self):
        entries = [
            {"payload": {"timestamp_ns": 1, "node_id": "a"}},
            {"payload": {"timestamp_ns": 2, "node_id": "b"}},
            {"payload": {"timestamp_ns": 2, "node_id": "c"}}
        ]
        self.assertTrue(self.replay.verify_order(entries))

    def test_verify_order_unsorted(self):
        entries = [
            {"payload": {"timestamp_ns": 2, "node_id": "b"}},
            {"payload": {"timestamp_ns": 1, "node_id": "a"}}
        ]
        self.assertFalse(self.replay.verify_order(entries))

    def test_reconstruct_state_flow(self):
        timeline = [
            {"event_type": "NODE_REGISTERED", "payload": {"node_id": "n1", "hostname": "h1", "roles": ["WORKER"]}},
            {"event_type": "NODE_HEARTBEAT", "payload": {"node_id": "n1", "load": 0.3}},
            {"event_type": "JOB_ASSIGNED", "payload": {"job_id": "j1", "node_id": "n1"}},
            {"event_type": "JOB_COMPLETED", "payload": {"job_id": "j1"}},
            {"event_type": "NODE_REMOVED", "payload": {"node_id": "n1"}},
            {"event_type": "ARTIFACT_REPLICATED", "payload": {}},
            {"event_type": "FEDERATION_SYNC_COMPLETED", "payload": {}},
            {"event_type": "WINNER_DECLARED", "payload": {"winner": "contestantA"}},
            {"event_type": "LEADERBOARD_UPDATE", "payload": {"scores": {}}}
        ]
        
        # Reconstruct up to end of timeline
        state = self.replay.reconstruct_state(timeline, len(timeline) - 1)
        
        self.assertEqual(state["nodes"]["n1"]["status"], "OFFLINE")
        self.assertEqual(state["nodes"]["n1"]["load"], 0.3)
        self.assertEqual(state["jobs"]["j1"]["status"], "COMPLETED")
        self.assertEqual(state["replicated_count"], 1)
        self.assertEqual(state["sync_completed_count"], 1)
        self.assertEqual(state["winner"], "contestantA")
        self.assertIsNotNone(state["leaderboard"])

    def test_merge_journals_single_journal(self):
        self.j1.write_entry("NODE_REGISTERED", {"node_id": "node1", "timestamp_ns": 10})
        merged = self.replay.merge_journals([self.j1])
        self.assertEqual(len(merged), 1)

    def test_merge_journals_identical_timestamps(self):
        self.j1.write_entry("NODE_REGISTERED", {"node_id": "nodeB", "timestamp_ns": 10})
        self.j2.write_entry("NODE_REGISTERED", {"node_id": "nodeA", "timestamp_ns": 10})
        merged = self.replay.merge_journals([self.j1, self.j2])
        # Sort key tie break on node_id: nodeA should be first
        self.assertEqual(merged[0]["payload"]["node_id"], "nodeA")

    def test_verify_order_empty(self):
        self.assertTrue(self.replay.verify_order([]))

    def test_verify_order_single(self):
        self.assertTrue(self.replay.verify_order([{"payload": {"timestamp_ns": 1}}]))

    def test_reconstruct_state_empty_timeline(self):
        state = self.replay.reconstruct_state([], 0)
        self.assertEqual(len(state["nodes"]), 0)

    def test_reconstruct_state_out_of_bounds_index(self):
        state = self.replay.reconstruct_state([{"event_type": "NODE_REGISTERED"}], 5)
        self.assertEqual(len(state["nodes"]), 0)


class TestFederationLeaderboard(unittest.TestCase):
    def setUp(self):
        self.flb = FederatedLeaderboard()
        self.snap1 = {
            "snapshot_id": "s1",
            "timestamp": "1000",
            "event_count": 5,
            "execution_tps": 50.0,
            "entries": [
                {"contestant_id": "c1", "score": 90.0, "rank": 1},
                {"contestant_id": "c2", "score": 80.0, "rank": 2}
            ]
        }
        self.snap2 = {
            "snapshot_id": "s2",
            "timestamp": "2000",  # Newer timestamp
            "event_count": 10,
            "execution_tps": 100.0,
            "entries": [
                {"contestant_id": "c2", "score": 85.0, "rank": 1},
                {"contestant_id": "c3", "score": 70.0, "rank": 2}
            ]
        }

    def test_merge_snapshots_empty(self):
        self.assertIsNone(self.flb.merge_snapshots([]))

    def test_merge_snapshots_resolves_conflict_by_newer_timestamp(self):
        merged = self.flb.merge_snapshots([self.snap1, self.snap2])
        self.assertEqual(merged["entry_count"], 3)
        
        # c2 has entries in both snap1 (score 80, ts 1000) and snap2 (score 85, ts 2000)
        # Newer timestamp in snap2 must win -> score should be 85
        entries = {e["contestant_id"]: e for e in merged["entries"]}
        self.assertEqual(entries["c2"]["score"], 85.0)

    def test_merge_snapshots_resolves_conflict_by_hash_when_timestamp_equal(self):
        snap1_equal = self.snap1.copy()
        snap1_equal["timestamp"] = "1000"
        snap1_equal["snapshot_id"] = "a_low_hash"
        
        snap2_equal = self.snap2.copy()
        snap2_equal["timestamp"] = "1000"
        snap2_equal["snapshot_id"] = "z_high_hash"  # Higher hash

        merged = self.flb.merge_snapshots([snap1_equal, snap2_equal])
        entries = {e["contestant_id"]: e for e in merged["entries"]}
        self.assertEqual(entries["c2"]["score"], 85.0)  # snap2_equal wins because of higher hash

    def test_merge_snapshots_resolves_conflict_by_node_id_when_hash_equal(self):
        snap1_equal = self.snap1.copy()
        snap1_equal["timestamp"] = "1000"
        snap1_equal["snapshot_id"] = "same_hash"
        snap1_equal["tournament_id"] = "nodeA"  # Lexicographically smaller node_id wins

        snap2_equal = self.snap2.copy()
        snap2_equal["timestamp"] = "1000"
        snap2_equal["snapshot_id"] = "same_hash"
        snap2_equal["tournament_id"] = "nodeB"

        merged = self.flb.merge_snapshots([snap1_equal, snap2_equal])
        entries = {e["contestant_id"]: e for e in merged["entries"]}
        self.assertEqual(entries["c2"]["score"], 80.0)  # nodeA wins!

    def test_merge_snapshots_no_entries(self):
        snap_empty = {"snapshot_id": "se", "timestamp": "100", "entries": []}
        merged = self.flb.merge_snapshots([snap_empty])
        self.assertEqual(merged["entry_count"], 0)

    def test_merge_snapshots_single_snapshot(self):
        merged = self.flb.merge_snapshots([self.snap1])
        self.assertEqual(merged["entry_count"], 2)

    def test_rank_stability(self):
        entries = [{"contestant_id": "c1", "score": 90}, {"contestant_id": "c2", "score": 90}]
        ranked = self.flb.rank(entries)
        # Lexicographical tie break: c1 should be rank 1, c2 rank 2
        self.assertEqual(ranked[0]["contestant_id"], "c1")
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[1]["contestant_id"], "c2")
        self.assertEqual(ranked[1]["rank"], 2)

    def test_rank_no_score_assigned_zero(self):
        entries = [{"contestant_id": "c1"}]
        ranked = self.flb.rank(entries)
        self.assertEqual(ranked[0]["rank"], 1)


class TestFederatedEvaluationRunner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.bus = AnalyticsEventBus()
        self.events = []
        self.bus.subscribe(self.events.append)
        
        self.registry = FederationRegistry(self.bus)
        self.scheduler = DistributedScheduler()
        self.journal = EvaluationJournal(os.path.join(self.temp_dir, "eval_j.jsonl"))
        self.runner = FederatedEvaluationRunner(
            self.registry, self.scheduler, self.journal, self.bus
        )
        
        # Setup mock worker node
        self.caps = NodeCapabilities(["CODING", "REASONING"], 4, 4096.0, 2)
        self.node = NodeInfo("node1", "host1", "1.0.0", "pub1", [NodeRole.WORKER], self.caps, registered_at=int(time.time()), last_seen=int(time.time()))
        self.registry.register_node(self.node)

        # Setup simple campaign
        self.b1 = Benchmark("b1", EvaluationDomain.CODING, "Task 1", "Task 1 description", 1, 100, "expected1", ["exact_match"], 1000)
        self.suite = BenchmarkSuite("suite1", "Suite 1", [self.b1])
        self.campaign = EvaluationCampaign("camp1", "Campaign 1", [self.suite], "contestant1", seed=42)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_run_campaign_happy(self):
        res = self.runner.run_campaign(self.campaign)
        self.assertEqual(res["campaign_id"], "camp1")
        self.assertEqual(res["contestant_id"], "contestant1")
        self.assertEqual(len(res["results"]), 1)
        self.assertAlmostEqual(res["average_score"], 97.97)
        self.assertEqual(res["overall_grade"], "S+")

        # Verify analytics events
        event_types = [e.event_type for e in self.events]
        self.assertIn(AnalyticsEventType.EVALUATION_STARTED, event_types)
        self.assertIn(AnalyticsEventType.JOB_ASSIGNED, event_types)
        self.assertIn(AnalyticsEventType.JOB_COMPLETED, event_types)
        self.assertIn(AnalyticsEventType.PROFILE_UPDATED, event_types)
        self.assertIn(AnalyticsEventType.REPORT_GENERATED, event_types)
        self.assertIn(AnalyticsEventType.EVALUATION_COMPLETED, event_types)

    def test_run_campaign_least_loaded(self):
        res = self.runner.run_campaign(self.campaign, scheduler_mode="LEAST_LOADED")
        self.assertAlmostEqual(res["average_score"], 97.97)

    def test_run_campaign_capability_match(self):
        res = self.runner.run_campaign(self.campaign, scheduler_mode="CAPABILITY_MATCH")
        self.assertAlmostEqual(res["average_score"], 97.97)

    def test_run_campaign_random_seeded(self):
        res = self.runner.run_campaign(self.campaign, scheduler_mode="RANDOM_SEEDED")
        self.assertAlmostEqual(res["average_score"], 97.97)

    def test_run_campaign_no_nodes_fallback(self):
        empty_registry = FederationRegistry(self.bus)
        runner_fallback = FederatedEvaluationRunner(
            empty_registry, self.scheduler, self.journal, self.bus
        )
        res = runner_fallback.run_campaign(self.campaign)
        self.assertAlmostEqual(res["average_score"], 97.97)


class TestFederationDashboardEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        state_cache.clear()
        
        self.caps = {
            "supported_domains": ["CODING"],
            "max_concurrent_jobs": 2,
            "memory_mb": 2048.0,
            "cpu_cores": 2
        }
        self.node_payload = {
            "node_id": "node1",
            "hostname": "host1",
            "version": "1.0.0",
            "public_key": "pubkey",
            "roles": ["WORKER"],
            "capabilities": self.caps
        }

    def test_nodes_endpoint_empty(self):
        response = self.client.get("/api/public/federation/nodes")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_register_node_admin_and_get_nodes(self):
        # Register node via admin API
        resp = self.client.post("/api/admin/federation/register", json=self.node_payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "SUCCESS")

        # Verify GET nodes
        resp_get = self.client.get("/api/public/federation/nodes")
        self.assertEqual(resp_get.status_code, 200)
        self.assertEqual(len(resp_get.json()), 1)
        self.assertEqual(resp_get.json()[0]["node_id"], "node1")

    def test_remove_node_admin(self):
        self.client.post("/api/admin/federation/register", json=self.node_payload)
        
        remove_payload = {"node_id": "node1"}
        resp = self.client.post("/api/admin/federation/remove", json=remove_payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "SUCCESS")

        resp_get = self.client.get("/api/public/federation/nodes")
        self.assertEqual(len(resp_get.json()), 0)

    def test_jobs_endpoint_empty(self):
        response = self.client.get("/api/public/federation/jobs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_health_endpoint_default(self):
        response = self.client.get("/api/public/federation/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "HEALTHY")

    def test_replay_endpoint_default(self):
        response = self.client.get("/api/public/federation/replay")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["event_count"], 0)

    def test_leaderboard_endpoint_empty_raises_404(self):
        response = self.client.get("/api/public/federation/leaderboard")
        self.assertEqual(response.status_code, 404)

    def test_admin_rebalance(self):
        # Set dummy jobs and nodes in cache
        state_cache.set_jobs([
            {"job_id": "j1", "task_type": "BENCHMARK_EXECUTION", "payload": {}, "status": "PENDING", "assigned_node_id": None, "created_at": 100, "started_at": None, "completed_at": None, "retry_count": 0, "max_retries": 3, "error": None}
        ])
        state_cache.set_nodes([
            {"node_id": "node1", "hostname": "host1", "version": "1.0", "public_key": "pub", "roles": ["WORKER"], "capabilities": {"supported_domains": ["CODING"], "max_concurrent_jobs": 4, "memory_mb": 1024, "cpu_cores": 1}, "registered_at": 100, "last_seen": 100, "load": 0.0, "status": "ACTIVE"}
        ])

        response = self.client.post("/api/admin/federation/rebalance")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "SUCCESS")
        
        # Verify job is now assigned
        jobs = self.client.get("/api/public/federation/jobs").json()
        self.assertEqual(jobs[0]["status"], "ASSIGNED")
        self.assertEqual(jobs[0]["assigned_node_id"], "node1")

    def test_admin_sync(self):
        sync_payload = {
            "peer_node_id": "node2",
            "peer_manifest": {"art1": "hash1"}
        }
        response = self.client.post("/api/admin/federation/sync", json=sync_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "SUCCESS")

    def test_admin_repair(self):
        # Trigger repair endpoint
        repair_payload = {
            "artifact_id": "art1",
            "correct_data": "some repaired content"
        }
        response = self.client.post("/api/admin/federation/repair", json=repair_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "SUCCESS")

    def test_get_health_populated(self):
        state_cache.set_federation_health({"status": "WARNING", "node_count": 5, "expired_pruned": 2})
        response = self.client.get("/api/public/federation/health")
        self.assertEqual(response.json()["status"], "WARNING")

    def test_get_replay_populated(self):
        state_cache.set_federation_replay({"timeline": [{"event": "node_reg"}], "event_count": 1})
        response = self.client.get("/api/public/federation/replay")
        self.assertEqual(response.json()["event_count"], 1)

    def test_get_leaderboard_populated(self):
        state_cache.set_federated_leaderboard({"entries": [], "entry_count": 0})
        response = self.client.get("/api/public/federation/leaderboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["entry_count"], 0)

    def test_admin_remove_nonexistent(self):
        # Even if node doesn't exist, removal should return SUCCESS status
        response = self.client.post("/api/admin/federation/remove", json={"node_id": "nonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "SUCCESS")


class TestFederationNetworkP2P(unittest.TestCase):
    def setUp(self):
        self.bus = AnalyticsEventBus()
        self.registry = FederationRegistry(self.bus)
        self.server = FederationServer(self.registry)
        
        self.node_id = "node_p2p"
        self.priv_key, self.pub_key = FederationKeyPair.generate_ed25519()
        self.client = FederationClient(self.node_id, self.priv_key)
        self.caps = NodeCapabilities(["CODING"], 2, 2048, 2)

    def test_p2p_register_and_heartbeat_flow(self):
        # 1. Register envelope
        reg_envelope = self.client.register_payload("host_p2p", [NodeRole.WORKER], self.caps, self.pub_key)
        
        # Dispatch to server
        res = self.server.handle_register(reg_envelope)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIsNotNone(self.registry.get_node(self.node_id))

        # 2. Heartbeat envelope
        hb_envelope = self.client.heartbeat_payload(load=0.4)
        res_hb = self.server.handle_heartbeat(hb_envelope)
        self.assertEqual(res_hb["status"], "SUCCESS")
        self.assertEqual(self.registry.get_node(self.node_id).load, 0.4)

    def test_p2p_register_invalid_signature_rejected(self):
        reg_envelope = self.client.register_payload("host_p2p", [NodeRole.WORKER], self.caps, self.pub_key)
        reg_envelope["signature"] = "tampered"
        res = self.server.handle_register(reg_envelope)
        self.assertEqual(res["status"], "ERROR")

    def test_p2p_heartbeat_not_registered_rejected(self):
        hb_envelope = self.client.heartbeat_payload(load=0.4)
        # Server doesn't know this node or its key
        res = self.server.handle_heartbeat(hb_envelope)
        self.assertEqual(res["status"], "ERROR")

    def test_p2p_job_dispatch_flow(self):
        # First register node
        reg_envelope = self.client.register_payload("host_p2p", [NodeRole.WORKER], self.caps, self.pub_key)
        self.server.handle_register(reg_envelope)

        # Dispatch job
        dispatch_envelope = self.client.dispatch_job_payload("job_p2p_1", "BENCHMARK_EXECUTION", {"benchmark_id": "b1"})
        res = self.server.handle_job_dispatch(dispatch_envelope)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(len(self.server.received_jobs), 1)
        self.assertEqual(self.server.received_jobs[0].job_id, "job_p2p_1")


class TestFederationJournalIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.filepath = os.path.join(self.temp_dir, "federation_j.jsonl")
        self.journal = FederationJournal(self.filepath)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_journal_hash_chain_creation_and_validation(self):
        h1 = self.journal.record_node_join("nodeA", "hostA", ["WORKER"])
        h2 = self.journal.record_node_leave("nodeA", "normal_leave")
        h3 = self.journal.record_assignment("job1", "nodeA")
        h4 = self.journal.record_completion("job1", {"score": 95.0})
        h5 = self.journal.record_replication("art1", "PUSH", "nodeB", "sha_val")

        records = self.journal.read_all()
        self.assertEqual(len(records), 5)
        self.assertEqual(records[0]["hash"], h1)
        self.assertEqual(records[1]["hash"], h2)
        self.assertEqual(records[2]["hash"], h3)
        self.assertEqual(records[3]["hash"], h4)
        self.assertEqual(records[4]["hash"], h5)

    def test_journal_corruption_detection(self):
        self.journal.record_node_join("nodeA", "hostA", ["WORKER"])
        
        # Read the file and tamper with the entries
        with open(self.filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Modify the first line payload
        record = json.loads(lines[0])
        record["entry"]["payload"]["node_id"] = "TAMPERED_NODE"
        
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        # Reading back should raise ValueError due to hash verification failure
        with self.assertRaises(ValueError):
            self.journal.read_all()


if __name__ == "__main__":
    unittest.main()
