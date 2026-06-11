import hashlib
from typing import List, Optional
from governance.models import AuditRecord, GovernanceDecision

class GovernanceJournal:
    def __init__(self):
        self.records: List[AuditRecord] = []
        self.last_hash = "0" * 64

    def append(self, decision: GovernanceDecision, timestamp: int) -> AuditRecord:
        record_id = f"aud_{decision.decision_id}"
        
        # Create a deterministic string to hash
        data_str = f"{self.last_hash}_{record_id}_{timestamp}_{decision.action_type}_{decision.target}"
        new_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        record = AuditRecord(record_id, self.last_hash, timestamp, decision, new_hash)
        self.records.append(record)
        self.last_hash = new_hash
        return record
        
    def get_all(self) -> List[AuditRecord]:
        return self.records
