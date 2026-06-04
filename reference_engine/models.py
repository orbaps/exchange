from __future__ import annotations

import decimal
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional, List

# ---
# Enumerations for the Order Life Cycle and Matching engine states
# ---

class Side(Enum):
    """Represents the side of an order."""
    SIDE_UNSPECIFIED = 0
    BUY = 1
    SELL = 2


class OrderType(Enum):
    """Represents the type of an order."""
    ORDER_TYPE_UNSPECIFIED = 0
    LIMIT = 1
    MARKET = 2
    STOP_LIMIT = 3


class TimeInForce(Enum):
    """Represents the time-in-force instructions for an order."""
    TIF_UNSPECIFIED = 0
    GFD = 1
    GTC = 2
    IOC = 3
    FOK = 4


class ExecType(Enum):
    """Represents the execution types emitted in Execution Reports."""
    EXEC_TYPE_UNSPECIFIED = 0
    NEW = 1
    REJECTED = 2
    PARTIALLY_FILLED = 3
    FILLED = 4
    CANCELED = 5
    EXPIRED = 6
    REPLACED = 7
    SMP_CANCELED = 8


class RejectReason(Enum):
    """Represents the reason why an order was rejected by the engine."""
    REJECT_REASON_UNSPECIFIED = 0
    INVALID_PRICE = 1
    INVALID_QUANTITY = 2
    INVALID_SYMBOL = 3
    INVALID_SIDE = 4
    INVALID_ORDER_TYPE = 5
    DUPLICATE_CLIENT_ORDER_ID = 6
    SESSION_NOT_ACCEPTING = 7
    FOK_WOULD_NOT_FILL = 8
    UNKNOWN_ORDER_ID = 9
    ORDER_ALREADY_TERMINAL = 10
    SMP_REJECT = 11


class SessionState(Enum):
    """Represents the current session state of an instrument's book."""
    SESSION_STATE_UNSPECIFIED = 0
    CLOSED = 1
    PRE_OPEN = 2
    NO_CANCEL = 3
    CONTINUOUS = 4
    HALTED = 5
    PRE_CLOSE = 6
    MAINTENANCE = 7


class MatchingAlgorithm(Enum):
    """Represents the matching algorithm configured for an instrument."""
    MATCHING_ALGORITHM_UNSPECIFIED = 0
    PRICE_TIME_FIFO = 1
    PRICE_TIME_PRORATA = 2
    THRESHOLD_PRORATA = 3


class SmpMode(Enum):
    """Represents the self-match prevention behavior configured for an instrument."""
    SMP_MODE_UNSPECIFIED = 0
    SMP_CANCEL_NEWEST = 1
    SMP_CANCEL_OLDEST = 2
    SMP_CANCEL_BOTH = 3
    SMP_DISABLED = 4


class OrderState(Enum):
    """Represents the internal state of an order in the engine."""
    PENDING_NEW = 0
    NEW = 1
    PARTIALLY_FILLED = 2
    FILLED = 3
    CANCELED = 4
    EXPIRED = 5
    REPLACED = 6
    REJECTED = 7
    SMP_CANCELED = 8


class SmpResult(Enum):
    """Represents the outcome of self-match prevention checking."""
    ALLOW_MATCH = 0
    CANCEL_INCOMING = 1
    CANCEL_RESTING = 2
    CANCEL_BOTH = 3


# ---
# Domain Data Transfer Objects and Value Objects
# ---

@dataclass
class InstrumentDefinition:
    """Defines the trading parameters for a specific instrument / symbol."""
    symbol: str
    tick_size: int
    lot_size: int
    max_order_qty: int
    price_band_lower: int
    price_band_upper: int
    matching_algorithm: MatchingAlgorithm
    smp_mode: SmpMode
    prorata_threshold: int

    def __post_init__(self) -> None:
        """Validates the fields of the instrument definition."""
        if not self.symbol or not isinstance(self.symbol, str):
            raise TypeError("symbol must be a non-empty string")
        if self.tick_size <= 0 or not isinstance(self.tick_size, int):
            raise ValueError("tick_size must be a positive integer")
        if self.lot_size <= 0 or not isinstance(self.lot_size, int):
            raise ValueError("lot_size must be a positive integer")
        if self.max_order_qty <= 0 or not isinstance(self.max_order_qty, int):
            raise ValueError("max_order_qty must be a positive integer")
        if self.price_band_lower < 0 or not isinstance(self.price_band_lower, int):
            raise ValueError("price_band_lower must be a non-negative integer")
        if self.price_band_upper < self.price_band_lower or not isinstance(self.price_band_upper, int):
            raise ValueError("price_band_upper must be greater than or equal to price_band_lower")
        if not isinstance(self.matching_algorithm, MatchingAlgorithm):
            raise TypeError("matching_algorithm must be a valid MatchingAlgorithm")
        if not isinstance(self.smp_mode, SmpMode):
            raise TypeError("smp_mode must be a valid SmpMode")
        if self.prorata_threshold < 0 or not isinstance(self.prorata_threshold, int):
            raise ValueError("prorata_threshold must be a non-negative integer")

    def is_tick_aligned(self, price: int) -> bool:
        """Checks if the price is aligned with the tick size."""
        if price <= 0 or not isinstance(price, int):
            return False
        return price % self.tick_size == 0

    def is_lot_aligned(self, qty: int) -> bool:
        """Checks if the quantity is aligned with the lot size."""
        if qty <= 0 or not isinstance(qty, int):
            return False
        return qty % self.lot_size == 0

    def is_within_bands(self, price: int) -> bool:
        """Checks if the price is within the instrument's price bands."""
        if not isinstance(price, int):
            return False
        return self.price_band_lower <= price <= self.price_band_upper



