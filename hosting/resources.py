from dataclasses import dataclass, field
from enum import Enum


class ResourceProfileType(Enum):
    SMALL  = "small"
    MEDIUM = "medium"
    LARGE  = "large"


@dataclass(frozen=True)
class ResourceProfile:
    """Describes the resource budget enforced for a single container."""
    name:                  ResourceProfileType
    cpu_limit:             float   # fractional vCPUs
    memory_limit_mb:       float
    disk_limit_mb:         float
    execution_timeout_sec: float


# ── Built-in profiles ─────────────────────────────────────────────────────────

SMALL = ResourceProfile(
    name=ResourceProfileType.SMALL,
    cpu_limit=1.0,
    memory_limit_mb=512.0,
    disk_limit_mb=1024.0,
    execution_timeout_sec=30.0,
)

MEDIUM = ResourceProfile(
    name=ResourceProfileType.MEDIUM,
    cpu_limit=2.0,
    memory_limit_mb=1024.0,
    disk_limit_mb=4096.0,
    execution_timeout_sec=60.0,
)

LARGE = ResourceProfile(
    name=ResourceProfileType.LARGE,
    cpu_limit=4.0,
    memory_limit_mb=4096.0,
    disk_limit_mb=16384.0,
    execution_timeout_sec=120.0,
)

PROFILE_MAP = {
    ResourceProfileType.SMALL:  SMALL,
    ResourceProfileType.MEDIUM: MEDIUM,
    ResourceProfileType.LARGE:  LARGE,
}


def get_profile(profile_type: ResourceProfileType) -> ResourceProfile:
    return PROFILE_MAP[profile_type]
