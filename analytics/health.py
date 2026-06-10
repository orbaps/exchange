from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

class SessionHealthStatus(Enum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    CRASHED = "CRASHED"
    TIMED_OUT = "TIMED_OUT"

@dataclass
class SessionHealth:
    session_id: str
    status: SessionHealthStatus
    last_update: int
    uptime_seconds: float = 0.0
    crash_count: int = 0
    timeout_count: int = 0

class SessionHealthHistory:
    """Tracks session health states over time."""
    
    def __init__(self):
        self.health_map: Dict[str, SessionHealth] = {}
        self.history: Dict[str, List[SessionHealth]] = {}
        
    def update(self, session_id: str, status: SessionHealthStatus, timestamp_ns: int):
        if session_id not in self.health_map:
            h = SessionHealth(session_id, SessionHealthStatus.STARTING, timestamp_ns)
            self.health_map[session_id] = h
            self.history[session_id] = [SessionHealth(**h.__dict__)]
            
        health = self.health_map[session_id]
        
        # Determine status transitions
        if status == SessionHealthStatus.CRASHED and health.status != SessionHealthStatus.CRASHED:
            health.crash_count += 1
        elif status == SessionHealthStatus.TIMED_OUT and health.status != SessionHealthStatus.TIMED_OUT:
            health.timeout_count += 1
            
        health.status = status
        
        # Uptime approximation
        if status in (SessionHealthStatus.RUNNING, SessionHealthStatus.STOPPED, SessionHealthStatus.CRASHED, SessionHealthStatus.TIMED_OUT):
            delta_s = (timestamp_ns - health.last_update) / 1e9
            if delta_s > 0 and health.status == SessionHealthStatus.RUNNING:
                health.uptime_seconds += delta_s
                
        health.last_update = timestamp_ns
        
        # Save historical snapshot
        self.history[session_id].append(SessionHealth(**health.__dict__))
        
    def get_health(self, session_id: str) -> SessionHealth:
        return self.health_map.get(session_id)
        
    def get_history(self, session_id: str) -> List[SessionHealth]:
        return self.history.get(session_id, [])
