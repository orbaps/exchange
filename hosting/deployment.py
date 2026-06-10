from dataclasses import dataclass, field
from typing import Optional
from hosting.deployment_state import DeploymentState


@dataclass
class DeploymentRecord:
    """Full audit trail linking build → container for one submission run.

    Traceability chain:
        submission_id  ← from SubmissionRegistry
        build_id       ← from BuildManager
        container_id   ← from ContainerManager
        deployment_id  ← synthetic unique key for this deployment attempt
    """
    deployment_id: str
    submission_id: str
    build_id:      str
    container_id:  str
    start_time:    int           # nanoseconds since epoch
    end_time:      Optional[int] # set when terminal
    status:        DeploymentState = DeploymentState.PENDING
    error:         Optional[str]   = None
