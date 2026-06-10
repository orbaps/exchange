from enum import Enum
from typing import Tuple

class UpgradePolicy(str, Enum):
    STRICT = "STRICT"
    BACKWARD_COMPATIBLE = "BACKWARD_COMPATIBLE"
    FORWARD_COMPATIBLE = "FORWARD_COMPATIBLE"

class VersionUpgradePolicy:
    """Evaluates protocol version compatibility between cluster members under different policies."""

    def __init__(self, policy: UpgradePolicy = UpgradePolicy.BACKWARD_COMPATIBLE):
        self.policy: UpgradePolicy = policy

    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, int, int]:
        """Parse version string 'v1.2.3' or '1.2.3' into integer tuple (major, minor, patch)."""
        clean = version_str.strip().lower()
        if clean.startswith("v"):
            clean = clean[1:]
        parts = clean.split(".")
        try:
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return (major, minor, patch)
        except ValueError:
            return (0, 0, 0)

    def is_compatible(self, sender_version: str, receiver_version: str) -> bool:
        """
        Evaluate compatibility from sender to receiver.
        - STRICT: Must be equal.
        - BACKWARD_COMPATIBLE: Newer receiver understands older sender (receiver >= sender).
        - FORWARD_COMPATIBLE: Older receiver understands newer sender (receiver <= sender).
        """
        v_send = self.parse_version(sender_version)
        v_recv = self.parse_version(receiver_version)

        if self.policy == UpgradePolicy.STRICT:
            return v_send == v_recv
        elif self.policy == UpgradePolicy.BACKWARD_COMPATIBLE:
            # Receiver is newer or equal to sender
            return v_recv >= v_send
        elif self.policy == UpgradePolicy.FORWARD_COMPATIBLE:
            # Receiver is older or equal to sender
            return v_recv <= v_send
            
        return False
