import json
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from federation.consensus.log import LogEntry, ConsensusLog

class SnapshotAssembler:
    """Assembles chunked snapshots received from the leader, verifying integrity at each step."""

    def __init__(self, snapshot_id: str, chunk_count: int):
        self.snapshot_id: str = snapshot_id
        self.chunk_count: int = chunk_count
        self.received_chunks: Dict[int, str] = {}
        self.last_included_index: int = 0
        self.last_included_term: int = 0

    def receive_chunk(self, chunk_index: int, chunk_count: int, payload: str, checksum: str) -> bool:
        """Validate and record an incoming snapshot chunk."""
        # Verify chunk checksum
        calculated = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if calculated != checksum:
            return False

        self.chunk_count = chunk_count
        self.received_chunks[chunk_index] = payload
        return True

    def is_complete(self) -> bool:
        """Check if all chunks have been received."""
        return len(self.received_chunks) == self.chunk_count

    def assemble_payload(self) -> str:
        """Concatenate all chunk payloads in order."""
        if not self.is_complete():
            raise ValueError("Cannot assemble incomplete snapshot.")
        return "".join(self.received_chunks[i] for i in range(self.chunk_count))

    def verify_assembled(self, expected_hash: str) -> bool:
        """Verify the integrity of the fully reassembled payload against the expected state hash."""
        payload = self.assemble_payload()
        calculated_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return calculated_hash == expected_hash

def compact_log(consensus_log: ConsensusLog, last_included_index: int) -> Tuple[int, int]:
    """
    Compact the consensus log up to last_included_index (inclusive).
    Uses a padding technique to preserve 1-based index offsets without rewriting log.py.
    """
    if last_included_index <= 0 or last_included_index > len(consensus_log.entries):
        return 0, 0
        
    boundary_entry = consensus_log.entries[last_included_index - 1]
    if boundary_entry is None:
        # Already compacted
        return 0, 0
        
    term = boundary_entry.term
    
    # Pad entries before last_included_index with None to preserve length and 1-based indexing
    # Keep the boundary_entry at its index position for replication checks if needed
    new_entries = [None] * (last_included_index - 1) + [boundary_entry] + consensus_log.entries[last_included_index:]
    consensus_log.entries = new_entries
    
    return last_included_index, term
