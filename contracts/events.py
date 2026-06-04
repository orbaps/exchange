from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from contracts.messages import (
    NewOrderRequest,
    CancelOrderRequest,
    ReplaceOrderRequest,
    SessionTransition,
    ExecutionReport,
    BookSnapshot,
)

# ---
# Event envelope for sequencing, replay, and system journal logging
# ---

@dataclass
class JournalRecord:
    """Represents a journal event envelope wrapping inbound and outbound payloads.

    Matches exchange.events.JournalRecord protobuf schema.
    """
    global_sequence_no: int
    logical_timestamp: int
    wall_clock_ns: int
    run_id: str
    new_order: Optional[NewOrderRequest] = None
    cancel_order: Optional[CancelOrderRequest] = None
    replace_order: Optional[ReplaceOrderRequest] = None
    session_change: Optional[SessionTransition] = None
    exec_report: Optional[ExecutionReport] = None
    book_snapshot: Optional[BookSnapshot] = None
