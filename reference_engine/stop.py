from __future__ import annotations

from typing import List, Dict
from reference_engine.models import Order, Side

# ---
# Stop Order Registry
# ---

class StopOrderRegistry:
    """Manages dormant stop-limit and stop orders, triggering them when price levels are breached."""

    def __init__(self) -> None:
        """Initializes the StopOrderRegistry with internal sorted tracking for buy and sell stops."""
        self._buy_stops: Dict[int, List[Order]] = {}
        self._sell_stops: Dict[int, List[Order]] = {}

    @property
    def buy_stops(self) -> Dict[int, List[Order]]:
        """Returns the registered buy stop orders mapped by trigger price."""
        return self._buy_stops

    @property
    def sell_stops(self) -> Dict[int, List[Order]]:
        """Returns the registered sell stop orders mapped by trigger price."""
        return self._sell_stops

    def register(self, order: Order) -> None:
        """Registers a stop order to the appropriate trigger side."""
        if order.stop_price is None:
            return
        side_stops = self._buy_stops if order.side == Side.BUY else self._sell_stops
        if order.stop_price not in side_stops:
            side_stops[order.stop_price] = []
        side_stops[order.stop_price].append(order)

    def check_triggers(self, trade_price: int) -> List[Order]:
        """Checks if the trade price triggers any dormant stop orders and returns the triggered list."""
        # Simple placeholder trigger checks
        triggered: List[Order] = []
        return triggered

    def remove(self, order_id: int) -> None:
        """Removes a stop order from the registry (e.g. if canceled before triggering)."""
        pass

