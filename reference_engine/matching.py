from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict
from reference_engine.models import Order, Fill, Side
from reference_engine.price_level import PriceLevelImpl

# ---
# Matcher Strategy Interface
# ---

class MatcherStrategy(ABC):
    """Abstract interface defining matching strategies for book levels."""

    @abstractmethod
    def match(self, incoming: Order, level: PriceLevelImpl) -> List[Fill]:
        """Matches an incoming aggressive order against resting orders at a price level."""
        raise NotImplementedError

    @abstractmethod
    def can_fully_fill(self, incoming: Order, levels: Dict[int, PriceLevelImpl]) -> bool:
        """Determines if the incoming order can be completely filled across available levels."""
        raise NotImplementedError


# ---
# FIFO Price-Time Matcher
# ---

class FifoMatcher(MatcherStrategy):
    """Implements classic Price-Time FIFO matching priority."""

    def match(self, incoming: Order, level: PriceLevelImpl) -> List[Fill]:
        """Matches incoming order sequentially from front to back of the price level queue."""
        fills = []
        remaining_qty = incoming.leaves_qty
        
        for resting_order in level:
            if remaining_qty == 0:
                break
            
            # The match quantity is the minimum of what the incoming order needs
            # and what the resting order has available.
            match_qty = min(remaining_qty, resting_order.leaves_qty)
            
            if match_qty > 0:
                fill = Fill(
                    maker_order_id=resting_order.order_id,
                    taker_order_id=incoming.order_id,
                    price=level.price,
                    quantity=match_qty
                )
                fills.append(fill)
                remaining_qty -= match_qty
                
        return fills

    def can_fully_fill(self, incoming: Order, levels: Dict[int, PriceLevelImpl]) -> bool:
        """Checks if the aggregated quantity across sorted levels is enough to satisfy incoming."""
        remaining_qty = incoming.leaves_qty
        
        for price, level in levels.items():
            # If incoming is a limit order, we can only match up to its limit price
            if incoming.price > 0:
                if incoming.side == Side.BUY and price > incoming.price:
                    break
                if incoming.side == Side.SELL and price < incoming.price:
                    break
                    
            remaining_qty -= level.total_quantity
            if remaining_qty <= 0:
                return True
                
        return False


# ---
# Pro-Rata Matcher
# ---

class ProRataMatcher(MatcherStrategy):
    """Implements proportional allocation matching priority based on resting order sizes."""

    def __init__(self, lot_size: int) -> None:
        """Initializes the ProRataMatcher."""
        raise NotImplementedError

    def match(self, incoming: Order, level: PriceLevelImpl) -> List[Fill]:
        """Matches incoming order proportionally against all resting orders at the level."""
        raise NotImplementedError

    def can_fully_fill(self, incoming: Order, levels: Dict[int, PriceLevelImpl]) -> bool:
        """Checks if the aggregated quantity across sorted levels is enough to satisfy incoming."""
        raise NotImplementedError

    def compute_allocations(self, incoming_qty: int, resting: List[Order]) -> Dict[int, int]:
        """Computes allocation quantities for each resting order based on size proportion."""
        raise NotImplementedError


# ---
# Threshold Pro-Rata Matcher (Hybrid)
# ---

class ThresholdProRataMatcher(MatcherStrategy):
    """Implements hybrid priority: FIFO up to a threshold, and Pro-Rata for the remainder."""

    def __init__(self, pro_rata_threshold: int, fifo_delegate: FifoMatcher, pro_rata_delegate: ProRataMatcher) -> None:
        """Initializes the ThresholdProRataMatcher."""
        raise NotImplementedError

    def match(self, incoming: Order, level: PriceLevelImpl) -> List[Fill]:
        """Matches incoming order using FIFO for first N lots, then Pro-Rata for the rest."""
        raise NotImplementedError

    def can_fully_fill(self, incoming: Order, levels: Dict[int, PriceLevelImpl]) -> bool:
        """Checks if the aggregated quantity across sorted levels is enough to satisfy incoming."""
        raise NotImplementedError
