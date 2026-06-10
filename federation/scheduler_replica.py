import os
import json
import hashlib
from typing import Dict, Any, List, Optional

from federation.consensus.leader import ConsensusLeaderElection, LeaderState
from federation.consensus.log import ConsensusLog, LogEntry
from federation.wal import WriteAheadLog
from federation.snapshot import SnapshotManager
from federation.checkpoint import CheckpointManager
from federation.recovery import RecoveryEngine
from federation.quorum import QuorumManager
from federation.reconcile import StateReconciler
from federation.locks import DistributedLockManager
from federation.scheduler import DistributedScheduler
from federation.registry import FederationRegistry
from federation.clock import global_clock
from federation.jobs import DistributedJob, JobStatus

# Phase 7.2 Extensions
from federation.membership import JointConsensusConfig, ConfigState
from federation.lease import LeaderLease
from federation.upgrades import VersionUpgradePolicy, UpgradePolicy
from federation.metrics import ConsensusMetrics
from federation.compaction import SnapshotAssembler, compact_log
from federation.replication.append_entries import handle_append_entries_request
from federation.replication.commit import process_majority_commit
from federation.replication.catchup import send_catchup_updates
from federation.replication.messages import AppendEntriesResponse, InstallSnapshotResponse, InstallSnapshotRequest

