"""Showcase management for competition judging presentations.

Showcase Fingerprint Formula:
    fingerprint = SHA256(json.dumps({
        "showcase_id": f"showcase_{clock.now()}",
        "result": {demo_runner output},
        "timestamp": clock.now()
    }, sort_keys=True))
"""

from federation.clock import DeterministicClock
from demo.demo_runner import DemoRunner
from typing import Dict, Any
import hashlib
import json


class ShowcaseManager:
    """Generates deterministic showcase presentations with SHA-256 fingerprints.

    Args:
        clock: DeterministicClock instance shared with the DemoRunner.
    """

    def __init__(self, clock: DeterministicClock):
        self.clock = clock
        self.runner = DemoRunner(clock)

    def generate_showcase(self) -> Dict[str, Any]:
        """Generate a full showcase with a deterministic fingerprint.

        Returns:
            Dict containing showcase_id, result, timestamp, and
            a SHA-256 fingerprint of the showcase data.
        """
        now = self.clock.now()
        result = self.runner.run_demo("SHOWCASE_1")

        showcase_data = {
            "showcase_id": f"showcase_{now}",
            "result": result,
            "timestamp": now
        }

        fingerprint = hashlib.sha256(json.dumps(showcase_data, sort_keys=True).encode("utf-8")).hexdigest()
        showcase_data["fingerprint"] = fingerprint
        return showcase_data
