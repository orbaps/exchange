import json
import hashlib
import os
import time
from typing import Dict, Any, List

class FederationJournal:
    """Audit ledger for federation cluster events with SHA256 hash chain verification."""
    
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

    def write_entry(self, event_type: str, payload: Dict[str, Any]) -> str:
        if "timestamp_ns" not in payload:
            payload["timestamp_ns"] = time.time_ns()
            
        entry = {
            "event_type": event_type,
            "payload": payload
        }
        entry_str = json.dumps(entry, sort_keys=True)
        
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

    def record_node_join(self, node_id: str, hostname: str, roles: List[str]) -> str:
        return self.write_entry("NODE_REGISTERED", {
            "node_id": node_id,
            "hostname": hostname,
            "roles": roles,
            "timestamp": int(time.time() * 1000),
            "timestamp_ns": time.time_ns()
        })

    def record_node_leave(self, node_id: str, reason: str) -> str:
        return self.write_entry("NODE_REMOVED", {
            "node_id": node_id,
            "reason": reason,
            "timestamp": int(time.time() * 1000),
            "timestamp_ns": time.time_ns()
        })

    def record_assignment(self, job_id: str, node_id: str) -> str:
        return self.write_entry("JOB_ASSIGNED", {
            "job_id": job_id,
            "node_id": node_id,
            "timestamp": int(time.time() * 1000),
            "timestamp_ns": time.time_ns()
        })

    def record_completion(self, job_id: str, result_data: Dict[str, Any]) -> str:
        return self.write_entry("JOB_COMPLETED", {
            "job_id": job_id,
            "result_data": result_data,
            "timestamp": int(time.time() * 1000),
            "timestamp_ns": time.time_ns()
        })

    def record_replication(self, artifact_id: str, direction: str, peer_node_id: str, hash_val: str) -> str:
        return self.write_entry("ARTIFACT_REPLICATED", {
            "artifact_id": artifact_id,
            "direction": direction,
            "peer_node_id": peer_node_id,
            "hash": hash_val,
            "timestamp": int(time.time() * 1000),
            "timestamp_ns": time.time_ns()
        })

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
                records.append(record)
        return records