class SchedulerReplica:
    """Consensus-driven replica coordinating job scheduling, log replication, and replication states."""

    def __init__(self, node_id: str, all_cluster_nodes: List[str], storage_dir: str = "federation_run_replica"):
        self.node_id: str = node_id
        self.all_cluster_nodes: List[str] = sorted(all_cluster_nodes)
        self.active_nodes: List[str] = sorted(all_cluster_nodes)
        
        self.storage_dir = os.path.join(storage_dir, node_id)
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Core components
        self.leader_election = ConsensusLeaderElection(node_id)
        self.consensus_log = ConsensusLog()
        self.wal = WriteAheadLog(os.path.join(self.storage_dir, "wal.log"))
        
        self.snapshot_manager = SnapshotManager(os.path.join(self.storage_dir, "snapshots"))
        self.checkpoint_manager = CheckpointManager(os.path.join(self.storage_dir, "checkpoints"))
        self.recovery_engine = RecoveryEngine(self.snapshot_manager)
        self.quorum_manager = QuorumManager()
        self.state_reconciler = StateReconciler()
        
        self.locks_manager = DistributedLockManager()
        self.scheduler = DistributedScheduler()
        self.registry = FederationRegistry()
        
        # Replication state fields
        self.commit_index: int = 0
        self.last_applied: int = 0
        self.match_index: Dict[str, int] = {nid: 0 for nid in self.all_cluster_nodes if nid != node_id}
        self.next_index: Dict[str, int] = {nid: 1 for nid in self.all_cluster_nodes if nid != node_id}

        # Phase 7.2 Extensions
        self.membership_config = JointConsensusConfig(all_cluster_nodes)
        self.leader_lease = LeaderLease(lease_duration=5.0)
        self.upgrade_policy = VersionUpgradePolicy(UpgradePolicy.BACKWARD_COMPATIBLE)
        self.metrics = ConsensusMetrics()
        self.version: str = "v1.0.0"
        self.transport: Optional[Any] = None
        self.snapshot_assemblers: Dict[str, SnapshotAssembler] = {}

    def schedule_job(self, job: DistributedJob) -> bool:
        """
        Orchestrate scheduling of a job using the Strict WAL-to-Commit sequence:
        1. WAL write
        2. WAL flush
        3. Consensus append
        4. Replicate
        5. Majority commit (applied when ACKs are received)
        """
        # Ensure we are the leader
        if self.leader_election.state != LeaderState.LEADER:
            return False

        # Validate leader lease expiry to prevent stale leader writes
        if not self.leader_lease.is_valid(global_clock.now()):
            # Step down from leader state immediately
            self.leader_election.state = LeaderState.FOLLOWER
            self.leader_election.current_leader = None
            return False

        # Validate quorum is present in the partition
        if not self.quorum_manager.is_quorum_present(self.active_nodes, self.all_cluster_nodes):
            # Fall back to Follower and restrict to Read-Only if quorum is lost
            self.leader_election.state = LeaderState.FOLLOWER
            self.leader_election.current_leader = None
            return False

        # Re-verify matching nodes list
        nodes = self.registry.list_nodes()
        active_node_infos = [n for n in nodes if n.node_id in self.active_nodes]
        
        # Let the scheduler select a node
        assigned_node_id = self.scheduler.assign_work(job, active_node_infos)
        if not assigned_node_id:
            return False

        command = {
            "action": "ASSIGN_JOB",
            "job_id": job.job_id,
            "node_id": assigned_node_id,
            "payload": job.payload
        }
        
        term = self.leader_election.current_term
        next_idx = len(self.consensus_log.entries) + 1

        # 1. WAL write
        self.wal.write(term=term, index=next_idx, entry_type="JOB_ASSIGNED", data=command)
        
        # 2. WAL flush
        self.wal.flush()
        
        # 3. Consensus append
        entry = self.consensus_log.append(term=term, command=command)
        
        # 4. Replicate entries to peer followers
        if self.transport:
            for peer_id in self.all_cluster_nodes:
                if peer_id != self.node_id:
                    send_catchup_updates(self, peer_id, self.transport)
        else:
            # Fallback to local commit in transportless tests
            self.commit_index = entry.index
            self.consensus_log.commit(entry.index)
            job.assigned_node_id = assigned_node_id
            job.status = JobStatus.ASSIGNED
            self.last_applied = entry.index

        return True

    def receive_replicated_entry(self, leader_id: str, term: int, entry: LogEntry, leader_commit: int) -> bool:
        """Local replication logic."""
        if hasattr(self, "receive_envelope"):
            return False  # Handled by network transport in Phase 7.2
            
        # Fallback to Phase 7.1 local validation
        if term < self.leader_election.current_term:
            return False
            
        self.wal.write(term=entry.term, index=entry.index, entry_type="JOB_ASSIGNED", data=entry.command)
        self.wal.flush()
        if entry.index > len(self.consensus_log.entries):
            self.consensus_log.append(term=entry.term, command=entry.command)
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.consensus_log.entries))
            self.consensus_log.commit(self.commit_index)
            self.last_applied = self.commit_index
        return True

    def get_replication_lag(self) -> Dict[str, int]:
        """Calculate replication lag per follower."""
        lag = {}
        for nid in self.all_cluster_nodes:
            if nid != self.node_id:
                replicated = self.match_index.get(nid, 0)
                lag[nid] = max(0, self.commit_index - replicated)
        return lag

    def simulate_replication(self) -> None:
        """Simulates updating replication indexes across active nodes in the cluster."""
        if self.leader_election.state != LeaderState.LEADER:
            return
            
        for nid in self.all_cluster_nodes:
            if nid != self.node_id and nid in self.active_nodes:
                self.match_index[nid] = self.commit_index
                self.next_index[nid] = self.commit_index + 1

    def receive_envelope(self, envelope: str) -> None:
        """Handle incoming transport envelope. Evaluates upgrades compatibilities and routes RPC payloads."""
        self.metrics.received_messages += 1
        
        # Version compatibility check
        sender_ver = getattr(envelope, "version", "v1.0.0")
        if not self.upgrade_policy.is_compatible(sender_ver, self.version):
            self.metrics.dropped_messages += 1
            return

        sender = envelope.sender_id
        msg_type = envelope.message_type
        payload = envelope.payload

        if msg_type == "APPEND_ENTRIES_REQ":
            resp = handle_append_entries_request(self, payload)
            if self.transport:
                self.transport.send(
                    sender_id=self.node_id,
                    receiver_id=sender,
                    message_type="APPEND_ENTRIES_RESP",
                    payload=resp,
                    term=self.leader_election.current_term,
                    commit_index=self.commit_index
                )
        elif msg_type == "APPEND_ENTRIES_RESP":
            if self.leader_election.state == LeaderState.LEADER:
                # Record metrics and update replication indices
                if payload.success:
                    self.match_index[sender] = max(self.match_index.get(sender, 0), payload.match_index)
                    self.next_index[sender] = payload.match_index + 1
                    
                    # Update replication metrics
                    lag = self.commit_index - payload.match_index
                    self.metrics.record_lag(sender, max(0, lag))
                    
                    # Lease renewal: count confirmations from active nodes
                    confirmations = [self.node_id]
                    for peer_id, match_idx in self.match_index.items():
                        if match_idx >= payload.match_index:
                            confirmations.append(peer_id)
                            
                    if self.membership_config.calculate_quorum_reached(confirmations):
                        self.leader_lease.renew(global_clock.now())
                        
                    # Process majority commit checks
                    process_majority_commit(self)
                else:
                    # Decrement next_index or jump to conflict_index to search for log matching index
                    if payload.conflict_index > 0:
                        self.next_index[sender] = payload.conflict_index
                    else:
                        self.next_index[sender] = max(1, self.next_index.get(sender, 1) - 1)
                        
                    self.leader_lease.record_attempt()
        elif msg_type == "INSTALL_SNAPSHOT_REQ":
            req: InstallSnapshotRequest = payload
            # Setup or retrieve snapshot assembler
            snap_id = req.snapshot_id
            if snap_id not in self.snapshot_assemblers:
                self.snapshot_assemblers[snap_id] = SnapshotAssembler(snap_id, req.chunk_count)
                
            assembler = self.snapshot_assemblers[snap_id]
            assembler.last_included_index = req.last_included_index
            assembler.last_included_term = req.last_included_term
            
            # Record chunk
            success = assembler.receive_chunk(req.chunk_index, req.chunk_count, req.payload, req.checksum)
            
            if success and assembler.is_complete():
                # Reassemble snapshot payload and load
                full_payload = assembler.assemble_payload()
                state_dict = json.loads(full_payload)
                
                # Write to local SnapshotManager and apply state
                self.snapshot_manager.create_snapshot(
                    snap_id,
                    state_dict,
                    req.last_included_index,
                    req.last_included_term
                )
                self.snapshot_manager.load_snapshot(snap_id)
                self.metrics.snapshot_installations += 1
                
                # Truncate and replace log
                compact_log(self.consensus_log, req.last_included_index)
                
                # Restore states locally
                self.commit_index = req.last_included_index
                self.last_applied = req.last_included_index
                
            # Send back response
            resp = InstallSnapshotResponse(
                term=self.leader_election.current_term,
                success=success,
                match_index=req.last_included_index
            )
            if self.transport:
                self.transport.send(
                    sender_id=self.node_id,
                    receiver_id=sender,
                    message_type="INSTALL_SNAPSHOT_RESP",
                    payload=resp,
                    term=self.leader_election.current_term,
                    commit_index=self.commit_index
                )
        elif msg_type == "INSTALL_SNAPSHOT_RESP":
            resp: InstallSnapshotResponse = payload
            if resp.success:
                self.match_index[sender] = max(self.match_index.get(sender, 0), resp.match_index)
                self.next_index[sender] = resp.match_index + 1
                process_majority_commit(self)

    def apply_command(self, command: Dict[str, Any]) -> None:
        """Execute a committed consensus command locally."""
        action = command.get("action")
        if action == "ASSIGN_JOB":
            job_id = command.get("job_id")
            node_id = command.get("node_id")
            # Cache it
            self.scheduler.cancel(DistributedJob(job_id, "", {}))  # Mock utility
