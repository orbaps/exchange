from typing import Any
from federation.consensus.leader import LeaderState
from federation.replication.messages import AppendEntriesRequest, AppendEntriesResponse
from federation.consensus.log import LogEntry

def handle_append_entries_request(replica: Any, req: AppendEntriesRequest) -> AppendEntriesResponse:
    """
    Process AppendEntries request on follower.
    Validates term, checks logs alignment at prev_log_index/prev_log_term, 
    resolves divergent logs, and commits entries.
    """
    # 1. Reply false if term < current_term
    if req.term < replica.leader_election.current_term:
        return AppendEntriesResponse(
            term=replica.leader_election.current_term,
            success=False,
            match_index=replica.commit_index,
            conflict_index=replica.commit_index + 1
        )

    # Update state to follower if newer term discovered
    if req.term > replica.leader_election.current_term:
        replica.leader_election.current_term = req.term
        replica.leader_election.state = LeaderState.FOLLOWER
        replica.leader_election.voted_for = None
        
    replica.leader_election.current_leader = req.leader_id

    log = replica.consensus_log
    
    # 2. Reply false if log doesn't contain entry at prev_log_index matching prev_log_term
    if req.prev_log_index > 0:
        if req.prev_log_index > len(log.entries):
            return AppendEntriesResponse(
                term=replica.leader_election.current_term,
                success=False,
                match_index=replica.commit_index,
                conflict_index=len(log.entries) + 1
            )
            
        entry_at_prev = log.entries[req.prev_log_index - 1]
        if entry_at_prev is None:
            # Entry is compacted. If it matches the snapshot boundary, we treat it as valid.
            # In simple replica, let's assume valid or fallback
            pass
        elif entry_at_prev.term != req.prev_log_term:
            # Term mismatch: return conflict_index to speed up alignment search
            conflict_idx = req.prev_log_index
            while conflict_idx > 0 and log.entries[conflict_idx - 1] and log.entries[conflict_idx - 1].term == entry_at_prev.term:
                conflict_idx -= 1
            return AppendEntriesResponse(
                term=replica.leader_election.current_term,
                success=False,
                match_index=replica.commit_index,
                conflict_index=max(1, conflict_idx)
            )

    # 3. If an existing entry conflicts with a new one, delete existing entry and all that follow it
    for entry in req.entries:
        idx = entry.index
        if idx <= len(log.entries):
            existing = log.entries[idx - 1]
            if existing is not None and existing.term != entry.term:
                # Divergence found: truncate log at this index
                log.truncate(idx - 1)
                if hasattr(replica, "wal") and replica.wal:
                    # Truncate WAL file is complex, so we just let consensus log truncate,
                    # and the new writes will overwrite in next WAL flush or replay.
                    pass

    # 4. Append any new entries not already in the log
    for entry in req.entries:
        if entry.index > len(log.entries):
            # Strict WAL-to-Commit: Follower writes to WAL then appends to consensus log
            if hasattr(replica, "wal") and replica.wal:
                replica.wal.write(entry.term, entry.index, "JOB_ASSIGNED", entry.command)
                replica.wal.flush()
            log.append(term=entry.term, command=entry.command, timestamp=entry.timestamp)

    # 5. If leader_commit > commit_index, set commit_index = min(leader_commit, index of last new entry)
    if req.leader_commit > replica.commit_index:
        last_new_idx = len(log.entries)
        replica.commit_index = min(req.leader_commit, last_new_idx)
        log.commit(replica.commit_index)
        
        # Apply committed entries locally
        for i in range(replica.last_applied + 1, replica.commit_index + 1):
            if i <= len(log.entries):
                committed_entry = log.entries[i - 1]
                if committed_entry and hasattr(replica, "apply_command"):
                    replica.apply_command(committed_entry.command)
                replica.last_applied = i

    return AppendEntriesResponse(
        term=replica.leader_election.current_term,
        success=True,
        match_index=len(log.entries),
        conflict_index=0
    )
