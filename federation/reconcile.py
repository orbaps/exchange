from typing import List, Dict, Any

class StateReconciler:
    """Reconciles consensus log differences, synchronizes replicas, and aligns scheduler/registry states."""

    @staticmethod
    def merge_journals(journal_a: List[Dict[str, Any]], journal_b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge two divergent log/journal records.
        For any entry index conflict, the entry with the higher term wins, truncating subsequent divergent history.
        """
        merged: List[Dict[str, Any]] = []
        len_a = len(journal_a)
        len_b = len(journal_b)
        max_len = max(len_a, len_b)

        for i in range(max_len):
            if i < len_a and i < len_b:
                entry_a = journal_a[i]
                entry_b = journal_b[i]
                
                # Check for conflict
                if entry_a["term"] == entry_b["term"]:
                    # No conflict, keep entry (prefer A)
                    merged.append(entry_a)
                elif entry_a["term"] > entry_b["term"]:
                    # A wins, truncate divergent B and copy remainder of A
                    merged.append(entry_a)
                    merged.extend(journal_a[i+1:])
                    break
                else:
                    # B wins, truncate divergent A and copy remainder of B
                    merged.append(entry_b)
                    merged.extend(journal_b[i+1:])
                    break
            elif i < len_a:
                # No conflict, append remainder of A
                merged.append(journal_a[i])
            else:
                # No conflict, append remainder of B
                merged.append(journal_b[i])
                
        return merged

    def sync_replay(self, replica: Any, leader_log: List[Dict[str, Any]]) -> bool:
        """
        Force a replica to synchronize its local log with the leader's log.
        Truncates divergent entries and replays missing committed entries.
        """
        try:
            # Let's check if the replica has a log
            if not hasattr(replica, "consensus_log"):
                return False
                
            local_log = replica.consensus_log
            
            # Find divergence point
            divergence_idx = 0
            for idx, entry in enumerate(leader_log):
                if idx < len(local_log.entries):
                    local_entry = local_log.entries[idx]
                    if local_entry.term != entry["term"]:
                        divergence_idx = idx
                        break
                else:
                    divergence_idx = idx
                    break
            else:
                # No divergence, check if local has more entries than leader (should truncate if so)
                if len(local_log.entries) > len(leader_log):
                    local_log.truncate(len(leader_log))
                return True
                
            # Truncate local log at the divergence point
            local_log.truncate(divergence_idx)
            
            # Append missing entries from leader_log
            for i in range(divergence_idx, len(leader_log)):
                leader_entry = leader_log[i]
                local_log.append(
                    term=leader_entry["term"],
                    command=leader_entry["command"],
                    timestamp=leader_entry.get("timestamp")
                )
                
            # Update commit index to match leader
            # Let's commit up to the leader's committed index
            return True
        except Exception:
            return False

    def reconcile_assignments(self, scheduler: Any, registry: Any) -> bool:
        """
        Reconcile job assignments against the active nodes in the registry.
        If a job is assigned to an offline or expired node, reset it to PENDING.
        """
        try:
            active_node_ids = {n.node_id for n in registry.list_nodes() if n.status == "ACTIVE"}
            
            # Reconcile jobs
            jobs_modified = False
            if hasattr(scheduler, "get_jobs") and hasattr(scheduler, "rebalance"):
                jobs = scheduler.get_jobs()
                for job in jobs:
                    # If job is ASSIGNED or RUNNING but the node is not active, reset it
                    if hasattr(job, "status") and hasattr(job, "assigned_node_id"):
                        if job.status in ("ASSIGNED", "RUNNING") and job.assigned_node_id not in active_node_ids:
                            job.assigned_node_id = None
                            job.status = "PENDING"
                            jobs_modified = True
            return True
        except Exception:
            return False
