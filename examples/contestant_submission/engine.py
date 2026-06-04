from typing import Dict, Any
from validation_engine.snapshots import EngineSnapshot, BookSnapshot, OrderSnapshot, TradeSnapshot

class ContestantMatchingEngine:
    """A minimal standalone engine example for testing."""
    
    def __init__(self):
        self.orders = {}
        self.trades = []

    def submit_order(self, payload: Dict[str, Any]) -> None:
        self.orders[payload['order_id']] = payload

    def cancel_order(self, payload: Dict[str, Any]) -> None:
        if payload['order_id'] in self.orders:
            del self.orders[payload['order_id']]

    def replace_order(self, payload: Dict[str, Any]) -> None:
        if payload['original_order_id'] in self.orders:
            order = self.orders.pop(payload['original_order_id'])
            order['price'] = payload['new_price']
            order['quantity'] = payload['new_quantity']
            order['order_id'] = payload['new_order_id']
            self.orders[payload['new_order_id']] = order

    def snapshot(self) -> EngineSnapshot:
        # Just returning an empty/dummy snapshot for testing.
        return EngineSnapshot(
            book_snapshots={"TEST": BookSnapshot("TEST", 0, 0, 0, 0, 0, 0)},
            order_snapshots={"TEST": {}},
            trade_snapshots={"TEST": []}
        )

    def reset(self) -> None:
        self.orders.clear()
        self.trades.clear()
