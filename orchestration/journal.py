import json
import hashlib
from typing import List, Dict, Any, Optional

class OrchestrationJournal:
    """Cryptographically chained ledger recording all autonomous decisions, actions, and rebalances."""

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def _calculate_hash(self, index: int, timestamp: float, event_type: str, data: Dict[str, Any], prev_hash: str) -> str:
        serialized_data = json.dumps(data, sort_keys=True)
        payload = f"{index}:{timestamp}:{event_type}:{serialized_data}:{prev_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def append_record(self, event_type: str, data: Dict[str, Any], timestamp: float) -> Dict[str, Any]:
        """Create and append a new hash-chained record to the journal."""
        index = len(self.entries) + 1
        prev_hash = "0" * 64 if not self.entries else self.entries[-1]["hash"]
        
        curr_hash = self._calculate_hash(index, timestamp, event_type, data, prev_hash)
        
        record = {
            "index": index,
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data,
            "prev_hash": prev_hash,
            "hash": curr_hash
        }
        self.entries.append(record)
        return record

    def verify_integrity(self) -> bool:
        """Verify the cryptographic hash chain of the journal."""
        for i, entry in enumerate(self.entries):
            index = entry["index"]
            timestamp = entry["timestamp"]
            event_type = entry["event_type"]
            data = entry["data"]
            prev_hash = entry["prev_hash"]
            stored_hash = entry["hash"]
            
            # 1. Verify index ordering
            if index != i + 1:
                return False
                
            # 2. Verify link to previous entry
            expected_prev = "0" * 64 if i == 0 else self.entries[i - 1]["hash"]
            if prev_hash != expected_prev:
                return False
                
            # 3. Verify current hash matches calculation
            calculated = self._calculate_hash(index, timestamp, event_type, data, prev_hash)
            if stored_hash != calculated:
                return False
                
        return True

    def clear(self) -> None:
        self.entries.clear()
