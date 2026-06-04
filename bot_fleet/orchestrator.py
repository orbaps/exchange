from __future__ import annotations

from typing import List

from bot_fleet.models import Scenario
from bot_fleet.parser import ScenarioParser
from bot_fleet.worker import BotWorker

# ---
# BotOrchestrator schedules work, allocates tasks to BotWorkers, and triggers runs
# ---


class BotOrchestrator:
    """Manages the full execution lifecycle of a testing scenario across workers."""

    def __init__(self, parser: ScenarioParser, run_id: str) -> None:
        """Initialize the BotOrchestrator.

        Args:
            parser: ScenarioParser instance for load config.
            run_id: A unique identifier for the execution run.
        """
        raise NotImplementedError

    def loadScenario(self, yaml_path: str) -> Scenario:
        """Load and parse the scenario file from disk.

        Args:
            yaml_path: Absolute path to the YAML scenario specification.

        Returns:
            The parsed and validated Scenario object.
        """
        raise NotImplementedError

    def assignWorkers(self, scenario: Scenario, worker_count: int) -> None:
        """Distribute scenario traffic and phase tasks across a specified count of worker instances.

        Args:
            scenario: The parsed Scenario definition.
            worker_count: The number of BotWorker instances to instantiate and partition load to.
        """
        raise NotImplementedError

    def start(self) -> None:
        """Start the traffic generation run, activating all workers."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop the traffic generation run and terminate all workers."""
        raise NotImplementedError
