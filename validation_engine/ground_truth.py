from dataclasses import dataclass
from typing import List, Dict, Optional
from validation_engine.snapshots import BookSnapshot, OrderSnapshot, TradeSnapshot, EngineSnapshot
from reference_engine.engine import MatchingEngine
from reference_engine.models import ExecutionReport, ExecType
from reference_engine.events import EventBus

@dataclass
class ValidationRecord:
    """Represents the canonical expected state after an event."""
    event_id: int
    expected_book_state: EngineSnapshot
    expected_order_state: EngineSnapshot
    expected_trade_state: EngineSnapshot


class GroundTruthGenerator:
    """Passively listens to engine events and generates canonical state snapshots."""
    
    def __init__(self, engine: MatchingEngine, event_bus: EventBus) -> None:
        """Initializes the GroundTruthGenerator and hooks into the event bus."""
        self._engine = engine
        self._event_bus = event_bus
        self._records: List[ValidationRecord] = []
        
        # Hook into ExecutionReports to generate snapshots
        self._event_bus.subscribe(ExecutionReport, self._on_execution_report)
        
    def _generate_engine_snapshot(self, timestamp: int) -> EngineSnapshot:
        """Takes a full snapshot of the engine state."""
        book_snapshots = {}
        order_snapshots = {}
        trade_snapshots = {}
        
        for symbol, book in self._engine._books.items():
            # Book Snapshot
            best_bid = 0
            bid_depth = 0
            if book.bids:
                best_bid = max(book.bids.keys())
                bid_depth = sum(lvl.total_quantity for lvl in book.bids.values())
                
            best_ask = 0
            ask_depth = 0
            if book.asks:
                best_ask = min(book.asks.keys())
                ask_depth = sum(lvl.total_quantity for lvl in book.asks.values())
                
            spread = best_ask - best_bid if best_ask > 0 and best_bid > 0 else 0
            
            book_snapshots[symbol] = BookSnapshot(
                instrument=symbol,
                best_bid=best_bid,
                best_ask=best_ask,
                spread=spread,
                bid_depth=bid_depth,
                ask_depth=ask_depth,
                timestamp=timestamp
            )
            
            # Order Snapshots
            order_snapshots[symbol] = {}
            for order_id, order in book.order_index.items():
                order_snapshots[symbol][order_id] = OrderSnapshot(
                    order_id=order.order_id,
                    status=order.state.name,
                    remaining_quantity=order.leaves_qty,
                    filled_quantity=order.cumulative_qty
                )
                
            # Trade Snapshots
            trade_snapshots[symbol] = []
            for trade in book._trade_manager.get_trades():
                trade_snapshots[symbol].append(TradeSnapshot(
                    trade_id=trade.match_id,
                    price=trade.price,
                    quantity=trade.quantity
                ))
                
        return EngineSnapshot(
            book_snapshots=book_snapshots,
            order_snapshots=order_snapshots,
            trade_snapshots=trade_snapshots
        )

    def _on_execution_report(self, report: ExecutionReport) -> None:
        """Triggered on every execution report to capture a checkpoint validation record."""
        # We capture a snapshot for every state change
        snapshot = self._generate_engine_snapshot(report.timestamp_ns)
        
        # We use the same snapshot for all three as it contains all data
        record = ValidationRecord(
            event_id=report.sequence_no,
            expected_book_state=snapshot,
            expected_order_state=snapshot,
            expected_trade_state=snapshot
        )
        self._records.append(record)

    @property
    def records(self) -> List[ValidationRecord]:
        return self._records
