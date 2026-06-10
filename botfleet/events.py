from dataclasses import dataclass
from enum import Enum
from typing import Optional

class EventType(Enum):
    NEW_ORDER = "NEW_ORDER"
    CANCEL = "CANCEL"
    REPLACE = "REPLACE"
    MARKET_ORDER = "MARKET_ORDER"

@dataclass
class TradingEvent:
    event_id: str
    timestamp_ns: int
    bot_id: str
    instrument: str
    event_type: EventType
    quantity: int
    price: int
    side: str  # "BUY" or "SELL"
    order_id: Optional[str] = None  # Needed for cancel/replace