@dataclass
class Fill:
    """Represents a single match fill between an incoming and resting order."""
    maker_order_id: int
    taker_order_id: int
    price: int
    quantity: int


@dataclass
class Trade:
    """Represents a trade generated by a match execution."""
    match_id: int
    symbol: str
    price: int
    quantity: int
    buyer_order_id: int
    seller_order_id: int


@dataclass
class NewOrderRequest:
    """Request to place a new order on the engine."""
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
    stop_price: Optional[int] = None


@dataclass
class CancelOrderRequest:
    """Request to cancel an existing order."""
    sequence_no: int
    timestamp_ns: int
    order_id: int
    client_order_id: str
    symbol: str


@dataclass
class ReplaceOrderRequest:
    """Request to replace / modify an existing order."""
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
    """Control event triggering session state change for an instrument."""
    sequence_no: int
    timestamp_ns: int
    symbol: str
    from_state: SessionState
    to_state: SessionState


@dataclass
class ExecutionReport:
    """Execution report emitted by the engine to report order events."""
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
    """Aggregated price level information for book snapshots."""
    price: int
    quantity: int
    order_count: int


@dataclass
class BookSnapshot:
    """Snapshot of the order book depth for a symbol."""
    sequence_no: int
    timestamp_ns: int
    symbol: str
    bids: List[PriceLevel]
    asks: List[PriceLevel]


# ---
# Order State Machine Object
# ---

