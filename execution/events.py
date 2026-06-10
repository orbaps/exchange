from dataclasses import dataclass
from typing import Optional
from botfleet.events import TradingEvent

@dataclass
class ExecutionEvent:
    event_id: str
    execution_sequence_id: int
    worker_id: str
    session_id: str
    dispatch_timestamp_ns: int
    completion_timestamp_ns: int
    success: bool
    error: Optional[str]
    trading_event: TradingEvent
