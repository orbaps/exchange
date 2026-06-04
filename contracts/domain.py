from __future__ import annotations

import enum

# ---
# Domain Enumerations mirroring the exchange.domain protobuf structures.
# These define the core states, types, and reasons used throughout the matching process.
# ---

class Side(enum.IntEnum):
    """Represents the side of an order (buy or sell)."""
    SIDE_UNSPECIFIED = 0
    BUY = 1
    SELL = 2


class OrderType(enum.IntEnum):
    """Represents the classification of order execution logic."""
    ORDER_TYPE_UNSPECIFIED = 0
    LIMIT = 1
    MARKET = 2
    STOP_LIMIT = 3


class TimeInForce(enum.IntEnum):
    """Governs the lifecycle and expiry conditions of an order."""
    TIF_UNSPECIFIED = 0
    GFD = 1   # Good for Day
    GTC = 2   # Good till Cancel
    IOC = 3   # Immediate or Cancel
    FOK = 4   # Fill or Kill


class ExecType(enum.IntEnum):
    """Represents the specific event type for an Execution Report."""
    EXEC_TYPE_UNSPECIFIED = 0
    NEW = 1
    REJECTED = 2
    PARTIALLY_FILLED = 3
    FILLED = 4
    CANCELED = 5
    EXPIRED = 6
    REPLACED = 7
    SMP_CANCELED = 8


class RejectReason(enum.IntEnum):
    """The reason why an order request was rejected by the engine."""
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


class SessionState(enum.IntEnum):
    """States representing the lifecycle of the exchange session."""
    SESSION_STATE_UNSPECIFIED = 0
    CLOSED = 1
    PRE_OPEN = 2
    NO_CANCEL = 3
    CONTINUOUS = 4
    HALTED = 5
    PRE_CLOSE = 6
    MAINTENANCE = 7


class MatchingAlgorithm(enum.IntEnum):
    """The priority rules used for matching matching orders."""
    MATCHING_ALGORITHM_UNSPECIFIED = 0
    PRICE_TIME_FIFO = 1
    PRICE_TIME_PRORATA = 2
    THRESHOLD_PRORATA = 3


class SmpMode(enum.IntEnum):
    """Self-Match Prevention behavior when matching identical party IDs."""
    SMP_MODE_UNSPECIFIED = 0
    SMP_CANCEL_NEWEST = 1
    SMP_CANCEL_OLDEST = 2
    SMP_CANCEL_BOTH = 3
    SMP_DISABLED = 4


class OrderState(enum.IntEnum):
    """Internal engine states for tracking order lifecycles."""
    PENDING_NEW = 0
    NEW = 1
    PARTIALLY_FILLED = 2
    FILLED = 3
    CANCELED = 4
    EXPIRED = 5
    REPLACED = 6
    REJECTED = 7
    SMP_CANCELED = 8