class Order:
    """Represents the internal state machine and attributes of an order."""

    def __init__(
        self,
        order_id: int,
        client_order_id: str,
        symbol: str,
        side: Side,
        order_type: OrderType,
        price: int,
        original_qty: int,
        tif: TimeInForce,
        party_id: str,
        sequence_no: int,
        stop_price: Optional[int] = None,
    ) -> None:
        """Initializes the Order state machine object."""
        if not order_id or not isinstance(order_id, int) or order_id <= 0:
            raise ValueError("order_id must be a positive integer")
        if not client_order_id or not isinstance(client_order_id, str):
            raise TypeError("client_order_id must be a non-empty string")
        if not symbol or not isinstance(symbol, str):
            raise TypeError("symbol must be a non-empty string")
        if not isinstance(side, Side):
            raise TypeError("side must be a valid Side")
        if not isinstance(order_type, OrderType):
            raise TypeError("order_type must be a valid OrderType")
        if not isinstance(price, int) or price < 0:
            raise ValueError("price must be a non-negative integer")
        if not isinstance(original_qty, int) or original_qty <= 0:
            raise ValueError("original_qty must be a positive integer")
        if not isinstance(tif, TimeInForce):
            raise TypeError("tif must be a valid TimeInForce")
        if not party_id or not isinstance(party_id, str):
            raise TypeError("party_id must be a non-empty string")
        if not isinstance(sequence_no, int) or sequence_no <= 0:
            raise ValueError("sequence_no must be a positive integer")
        if stop_price is not None and (not isinstance(stop_price, int) or stop_price <= 0):
            raise ValueError("stop_price must be a positive integer if provided")

        self._order_id = order_id
        self._client_order_id = client_order_id
        self._symbol = symbol
        self._side = side
        self._order_type = order_type
        self._price = price
        self._original_qty = original_qty
        self._leaves_qty = original_qty
        self._cumulative_qty = 0
        self._canceled_qty = 0
        self._tif = tif
        self._party_id = party_id
        self._sequence_no = sequence_no
        self._state = OrderState.NEW if order_type != OrderType.STOP_LIMIT else OrderState.PENDING_NEW
        self._is_stop_triggered = False if order_type == OrderType.STOP_LIMIT else True
        self._stop_price = stop_price

    @property
    def order_id(self) -> int:
        """Returns the unique order identifier."""
        return self._order_id

    @property
    def client_order_id(self) -> str:
        """Returns the client order identifier."""
        return self._client_order_id

    @property
    def symbol(self) -> str:
        """Returns the trading symbol."""
        return self._symbol

    @property
    def side(self) -> Side:
        """Returns the side (buy/sell) of the order."""
        return self._side

    @property
    def order_type(self) -> OrderType:
        """Returns the type of the order."""
        return self._order_type

    @property
    def price(self) -> int:
        """Returns the price of the order."""
        return self._price

    @property
    def original_qty(self) -> int:
        """Returns the original quantity of the order."""
        return self._original_qty

    @property
    def leaves_qty(self) -> int:
        """Returns the remaining quantity to fill (leaves quantity)."""
        return self._leaves_qty

    @property
    def cumulative_qty(self) -> int:
        """Returns the total filled quantity."""
        return self._cumulative_qty

    @property
    def canceled_qty(self) -> int:
        """Returns the canceled quantity."""
        return self._canceled_qty

    @property
    def tif(self) -> TimeInForce:
        """Returns the time-in-force instruction."""
        return self._tif

    @property
    def party_id(self) -> str:
        """Returns the party/firm identifier."""
        return self._party_id

    @property
    def sequence_no(self) -> int:
        """Returns the sequence number of the order's entry or modification."""
        return self._sequence_no

    @property
    def state(self) -> OrderState:
        """Returns the current OrderState of the order."""
        return self._state

    @property
    def is_stop_triggered(self) -> bool:
        """Returns whether this stop order has been triggered."""
        return self._is_stop_triggered

    @property
    def stop_price(self) -> Optional[int]:
        """Returns the stop price if this is a stop/stop-limit order."""
        return self._stop_price

    def fill(self, qty: int, fill_price: int, execution_id: int, sequence_no: int, timestamp_ns: int) -> ExecutionReport:
        """Updates order state and returns an ExecutionReport of ExecType.PARTIALLY_FILLED or FILLED."""
        if self.is_terminal():
            raise ValueError("Cannot fill a terminal order")
        if qty <= 0 or qty > self._leaves_qty:
            raise ValueError(f"Invalid fill quantity {qty}, leaves is {self._leaves_qty}")
        if fill_price <= 0:
            raise ValueError("Fill price must be positive")

        self._leaves_qty -= qty
        self._cumulative_qty += qty
        self._sequence_no = sequence_no

        if self._leaves_qty == 0:
            self._state = OrderState.FILLED
            exec_type = ExecType.FILLED
        else:
            self._state = OrderState.PARTIALLY_FILLED
            exec_type = ExecType.PARTIALLY_FILLED

        self.check_invariant()

        return ExecutionReport(
            sequence_no=sequence_no,
            timestamp_ns=timestamp_ns,
            execution_id=execution_id,
            order_id=self._order_id,
            client_order_id=self._client_order_id,
            symbol=self._symbol,
            side=self._side,
            exec_type=exec_type,
            last_price=fill_price,
            last_qty=qty,
            leaves_qty=self._leaves_qty,
            cumulative_qty=self._cumulative_qty,
            original_qty=self._original_qty,
            reject_reason=RejectReason.REJECT_REASON_UNSPECIFIED,
            match_order_id=0, # caller can override or we set to 0
        )

    def cancel(self, execution_id: int, sequence_no: int, timestamp_ns: int) -> ExecutionReport:
        """Cancels the order, updating its state to CANCELED and returns an ExecutionReport."""
        if self.is_terminal():
            raise ValueError("Cannot cancel a terminal order")

        self._canceled_qty = self._leaves_qty
        self._leaves_qty = 0
        self._state = OrderState.CANCELED
        self._sequence_no = sequence_no

        self.check_invariant()

        return ExecutionReport(
            sequence_no=sequence_no,
            timestamp_ns=timestamp_ns,
            execution_id=execution_id,
            order_id=self._order_id,
            client_order_id=self._client_order_id,
            symbol=self._symbol,
            side=self._side,
            exec_type=ExecType.CANCELED,
            last_price=0,
            last_qty=0,
            leaves_qty=self._leaves_qty,
            cumulative_qty=self._cumulative_qty,
            original_qty=self._original_qty,
            reject_reason=RejectReason.REJECT_REASON_UNSPECIFIED,
            match_order_id=0,
        )

    def expire(self, execution_id: int, sequence_no: int, timestamp_ns: int) -> ExecutionReport:
        """Expires the order, updating its state to EXPIRED and returns an ExecutionReport."""
        if self.is_terminal():
            raise ValueError("Cannot expire a terminal order")

        self._canceled_qty = self._leaves_qty
        self._leaves_qty = 0
        self._state = OrderState.EXPIRED
        self._sequence_no = sequence_no

        self.check_invariant()

        return ExecutionReport(
            sequence_no=sequence_no,
            timestamp_ns=timestamp_ns,
            execution_id=execution_id,
            order_id=self._order_id,
            client_order_id=self._client_order_id,
            symbol=self._symbol,
            side=self._side,
            exec_type=ExecType.EXPIRED,
            last_price=0,
            last_qty=0,
            leaves_qty=self._leaves_qty,
            cumulative_qty=self._cumulative_qty,
            original_qty=self._original_qty,
            reject_reason=RejectReason.REJECT_REASON_UNSPECIFIED,
            match_order_id=0,
        )

    def smp_cancel(self, execution_id: int, sequence_no: int, timestamp_ns: int) -> ExecutionReport:
        """Cancels the order due to SMP, updating state to SMP_CANCELED and returns an ExecutionReport."""
        if self.is_terminal():
            raise ValueError("Cannot SMP cancel a terminal order")

        self._canceled_qty = self._leaves_qty
        self._leaves_qty = 0
        self._state = OrderState.SMP_CANCELED
        self._sequence_no = sequence_no

        self.check_invariant()

        return ExecutionReport(
            sequence_no=sequence_no,
            timestamp_ns=timestamp_ns,
            execution_id=execution_id,
            order_id=self._order_id,
            client_order_id=self._client_order_id,
            symbol=self._symbol,
            side=self._side,
            exec_type=ExecType.SMP_CANCELED,
            last_price=0,
            last_qty=0,
            leaves_qty=self._leaves_qty,
            cumulative_qty=self._cumulative_qty,
            original_qty=self._original_qty,
            reject_reason=RejectReason.REJECT_REASON_UNSPECIFIED,
            match_order_id=0,
        )

    def replace(self, new_price: int, new_qty: int, new_order_id: int, execution_id: int, sequence_no: int, timestamp_ns: int) -> ExecutionReport:
        """Modifies order price/quantity, transitions to REPLACED, and returns an ExecutionReport."""
        if self.is_terminal():
            raise ValueError("Cannot replace a terminal order")
        if new_price < 0:
            raise ValueError("New price must be non-negative")
        if new_qty <= self._cumulative_qty:
            raise ValueError("New quantity must be greater than cumulative filled quantity")

        self._canceled_qty = self._leaves_qty
        self._leaves_qty = 0
        self._state = OrderState.REPLACED
        self._sequence_no = sequence_no

        self.check_invariant()

        return ExecutionReport(
            sequence_no=sequence_no,
            timestamp_ns=timestamp_ns,
            execution_id=execution_id,
            order_id=self._order_id,
            client_order_id=self._client_order_id,
            symbol=self._symbol,
            side=self._side,
            exec_type=ExecType.REPLACED,
            last_price=new_price,
            last_qty=new_qty,
            leaves_qty=0,
            cumulative_qty=self._cumulative_qty,
            original_qty=self._original_qty,
            reject_reason=RejectReason.REJECT_REASON_UNSPECIFIED,
            match_order_id=0,
        )

    def trigger_stop(self) -> None:
        """Marks the stop order as triggered."""
        if self._order_type != OrderType.STOP_LIMIT:
            raise ValueError("Only STOP_LIMIT orders can be triggered")
        self._is_stop_triggered = True
        self._state = OrderState.NEW

    def is_terminal(self) -> bool:
        """Checks if the order is in a terminal state (FILLED, CANCELED, REJECTED, EXPIRED, SMP_CANCELED)."""
        return self._state in (OrderState.FILLED, OrderState.CANCELED, OrderState.EXPIRED, OrderState.REJECTED, OrderState.SMP_CANCELED)

    def is_active(self) -> bool:
        """Checks if the order is currently active (NEW or PARTIALLY_FILLED)."""
        return self._state in (OrderState.NEW, OrderState.PARTIALLY_FILLED)

    def check_invariant(self) -> bool:
        """Enforces order quantity invariants: original_qty == cumulative_qty + leaves_qty + canceled_qty."""
        valid = self._original_qty == (self._cumulative_qty + self._leaves_qty + self._canceled_qty)
        if not valid:
            raise AssertionError(
                f"Invariant broken: original_qty={self._original_qty} != "
                f"cumulative_qty={self._cumulative_qty} + leaves_qty={self._leaves_qty} + "
                f"canceled_qty={self._canceled_qty}"
            )
        return True

