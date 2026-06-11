import hashlib
from strategic.journal import StrategicJournal, StrategicJournalRecord
from typing import List, Optional

class StrategicReplay:
    def __init__(self, journal: StrategicJournal):
        self.journal = journal
        self.cursor = 0

    def compute_fingerprint(self, record: StrategicJournalRecord) -> str:
        data = f"{record.previous_hash}{record.timestamp}{record.plan_id}{record.action}{record.cluster_id}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def step_forward(self) -> Optional[StrategicJournalRecord]:
        if self.cursor < len(self.journal.records):
            record = self.journal.records[self.cursor]
            
            # Verify integrity
            computed_hash = self.compute_fingerprint(record)
            if computed_hash != record.record_hash:
                raise ValueError(f"Integrity check failed at cursor {self.cursor}")
                
            self.cursor += 1
            return record
        return None

    def step_backward(self) -> Optional[StrategicJournalRecord]:
        if self.cursor > 0:
            self.cursor -= 1
            return self.journal.records[self.cursor]
        return None

    def seek(self, target_cursor: int) -> bool:
        if 0 <= target_cursor <= len(self.journal.records):
            self.cursor = target_cursor
            return True
        return False
