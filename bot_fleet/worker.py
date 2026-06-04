from __future__ import annotations

from bot_fleet.models import CancelOrderRequest, NewOrderRequest, TrafficPhase
from bot_fleet.prng import SeededPrng
from bot_fleet.profiles import TrafficProfile
from bot_fleet.transport import Transport

# ---
# BotWorker executes simulated client behaviors deterministic based on a seed
# ---


class BotWorker:
    """Simulates a trading participant generating order traffic."""

    def __init__(
        self,
        seed: int,
        profile: TrafficProfile,
        transport: Transport,
        worker_id: str,
    ) -> None:
        """Initialize the bot worker.

        Args:
            seed: Initial seed value for this worker's PRNG.
            profile: Selected traffic profile behavior.
            transport: The network client used to send events.
            worker_id: A unique string identifier for this worker.
        """
        raise NotImplementedError

    def generate(self, phase: TrafficPhase) -> None:
        """Run the traffic generation loop according to parameters in the phase.

        Args:
            phase: Configuration detail for the current simulation window.
        """
        raise NotImplementedError

    def sendOrder(self, request: NewOrderRequest) -> None:
        """Send a new order to the transport.

        Args:
            request: The NewOrderRequest DTO.
        """
        raise NotImplementedError

    def sendCancel(self, request: CancelOrderRequest) -> None:
        """Send a cancel request to the transport.

        Args:
            request: The CancelOrderRequest DTO.
        """
        raise NotImplementedError
