from __future__ import annotations

from abc import ABC, abstractmethod

from bot_fleet.models import (
    CancelOrderRequest,
    NewOrderRequest,
    ReplaceOrderRequest,
    SessionTransition,
)

# ---
# Transport acts as the abstraction layer for network transmission from bot to sequencer
# ---


class Transport(ABC):
    """Abstract class defining the network interface for transmitting order requests."""

    @abstractmethod
    def send(
        self,
        message: NewOrderRequest
        | CancelOrderRequest
        | ReplaceOrderRequest
        | SessionTransition,
    ) -> None:
        """Send a message to the downstream sequencing system.

        Args:
            message: The message/request to transmit.
        """
        raise NotImplementedError


class SequencerClient(Transport):
    """Concrete implementation of Transport communicating directly with Sequencer."""

    def __init__(self, address: str) -> None:
        """Initialize connection parameters for SequencerClient.

        Args:
            address: Network target address of the sequencer (e.g. host:port).
        """
        raise NotImplementedError

    def send(
        self,
        message: NewOrderRequest
        | CancelOrderRequest
        | ReplaceOrderRequest
        | SessionTransition,
    ) -> None:
        """Transmit the message over the network socket to the sequencer."""
        raise NotImplementedError
