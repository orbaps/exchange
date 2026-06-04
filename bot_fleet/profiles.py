from __future__ import annotations

from abc import ABC, abstractmethod

from bot_fleet.models import NewOrderRequest, SymbolConfig
from bot_fleet.prng import SeededPrng

# ---
# TrafficProfile defines the interface for order generators based on specific scenarios
# ---


class TrafficProfile(ABC):
    """Abstract interface defining standard traffic profile generators."""

    @abstractmethod
    def generateOrder(
        self, prng: SeededPrng, symbol: SymbolConfig, currentPrice: int
    ) -> NewOrderRequest:
        """Generate a deterministic order request based on the profile behavior.

        Args:
            prng: Seeded PRNG instance.
            symbol: Target symbol configuration.
            currentPrice: Current market price of the symbol.

        Returns:
            A populated NewOrderRequest DTO.
        """
        raise NotImplementedError


class NormalMarketProfile(TrafficProfile):
    """Generates order requests simulating standard, healthy market trading."""

    def generateOrder(
        self, prng: SeededPrng, symbol: SymbolConfig, currentPrice: int
    ) -> NewOrderRequest:
        """Generate a standard order request under normal market conditions."""
        raise NotImplementedError


class FlashCrashProfile(TrafficProfile):
    """Generates aggressive sell orders and wide spreads to simulate a flash crash."""

    def generateOrder(
        self, prng: SeededPrng, symbol: SymbolConfig, currentPrice: int
    ) -> NewOrderRequest:
        """Generate an order request designed to cascade price downwards."""
        raise NotImplementedError


class CancelStormProfile(TrafficProfile):
    """Generates rapid short-lived orders and high cancel ratios to stress engines."""

    def generateOrder(
        self, prng: SeededPrng, symbol: SymbolConfig, currentPrice: int
    ) -> NewOrderRequest:
        """Generate an order request designed to be canceled shortly after placement."""
        raise NotImplementedError
