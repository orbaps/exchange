from enum import Enum


class DeploymentState(Enum):
    """Primary lifecycle visible to users and operators.

    Sequence:
        PENDING → BUILDING → BUILT → DEPLOYING → RUNNING
                                              ↘ FAILED
        Any state → TERMINATED (manual teardown)
    """
    PENDING    = "PENDING"
    BUILDING   = "BUILDING"
    BUILT      = "BUILT"
    DEPLOYING  = "DEPLOYING"
    RUNNING    = "RUNNING"
    FAILED     = "FAILED"
    TERMINATED = "TERMINATED"

    @property
    def is_terminal(self) -> bool:
        return self in (DeploymentState.FAILED, DeploymentState.TERMINATED)

    @property
    def is_active(self) -> bool:
        return self in (DeploymentState.DEPLOYING, DeploymentState.RUNNING)
