from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from federation.consensus.log import LogEntry

@dataclass
class AppendEntriesRequest:
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: List[LogEntry]
    leader_commit: int

@dataclass
class AppendEntriesResponse:
    term: int
    success: bool
    match_index: int
    conflict_index: int

@dataclass
class InstallSnapshotRequest:
    term: int
    leader_id: str
    last_included_index: int
    last_included_term: int
    snapshot_id: str
    chunk_index: int
    chunk_count: int
    payload: str  # Hex or base64 serialized chunk state fragment
    checksum: str  # Checksum for chunk verification

@dataclass
class InstallSnapshotResponse:
    term: int
    success: bool
    match_index: int

@dataclass
class TransportEnvelope:
    message_id: str
    sequence_id: int
    origin_term: int
    origin_commit_index: int
    sender_id: str
    receiver_id: str
    message_type: str  # e.g., "APPEND_ENTRIES_REQ", "INSTALL_SNAPSHOT_REQ", etc.
    payload: Any
