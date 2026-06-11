import hashlib
from dataclasses import dataclass
from typing import List

@dataclass
class StrategicJournalRecord:
    record_id: str
    previous_hash: str
    timestamp: float
    plan_id: str
    action: str
    cluster_id: str
    record_hash: str

class StrategicJournal:
    def __init__(self):
        self.records: List[StrategicJournalRecord] = []
        self._last_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    def append(self, timestamp: float, plan_id: str, action: str, cluster_id: str) -> StrategicJournalRecord:
        # Formula: SHA256(previous_hash + timestamp + plan_id + action + cluster_id)
        data = f"{self._last_hash}{timestamp}{plan_id}{action}{cluster_id}"
        record_hash = hashlib.sha256(data.encode("utf-8")).hexdigest()
        
        record_id = f"sj_{len(self.records)}_{timestamp}"
        
        record = StrategicJournalRecord(
            record_id=record_id,
            previous_hash=self._last_hash,
            timestamp=timestamp,
            plan_id=plan_id,
            action=action,
            cluster_id=cluster_id,
            record_hash=record_hash
        )
        
        self.records.append(record)
        self._last_hash = record_hash
        return record

    def get_all(self) -> List[StrategicJournalRecord]:
        return self.records
