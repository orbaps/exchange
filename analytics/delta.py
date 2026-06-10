from dataclasses import dataclass

@dataclass
class RankDelta:
    contestant_id: str
    old_rank: int
    new_rank: int
    delta: int
