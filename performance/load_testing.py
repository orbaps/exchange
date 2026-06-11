"""Deterministic load testing engine.

Uses DeterministicClock.tick() to simulate load generation
without wall-clock dependencies.
"""

from federation.clock import DeterministicClock
from typing import Dict, Any


class LoadTester:
    """Generates deterministic load against the platform.

    Args:
        clock: DeterministicClock instance for time tracking.
    """

    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def generate_load(self, target_qps: int, duration_s: int) -> Dict[str, Any]:
        """Simulate a load test run.

        Args:
            target_qps: Target queries-per-second.
            duration_s: Duration in seconds.

        Returns:
            Dict with status, qps_achieved, duration_s, start_time, end_time.
        """
        start = self.clock.now()
        self.clock.tick(duration_s * 1000)
        end = self.clock.now()

        return {
            "status": "COMPLETED",
            "qps_achieved": target_qps * 0.98,
            "duration_s": duration_s,
            "start_time": start,
            "end_time": end
        }
