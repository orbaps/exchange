from dataclasses import dataclass
from typing import Optional
from botfleet.events import TradingEvent

@dataclass
class ExecutionRequest:
    """Standardized request to execute a trading event against a contestant session."""
    session_id: str
    trading_event: TradingEvent

@dataclass
class ExecutionResponse:
    """Standardized response from an execution session."""
    success: bool
    latency_ns: int
    error: Optional[str] = None
