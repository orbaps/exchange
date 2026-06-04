from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
from reference_engine.models import Fill
from reference_engine.price_level import PriceLevelImpl

# ---
# Auction Value Objects
# ---

@dataclass
class CumulativeLevel:
    """Represents aggregated quantity at a price level for supply/demand curve construction."""
    price: int
    cumulative_qty: int


@dataclass
class CandidatePrice:
    """Represents a price point and the matchable volume at that price."""
    price: int
    volume: int


@dataclass
class AuctionResult:
    """The outcome of an uncrossing auction execution."""
    equilibrium_price: int
    matched_volume: int
    fills: List[Fill]


# ---
# Auction Engine
# ---

class AuctionEngine:
    """Computes the uncrossing equilibrium price and matches orders during session transitions."""

    def compute_equilibrium_price(
        self,
        bids: Dict[int, PriceLevelImpl],
        asks: Dict[int, PriceLevelImpl],
        last_trade_price: int,
    ) -> AuctionResult:
        """Finds the clearing price that maximizes volume, minimizes imbalance, and resolves ties."""
        raise NotImplementedError

    def build_demand_curve(self, bids: Dict[int, PriceLevelImpl]) -> List[CumulativeLevel]:
        """Constructs the cumulative demand curve from bid levels (higher price -> cumulative qty increases)."""
        raise NotImplementedError

    def build_supply_curve(self, asks: Dict[int, PriceLevelImpl]) -> List[CumulativeLevel]:
        """Constructs the cumulative supply curve from ask levels (lower price -> cumulative qty increases)."""
        raise NotImplementedError

    def maximize_volume(
        self,
        demand: List[CumulativeLevel],
        supply: List[CumulativeLevel],
    ) -> List[CandidatePrice]:
        """Identifies prices that maximize crossing volume."""
        raise NotImplementedError

    def break_tie(self, candidates: List[CandidatePrice], last_trade_price: int) -> int:
        """Applies tie-breaking rules (min imbalance, price closest to last trade) to select a single price."""
        raise NotImplementedError
