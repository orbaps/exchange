from dataclasses import dataclass
from typing import List, Dict

@dataclass(frozen=True)
class BookSnapshot:
    """Immutable snapshot of the expected order book state."""
    instrument: str
    best_bid: int
    best_ask: int
    spread: int
    bid_depth: int
    ask_depth: int
    timestamp: int


@dataclass(frozen=True)
class OrderSnapshot:
    """Immutable snapshot of the expected order state."""
    order_id: int
    status: str
    remaining_quantity: int
    filled_quantity: int


@dataclass(frozen=True)
class TradeSnapshot:
    """Immutable snapshot of the expected trade state."""
    trade_id: int
    price: int
    quantity: int


@dataclass(frozen=True)
class EngineSnapshot:
    """Immutable snapshot of the complete engine state."""
    book_snapshots: Dict[str, BookSnapshot]
    order_snapshots: Dict[str, Dict[int, OrderSnapshot]]
    trade_snapshots: Dict[str, List[TradeSnapshot]]
