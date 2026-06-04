from __future__ import annotations

import dataclasses
from abc import ABC
from enum import Enum, IntEnum
from typing import List

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Side(IntEnum):
    """Enumeration for order side (BUY or SELL)."""

    SIDE_UNSPECIFIED = 0
    BUY = 1
    SELL = 2


class OrderType(IntEnum):
    """Enumeration for order type classification."""

    ORDER_TYPE_UNSPECIFIED = 0
    LIMIT = 1
    MARKET = 2
    STOP_LIMIT = 3


class TimeInForce(IntEnum):
    """Enumeration for order time-in-force options."""

    TIF_UNSPECIFIED = 0
    GFD = 1
    GTC = 2
    IOC = 3
    FOK = 4


class SessionState(IntEnum):
    """Enumeration for the exchange session states."""

    SESSION_STATE_UNSPECIFIED = 0
    CLOSED = 1
    PRE_OPEN = 2
    NO_CANCEL = 3
    CONTINUOUS = 4
    HALTED = 5
    PRE_CLOSE = 6
    MAINTENANCE = 7


class MatchingAlgorithm(IntEnum):
    """Enumeration for matching algorithm types."""

    MATCHING_ALGORITHM_UNSPECIFIED = 0
    PRICE_TIME_FIFO = 1
    PRICE_TIME_PRORATA = 2
    THRESHOLD_PRORATA = 3


class SmpMode(IntEnum):
    """Enumeration for Self-Match Prevention modes."""

    SMP_MODE_UNSPECIFIED = 0
    SMP_CANCEL_NEWEST = 1
    SMP_CANCEL_OLDEST = 2
    SMP_CANCEL_BOTH = 3
    SMP_DISABLED = 4


# ---------------------------------------------------------------------------
# DTO / Value Objects
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class NewOrderRequest:
    """Request DTO to place a new order."""

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


@dataclasses.dataclass(frozen=True)
class CancelOrderRequest:
    """Request DTO to cancel an existing order."""

    sequence_no: int
    timestamp_ns: int
    order_id: int
    client_order_id: str
    symbol: str


@dataclasses.dataclass(frozen=True)
class ReplaceOrderRequest:
    """Request DTO to replace price or quantity of an existing order."""

    sequence_no: int
    timestamp_ns: int
    original_order_id: int
    new_order_id: int
    client_order_id: str
    symbol: str
    new_price: int
    new_quantity: int


@dataclasses.dataclass(frozen=True)
class SessionTransition:
    """Control message for triggering exchange state transition."""

    sequence_no: int
    timestamp_ns: int
    symbol: str
    from_state: SessionState
    to_state: SessionState


# ---------------------------------------------------------------------------
# Scenario Models & Configs
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class SymbolConfig:
    """Configuration settings for a single trading symbol/instrument."""

    name: str
    tickSize: int
    lotSize: int
    maxOrderQty: int
    matchingAlgorithm: MatchingAlgorithm
    smpMode: SmpMode
    priceBandLower: int
    priceBandUpper: int


class Phase(ABC):
    """Abstract base class representing a phase in a simulation scenario."""

    pass


@dataclasses.dataclass(frozen=True)
class SessionTransitionPhase(Phase):
    """Scenario phase defined by an explicit session state transition."""

    atSeconds: int
    fromState: SessionState
    toState: SessionState


@dataclasses.dataclass(frozen=True)
class TrafficPhase(Phase):
    """Scenario phase generating market traffic under specified parameters."""

    fromSeconds: int
    toSeconds: int
    profile: str
    rate: int
    cancelRatio: float
    marketOrderRatio: float
    priceModel: str
    volatility: float
    magnitude: float


@dataclasses.dataclass(frozen=True)
class Scenario:
    """Top-level scenario container for simulating test loads."""

    name: str
    version: int
    seed: int
    durationSeconds: int
    symbols: List[SymbolConfig]
    phases: List[Phase]


@dataclasses.dataclass(frozen=True)
class ScenarioError:
    """Data class capturing validation errors during scenario parsing."""

    field: str
    message: str
