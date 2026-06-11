"""Deterministic demo execution for competition showcase presentations.

Uses DeterministicClock.tick() to simulate demo runtime
without wall-clock dependencies.
"""

from federation.clock import DeterministicClock
from typing import Dict, Any


class DemoRunner:
    """Executes pre-canned, replayable demo sequences.

    Args:
        clock: DeterministicClock instance for time tracking.
    """

    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def run_demo(self, demo_id: str) -> Dict[str, Any]:
        """Execute a single demo run.

        Args:
            demo_id: Identifier for the demo to execute.

        Returns:
            Dict with demo_id, status, start_time, end_time.
        """
        start = self.clock.now()
        self.clock.tick(1000)
        end = self.clock.now()
        return {
            "demo_id": demo_id,
            "status": "COMPLETED",
            "start_time": start,
            "end_time": end
        }
