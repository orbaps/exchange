from typing import Optional
from governance.journal import GovernanceJournal
from governance.models import AuditRecord

class GovernanceReplaySystem:
    def __init__(self, journal: GovernanceJournal):
        self.journal = journal
        self.records = journal.get_all()
        self.current_idx = -1

    def step_forward(self) -> Optional[AuditRecord]:
        if self.current_idx + 1 < len(self.records):
            self.current_idx += 1
            return self.records[self.current_idx]
        return None

    def step_backward(self) -> Optional[AuditRecord]:
        if self.current_idx > -1:
            record = self.records[self.current_idx]
            self.current_idx -= 1
            return record
        return None

    def seek(self, index: int) -> bool:
        if -1 <= index < len(self.records):
            self.current_idx = index
            return True
        return False

    def generate_fingerprint(self) -> str:
        # Fingerprint is the hash of the current record we are on
        if self.current_idx == -1:
            return "0" * 64
        return self.records[self.current_idx].hash
