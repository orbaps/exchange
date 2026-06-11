from federation.clock import DeterministicClock
import hashlib
import json
from typing import Dict, Any

class DeploymentSync:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def sync(self, target_environment: str, manifest: Dict[str, Any]) -> str:
        # Simulate syncing by computing a deterministic hash of the manifest + clock
        data = {
            "environment": target_environment,
            "manifest": manifest,
            "timestamp": self.clock.now()
        }
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
