from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from contracts.domain import Side, OrderType, TimeInForce, ExecType, RejectReason, SessionState

# ---
# Core Dataclasses representing inbound and outbound trading messages
# mirroring the protobuf messages.proto schema.
# ---

@dataclass
class NewOrderRequest:
    """Represents a request to enter a new order into the exchange."""
    sequence_no: int
    timestamp_ns: int
    order_id: int
    client_order_id: str
    symbol: str
    side: Side
    order_type: OrderType
    price: int
    quantity: int
    tif: TimeInForce
    party_id: str


@dataclass
class CancelOrderRequest:
    """Represents a request to cancel an existing resting order."""
    sequence_no: int
    timestamp_ns: int
    order_id: int
    client_order_id: str
    symbol: str


@dataclass
class ReplaceOrderRequest:
    """Represents a request to modify price or quantity of an existing order."""
    sequence_no: int
    timestamp_ns: int
    original_order_id: int
    new_order_id: int
    client_order_id: str
    symbol: str
    new_price: int
    new_quantity: int


@dataclass
class SessionTransition:
    """Represents a state change in the exchange session lifecycle."""
    sequence_no: int
    timestamp_ns: int
    symbol: str
    from_state: SessionState
    to_state: SessionState


@dataclass
class ExecutionReport:
    """Represents an execution update emitted by the matching engine."""
    sequence_no: int
    timestamp_ns: int
    execution_id: int
    order_id: int
    client_order_id: str
    symbol: str
    side: Side
    exec_type: ExecType
    last_price: int
    last_qty: int
    leaves_qty: int
    cumulative_qty: int
    original_qty: int
    reject_reason: RejectReason
    match_order_id: int


@dataclass
class PriceLevel:
    """Represents aggregate quantity and order count at a specific price."""
    price: int
    quantity: int
    order_count: int


@dataclass
class BookSnapshot:
    """Represents the complete state snapshot of the order book for a symbol."""
    sequence_no: int
    timestamp_ns: int
    symbol: str
    bids: List[PriceLevel]
    asks: List[PriceLevel]
