from typing import Any, List, Dict, Optional
from orchestration.models import AutonomousAction
from federation.consensus.leader import LeaderState
from federation.compaction import compact_log
from federation.replication.catchup import send_catchup_updates

class SelfHealingEngine:
    """Executes healing commands targeting node recovery, replication repairs, and network rejoins."""

    def execute_healing_action(
        self,
        action: AutonomousAction,
        cluster_replicas: Dict[str, Any],
        network_simulator: Optional[Any],
        transport: Optional[Any]
    ) -> bool:
        """
        Execute the specified healing action on the target node/replica.
        Returns:
            bool: True if action was successfully executed, False otherwise.
        """
        node_id = action.node_id
        action.status = "IN_PROGRESS"
        
        try:
            # 1. RESTART_NODE
            if action.action_type == "RESTART_NODE":
                if node_id in cluster_replicas:
                    replica = cluster_replicas[node_id]
                    # Simulate restart: mark node inactive, clear leader state
                    replica.active_nodes = [n for n in replica.active_nodes if n != node_id]
                    replica.leader_election.state = LeaderState.FOLLOWER
                    replica.leader_election.current_leader = None
                    action.evidence.append(f"Node {node_id} marked offline for simulated restart.")
                    
                    # Bring it back online
                    replica.active_nodes = sorted(list(set(replica.active_nodes + [node_id])))
                    # Reset metrics
                    if hasattr(replica, "metrics"):
                        replica.metrics.dropped_messages = 0
                    action.evidence.append(f"Node {node_id} restarted and restored online.")
                    action.status = "COMPLETED"
                    return True

            # 2. RECOVER_REPLICA
            elif action.action_type == "RECOVER_REPLICA":
                # Find the leader in the cluster
                leader = None
                for r in cluster_replicas.values():
                    if r.leader_election.state == LeaderState.LEADER:
                        leader = r
                        break
                
                if leader and node_id in cluster_replicas and transport:
                    # Reset replica index maps on leader and send catch-up
                    leader.next_index[node_id] = 1
                    leader.match_index[node_id] = 0
                    send_catchup_updates(leader, node_id, transport)
                    action.evidence.append(f"Triggered catch-up updates from leader {leader.node_id} to node {node_id}.")
                    action.status = "COMPLETED"
                    return True
                else:
                    action.evidence.append("Replication catch-up skipped: Leader or transport not available.")
                    action.status = "FAILED"
                    return False

            # 3. RESTORE_SNAPSHOT
            elif action.action_type == "RESTORE_SNAPSHOT":
                if node_id in cluster_replicas:
                    replica = cluster_replicas[node_id]
                    # Find last snapshot
                    snapshots = replica.snapshot_manager.verify_snapshot("snap_latest")
                    snap_id = "snap_latest" if snapshots else None
                    if not snap_id:
                        # Fallback: check stored files
                        import os
                        files = os.listdir(replica.snapshot_manager.store_dir) if os.path.exists(replica.snapshot_manager.store_dir) else []
                        for f in files:
                            if f.startswith("snapshot_") and f.endswith(".json"):
                                snap_id = f.replace("snapshot_", "").replace(".json", "")
                                break
                    
                    if snap_id:
                        snapshot_data = replica.snapshot_manager.load_snapshot(snap_id)
                        last_idx = snapshot_data["last_included_index"]
                        last_term = snapshot_data["last_included_term"]
                        compact_log(replica.consensus_log, last_idx)
                        replica.commit_index = last_idx
                        replica.last_applied = last_idx
                        action.evidence.append(f"Node {node_id} rolled back and restored from snapshot '{snap_id}' up to index {last_idx}.")
                        action.status = "COMPLETED"
                        return True
                    else:
                        action.evidence.append(f"Snapshot restore failed: No valid snapshot file found for node {node_id}.")
                        action.status = "FAILED"
                        return False

            # 4. REBUILD_REPLICATION
            elif action.action_type == "REBUILD_REPLICATION":
                leader = None
                for r in cluster_replicas.values():
                    if r.leader_election.state == LeaderState.LEADER:
                        leader = r
                        break
                
                if leader and node_id in leader.next_index:
                    leader.next_index[node_id] = len(leader.consensus_log.entries) + 1
                    leader.match_index[node_id] = 0
                    action.evidence.append(f"Rebuild index parameters for node {node_id} on leader {leader.node_id}.")
                    action.status = "COMPLETED"
                    return True

            # 5. REJOIN
            elif action.action_type == "REJOIN":
                if network_simulator and node_id in cluster_replicas:
                    # Restore all links from/to this node
                    for other_id in cluster_replicas.keys():
                        if other_id != node_id:
                            network_simulator.set_link(node_id, other_id, blocked=False)
                            network_simulator.set_link(other_id, node_id, blocked=False)
                    action.evidence.append(f"Restored network simulator links for node {node_id} to rejoin cluster.")
                    
                    # Sync replica node list
                    replica = cluster_replicas[node_id]
                    replica.active_nodes = sorted(list(cluster_replicas.keys()))
                    action.status = "COMPLETED"
                    return True

            action.status = "FAILED"
            action.evidence.append(f"Unsupported healing action type: {action.action_type}")
            return False
            
        except Exception as e:
            action.status = "FAILED"
            action.evidence.append(f"Exception raised during healing execution: {str(e)}")
            return False
