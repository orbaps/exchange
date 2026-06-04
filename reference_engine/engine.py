from __future__ import annotations

from typing import List, Dict, Union
from reference_engine.order_book import OrderBook
from reference_engine.models import (
    InstrumentDefinition, ExecutionReport,
    NewOrderRequest, CancelOrderRequest, ReplaceOrderRequest, SessionTransition
)

# ---
# Matching Engine Top-Level Router
# ---

class MatchingEngine:
    """Top-level router orchestrating multiple OrderBooks, sequencing outputs, and handling incoming messages."""

    def __init__(self, instruments: List[InstrumentDefinition]) -> None:
        """Initializes the MatchingEngine, setting up OrderBook instances for each instrument definition."""
        self._books: Dict[str, OrderBook] = {}
        self._next_output_seq_no = 1
        
        from reference_engine.matching import FifoMatcher
        from reference_engine.smp import SmpHandler
        from reference_engine.stop import StopOrderRegistry
        from reference_engine.models import MatchingAlgorithm
        
        for inst in instruments:
            # We currently only support FIFO matcher in Phase 2.2
            matcher = FifoMatcher()
            smp_handler = SmpHandler(inst.smp_mode)
            stop_registry = StopOrderRegistry()
            
            self._books[inst.symbol] = OrderBook(
                symbol=inst.symbol,
                instrument=inst,
                matcher=matcher,
                smp_handler=smp_handler,
                stop_orders=stop_registry
            )

    @property
    def books(self) -> Dict[str, OrderBook]:
        """Returns the dictionary mapping symbol to OrderBook."""
        return self._books

    @property
    def next_output_seq_no(self) -> int:
        """Returns the next sequence number to assign to output execution reports."""
        return self._next_output_seq_no

    def on_message(
        self,
        record: Union[NewOrderRequest, CancelOrderRequest, ReplaceOrderRequest, SessionTransition]
    ) -> List[ExecutionReport]:
        """Routes sequenced commands and control messages to the appropriate OrderBook and stamps outputs."""
        if isinstance(record, NewOrderRequest):
            reports = self.route_new_order(record)
        elif isinstance(record, CancelOrderRequest):
            reports = self.route_cancel(record)
        elif isinstance(record, ReplaceOrderRequest):
            reports = self.route_replace(record)
        elif isinstance(record, SessionTransition):
            reports = self.route_session_transition(record)
        else:
            raise ValueError("Unknown record type")
            
        # Stamp output seq no if needed, but our reports currently just carry sequence_no from requests
        # In a real engine, the output stream has its own sequence numbers. 
        # For reference engine, we just return the reports.
        return reports

    def get_book(self, symbol: str) -> OrderBook:
        """Looks up and returns the OrderBook for a given trading symbol."""
        if symbol not in self._books:
            raise ValueError(f"Unknown symbol: {symbol}")
        return self._books[symbol]

    def destroy(self) -> None:
        """Cleans up engine resources, closing files, flushing telemetry, or shutting down."""
        pass

    def route_new_order(self, request: NewOrderRequest) -> List[ExecutionReport]:
        """Routes a NewOrderRequest to the correct OrderBook."""
        try:
            book = self.get_book(request.symbol)
            return book.process_new_order(request)
        except ValueError:
            return []

    def route_cancel(self, request: CancelOrderRequest) -> List[ExecutionReport]:
        """Routes a CancelOrderRequest to the correct OrderBook."""
        try:
            book = self.get_book(request.symbol)
            report = book.process_cancel_order(request)
            return [report]
        except ValueError:
            return []

    def route_replace(self, request: ReplaceOrderRequest) -> List[ExecutionReport]:
        """Routes a ReplaceOrderRequest to the correct OrderBook."""
        try:
            book = self.get_book(request.symbol)
            return book.process_replace_order(request)
        except ValueError:
            return []

    def route_session_transition(self, transition: SessionTransition) -> List[ExecutionReport]:
        """Routes a SessionTransition request to the correct OrderBook."""
        try:
            book = self.get_book(transition.symbol)
            return book.process_session_transition(transition)
        except ValueError:
            return []

    def assign_output_sequence(self, report: ExecutionReport) -> None:
        """Stamps the outgoing ExecutionReport with the next output sequence number and increments it."""
        raise NotImplementedError
