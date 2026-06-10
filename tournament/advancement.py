from dataclasses import dataclass
from enum import Enum
from typing import List, Callable, Optional

from leaderboard.models import LeaderboardSnapshot

class AdvancementType(Enum):
    TOP_N = "TOP_N"
    TOP_PERCENT = "TOP_PERCENT"
    MIN_SCORE = "MIN_SCORE"
    CUSTOM = "CUSTOM"

@dataclass
class AdvancementRule:
    rule_type: AdvancementType
    value: float
    custom_func: Optional[Callable[[LeaderboardSnapshot, List[str]], List[str]]] = None

    def __post_init__(self):
        if self.rule_type == AdvancementType.TOP_N and self.value <= 0:
            raise ValueError("TOP_N requires value > 0")
        if self.rule_type == AdvancementType.TOP_PERCENT and (self.value <= 0 or self.value > 100):
            raise ValueError("TOP_PERCENT requires 0 < value <= 100")

    def advance(self, snapshot: LeaderboardSnapshot, current_pool: List[str]) -> List[str]:
        """
        Applies the advancement rule to a given leaderboard snapshot.
        Only contestants currently in `current_pool` are considered.
        Returns the list of advanced contestant_ids.
        """
        import math
        
        # Filter entries to only those in the current pool, and keep them ordered by rank
        eligible_entries = [entry for entry in snapshot.entries if entry.contestant_id in current_pool]
        
        if self.rule_type == AdvancementType.TOP_N:
            limit = int(self.value)
            return [e.contestant_id for e in eligible_entries[:limit]]
            
        elif self.rule_type == AdvancementType.TOP_PERCENT:
            percentage = self.value / 100.0
            limit = max(1, math.ceil(len(current_pool) * percentage))
            return [e.contestant_id for e in eligible_entries[:limit]]
            
        elif self.rule_type == AdvancementType.MIN_SCORE:
            return [e.contestant_id for e in eligible_entries if e.score >= self.value]
            
        elif self.rule_type == AdvancementType.CUSTOM:
            if not self.custom_func:
                raise ValueError("CUSTOM rule requires a custom_func")
            return self.custom_func(snapshot, current_pool)
            
        return []
