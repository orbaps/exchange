from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeploymentHealth:
    """Operational snapshot for a single hosted submission."""
    submission_id:  str
    container_id:   str
    status:         str          # mirrors ContainerState.value
    uptime_ns:      int  = 0
    restart_count:  int  = 0
    failure_count:  int  = 0
    last_heartbeat: Optional[int] = None    # ns epoch

    @property
    def uptime_seconds(self) -> float:
        return self.uptime_ns / 1e9
