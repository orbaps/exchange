import time
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class TournamentSchedule:
    start_time: int
    registration_deadline: int
    stage_times: Dict[str, int] = field(default_factory=dict)
    
    def is_open(self, current_time: int = None) -> bool:
        if current_time is None:
            current_time = time.time_ns()
        return current_time <= self.registration_deadline
        
    def is_running(self, current_time: int = None) -> bool:
        if current_time is None:
            current_time = time.time_ns()
        return current_time >= self.start_time
        
    def is_closed(self, current_time: int = None) -> bool:
        # For our mock/simulated environment, closed typically means registration is over 
        # and the tournament is actively running or completed.
        if current_time is None:
            current_time = time.time_ns()
        return current_time > self.registration_deadline
