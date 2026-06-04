import hashlib
import json
from validation_engine.snapshots import BookSnapshot, OrderSnapshot, TradeSnapshot

class StateFingerprint:
    """Generates deterministic hashes for engine state snapshots."""

    @staticmethod
    def _hash_payload(payload: dict) -> str:
        """Helper to generate a SHA256 hash of a deterministic JSON string."""
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    @staticmethod
    def book_hash(book: BookSnapshot) -> str:
        """Generates a deterministic hash for a BookSnapshot."""
        payload = {
            "instrument": book.instrument,
            "best_bid": book.best_bid,
            "best_ask": book.best_ask,
            "bid_depth": book.bid_depth,
            "ask_depth": book.ask_depth,
            "spread": book.spread
        }
        return StateFingerprint._hash_payload(payload)

    @staticmethod
    def order_hash(order: OrderSnapshot) -> str:
        """Generates a deterministic hash for an OrderSnapshot."""
        payload = {
            "order_id": order.order_id,
            "status": order.status,
            "remaining_quantity": order.remaining_quantity,
            "filled_quantity": order.filled_quantity
        }
        return StateFingerprint._hash_payload(payload)

    @staticmethod
    def trade_hash(trade: TradeSnapshot) -> str:
        """Generates a deterministic hash for a TradeSnapshot."""
        payload = {
            "trade_id": trade.trade_id,
            "price": trade.price,
            "quantity": trade.quantity
        }
        return StateFingerprint._hash_payload(payload)
