import json
import hashlib
import os
from typing import Dict, Any, List

class TournamentJournal:
    """Persists tournament events to a JSONL file with SHA256 hashing."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filepath) or '.', exist_ok=True)
        self._last_hash = self._initialize_hash_chain()
        
    def _initialize_hash_chain(self) -> str:
        if not os.path.exists(self.filepath):
            return ""
        last_hash = ""
        with open(self.filepath, "r") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    last_hash = record.get("hash", "")
        return last_hash
        
    def _write_event(self, event_type: str, payload: Dict[str, Any]):
        entry = {
            "event_type": event_type,
            "payload": payload
        }
        entry_str = json.dumps(entry, sort_keys=True)
        
        # Hash chain: hash(previous_hash + entry_str)
        content_to_hash = self._last_hash + entry_str
        entry_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()
        self._last_hash = entry_hash
        
        record = {
            "entry": entry,
            "hash": entry_hash
        }
        with open(self.filepath, "a") as f:
            f.write(json.dumps(record) + "\n")
            
    def record_snapshot(self, tournament_id: str, stage_id: str, snapshot: 'LeaderboardSnapshot'):
        entries = []
        for e in snapshot.entries:
            entries.append({
                "contestant_id": e.contestant_id,
                "rank": e.rank,
                "score": e.score
            })
            
        self._write_event("SNAPSHOT", {
            "tournament_id": tournament_id,
            "stage_id": stage_id,
            "entries": entries
        })
            
    def record_stage_start(self, tournament_id: str, stage_id: str, contestants: List[str]):
        self._write_event("STAGE_START", {
            "tournament_id": tournament_id,
            "stage_id": stage_id,
            "contestants": contestants
        })
        
    def record_stage_end(self, tournament_id: str, stage_id: str, rankings: List[str]):
        self._write_event("STAGE_END", {
            "tournament_id": tournament_id,
            "stage_id": stage_id,
            "rankings": rankings
        })
        
    def record_advancement(self, tournament_id: str, stage_id: str, advanced: List[str]):
        self._write_event("ADVANCEMENT", {
            "tournament_id": tournament_id,
            "stage_id": stage_id,
            "advanced": advanced
        })
        
    def record_elimination(self, tournament_id: str, stage_id: str, eliminated: List[str]):
        self._write_event("ELIMINATION", {
            "tournament_id": tournament_id,
            "stage_id": stage_id,
            "eliminated": eliminated
        })
        
    def record_winner_declaration(self, tournament_id: str, winner: str):
        self._write_event("WINNER_DECLARATION", {
            "tournament_id": tournament_id,
            "winner": winner
        })
        
    def record_tournament_start(self, tournament_id: str, locked_contestants: List[str]):
        self._write_event("TOURNAMENT_START", {
            "tournament_id": tournament_id,
            "locked_contestants": locked_contestants
        })
        
    def read_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            return []
        records = []
        last_hash = ""
        with open(self.filepath, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                
                # Verify hash chain
                entry_str = json.dumps(record["entry"], sort_keys=True)
                content_to_hash = last_hash + entry_str
                expected_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()
                if expected_hash != record["hash"]:
                    raise ValueError(f"Journal corruption detected. Hash mismatch for record: {record}")
                    
                last_hash = record["hash"]
                records.append(record["entry"])
        return records
