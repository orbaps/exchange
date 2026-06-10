import json
import hashlib
import os
from typing import Dict, Any, List

class EvaluationJournal:
    """Audit ledger for evaluation events with SHA256 hash chain verification."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)) or '.', exist_ok=True)
        self._last_hash = self._initialize_hash_chain()
        
    def _initialize_hash_chain(self) -> str:
        if not os.path.exists(self.filepath):
            return ""
        last_hash = ""
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    last_hash = record.get("hash", "")
        return last_hash
        
    def write_entry(self, event_type: str, run_id: str, benchmark_id: str, payload: Dict[str, Any]) -> str:
        entry = {
            "event_type": event_type,
            "run_id": run_id,
            "benchmark_id": benchmark_id,
            "payload": payload
        }
        entry_str = json.dumps(entry, sort_keys=True)
        
        # Hash chain: hash(previous_hash + current_entry_str)
        content_to_hash = self._last_hash + entry_str
        entry_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()
        self._last_hash = entry_hash
        
        record = {
            "entry": entry,
            "hash": entry_hash
        }
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            
        return entry_hash
        
    def read_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            return []
        records = []
        last_hash = ""
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                
                # Verify hash chain
                entry_str = json.dumps(record["entry"], sort_keys=True)
                content_to_hash = last_hash + entry_str
                expected_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()
                if expected_hash != record["hash"]:
                    raise ValueError(f"Journal integrity check failed. Corruption detected for record: {record}")
                    
                last_hash = record["hash"]
                records.append(record["entry"])
        return records
