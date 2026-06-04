from __future__ import annotations

from typing import List

from bot_fleet.models import Scenario, ScenarioError

# ---
# ScenarioParser is responsible for reading and validating scenario configs
# ---


class ScenarioParser:
    """Parses and validates Scenario objects from raw YAML input."""

    def parse(self, yaml_content: str) -> Scenario:
        """Parse raw YAML DSL string into a Scenario object hierarchy.

        Args:
            yaml_content: The YAML document content.

        Returns:
            The parsed Scenario model.
        """
        raise NotImplementedError

    def validate(self, scenario: Scenario) -> List[ScenarioError]:
        """Perform semantic and integrity checks on a Scenario configuration.

        Args:
            scenario: The Scenario configuration instance.

        Returns:
            A list of ScenarioError instances detailing validation failures.
        """
        raise NotImplementedError
