import hashlib
from governance.journal import GovernanceJournal

class GovernanceAuditor:
    def __init__(self, journal: GovernanceJournal):
        self.journal = journal

    def verify_chain(self) -> bool:
        records = self.journal.get_all()
        if not records:
            return True
            
        expected_prev = "0" * 64
        for r in records:
            if r.previous_hash != expected_prev:
                return False
                
            data_str = f"{r.previous_hash}_{r.record_id}_{r.timestamp}_{r.decision.action_type}_{r.decision.target}"
            computed_hash = hashlib.sha256(data_str.encode()).hexdigest()
            
            if r.hash != computed_hash:
                return False
                
            expected_prev = r.hash
            
        return True
