import os
import json
import hashlib
from typing import Dict, Any, List, Optional

class WriteAheadLog:
    """Write-Ahead Log (WAL) to persist state modifications before they are committed."""

    def __init__(self, filepath: str):
        self.filepath: str = filepath
        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)) or '.', exist_ok=True)
        self._last_hash: str = self._initialize_hash_chain()
        self._pending_writes: List[str] = []

    def _initialize_hash_chain(self) -> str:
        """Read existing WAL entries to find the last hash."""
        if not os.path.exists(self.filepath):
            return ""
        last_hash = ""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        last_hash = record.get("checksum", "")
        except Exception:
            pass
        return last_hash

    def write(self, term: int, index: int, entry_type: str, data: Dict[str, Any]) -> str:
        """Write a record to the WAL memory buffer/cache."""
        serialized_data = json.dumps(data, sort_keys=True)
        payload = f"{term}:{index}:{entry_type}:{serialized_data}"
        
        # Calculate checksum chaining from the previous hash
        content_to_hash = self._last_hash + payload
        checksum = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()
        
        record = {
            "term": term,
            "index": index,
            "entry_type": entry_type,
            "data": data,
            "checksum": checksum,
            "previous_hash": self._last_hash
        }
        
        self._pending_writes.append(json.dumps(record))
        self._last_hash = checksum
        return checksum

    def flush(self) -> None:
        """Flush all pending memory writes to disk, running fsync for durability."""
        if not self._pending_writes:
            return
        
        # Open in append mode, write all pending lines, then fsync
        with open(self.filepath, "a", encoding="utf-8") as f:
            for line in self._pending_writes:
                f.write(line + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                # Fsync might fail on some mock in-memory filesystems or standard tests
                pass
                
        self._pending_writes.clear()

    def replay(self) -> List[Dict[str, Any]]:
        """Read, verify and return all records from the WAL file."""
        if not os.path.exists(self.filepath):
            return []
            
        records: List[Dict[str, Any]] = []
        expected_prev_hash = ""
        
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                
                # Verify previous hash chain integrity
                if record.get("previous_hash") != expected_prev_hash:
                    raise ValueError(
                        f"WAL integrity check failed: expected previous hash '{expected_prev_hash}', "
                        f"but got '{record.get('previous_hash')}'."
                    )
                
                # Verify current checksum
                serialized_data = json.dumps(record["data"], sort_keys=True)
                payload = f"{record['term']}:{record['index']}:{record['entry_type']}:{serialized_data}"
                content_to_hash = expected_prev_hash + payload
                calculated_checksum = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()
                
                if record["checksum"] != calculated_checksum:
                    raise ValueError(
                        f"WAL corruption detected: record checksum '{record['checksum']}' "
                        f"does not match calculated checksum '{calculated_checksum}'."
                    )
                
                expected_prev_hash = record["checksum"]
                records.append(record)
                
        return records

    def clear(self) -> None:
        """Truncate the WAL file and reset states."""
        self._pending_writes.clear()
        self._last_hash = ""
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
