import json
import hashlib
from typing import Any
from federation.replication.messages import AppendEntriesRequest, InstallSnapshotRequest

def send_catchup_updates(leader: Any, follower_id: str, transport: Any) -> None:
    """
    Leader-side catch-up synchronization.
    If the follower next_index is compacted, triggers chunked snapshot replication.
    Otherwise, sends AppendEntries with all lagging entries.
    """
    next_idx = leader.next_index.get(follower_id, 1)
    if next_idx <= 0:
        next_idx = 1
        leader.next_index[follower_id] = 1

    log = leader.consensus_log
    term = leader.leader_election.current_term

    # Determine if next_idx lies in the compacted log region
    # Look for the first non-None entry in our log
    compacted_boundary = 0
    boundary_term = 0
    for entry in log.entries:
        if entry is None:
            compacted_boundary += 1
        else:
            if compacted_boundary > 0:
                boundary_term = log.entries[compacted_boundary].term if compacted_boundary < len(log.entries) else 0
            break

    if compacted_boundary > 0:
        compacted_boundary = compacted_boundary + 1

    # If the required index is compacted, we MUST send a snapshot
    if next_idx <= compacted_boundary:
        # Load snapshot state from SnapshotManager
        snapshot_id = f"snap_{compacted_boundary}"
        try:
            snapshot_data = leader.snapshot_manager.load_snapshot(snapshot_id)
            state_str = json.dumps(snapshot_data["state"], sort_keys=True)
            
            # Segment state_str into small chunks (e.g. 50 characters) to simulate network transfers
            chunk_size = 50
            chunks = [state_str[i:i + chunk_size] for i in range(0, len(state_str), chunk_size)]
            chunk_count = len(chunks)
            
            # Send each chunk to the follower
            for idx, chunk_payload in enumerate(chunks):
                chk = hashlib.sha256(chunk_payload.encode("utf-8")).hexdigest()
                req = InstallSnapshotRequest(
                    term=term,
                    leader_id=leader.node_id,
                    last_included_index=snapshot_data["last_included_index"],
                    last_included_term=snapshot_data["last_included_term"],
                    snapshot_id=snapshot_id,
                    chunk_index=idx,
                    chunk_count=chunk_count,
                    payload=chunk_payload,
                    checksum=chk
                )
                transport.send(
                    sender_id=leader.node_id,
                    receiver_id=follower_id,
                    message_type="INSTALL_SNAPSHOT_REQ",
                    payload=req,
                    term=term,
                    commit_index=leader.commit_index
                )
        except Exception:
            # Snapshot not created yet, skip
            pass
        return

    # Normal AppendEntries replication path
    prev_log_index = next_idx - 1
    prev_log_term = 0
    if prev_log_index > 0:
        if prev_log_index <= len(log.entries):
            prev_entry = log.entries[prev_log_index - 1]
            prev_log_term = prev_entry.term if prev_entry else boundary_term

    # Send entries starting from next_idx
    entries_to_send = []
    for i in range(next_idx, len(log.entries) + 1):
        if i <= len(log.entries):
            entry = log.entries[i - 1]
            if entry:
                entries_to_send.append(entry)

    req = AppendEntriesRequest(
        term=term,
        leader_id=leader.node_id,
        prev_log_index=prev_log_index,
        prev_log_term=prev_log_term,
        entries=entries_to_send,
        leader_commit=leader.commit_index
    )

    transport.send(
        sender_id=leader.node_id,
        receiver_id=follower_id,
        message_type="APPEND_ENTRIES_REQ",
        payload=req,
        term=term,
        commit_index=leader.commit_index
    )
