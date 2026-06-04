from typing import Dict, Any, List
from benchmarking.contestant_adapter import ContestantEngine
from reference_engine.engine import MatchingEngine
from reference_engine.models import (
    InstrumentDefinition, MatchingAlgorithm, SmpMode, Side, OrderType, TimeInForce,
    NewOrderRequest, CancelOrderRequest, ReplaceOrderRequest
)
from validation_engine.snapshots import EngineSnapshot, BookSnapshot, OrderSnapshot, TradeSnapshot

class ReferenceEngineAdapter(ContestantEngine):
    """Wraps the Reference Engine to fulfill the ContestantEngine interface."""

    def __init__(self, instruments: List[InstrumentDefinition] = None):
        self._instruments = instruments or [
            InstrumentDefinition(
                symbol="TEST",
                tick_size=1,
                lot_size=1,
                max_order_qty=10000,
                price_band_lower=1,
                price_band_upper=100000,
                matching_algorithm=MatchingAlgorithm.PRICE_TIME_FIFO,
                smp_mode=SmpMode.SMP_DISABLED,
                prorata_threshold=0
            )
        ]
        self._engine = MatchingEngine(self._instruments)
        # In a real environment, we would inject a SessionTransition before accepting orders.
        # For benchmarking, we assume the engine is always in CONTINUOUS state.
        from reference_engine.models import SessionState
        for symbol, book in self._engine._books.items():
            book._session_state = SessionState.CONTINUOUS

    def submit_order(self, payload: Dict[str, Any]) -> None:
        req = NewOrderRequest(
            sequence_no=payload['sequence_no'],
            timestamp_ns=payload['timestamp_ns'],
            order_id=payload['order_id'],
            client_order_id=payload['client_order_id'],
            symbol=payload['symbol'],
            side=Side[payload['side']],
            order_type=OrderType[payload['order_type']],
            price=payload['price'],
            quantity=payload['quantity'],
            tif=TimeInForce[payload['tif']],
            party_id=payload['party_id'],
            stop_price=payload.get('stop_price')
        )
        self._engine.on_message(req)

    def cancel_order(self, payload: Dict[str, Any]) -> None:
        req = CancelOrderRequest(
            sequence_no=payload['sequence_no'],
            timestamp_ns=payload['timestamp_ns'],
            order_id=payload['order_id'],
            client_order_id=payload['client_order_id'],
            symbol=payload['symbol']
        )
        self._engine.on_message(req)

    def replace_order(self, payload: Dict[str, Any]) -> None:
        req = ReplaceOrderRequest(
            sequence_no=payload['sequence_no'],
            timestamp_ns=payload['timestamp_ns'],
            original_order_id=payload['original_order_id'],
            new_order_id=payload['new_order_id'],
            client_order_id=payload['client_order_id'],
            symbol=payload['symbol'],
            new_price=payload['new_price'],
            new_quantity=payload['new_quantity']
        )
        self._engine.on_message(req)

    def snapshot(self) -> EngineSnapshot:
        """Takes a full snapshot of the engine state, independent of the GroundTruthGenerator."""
        book_snapshots = {}
        order_snapshots = {}
        trade_snapshots = {}
        
        # We can extract the timestamp from the current state if needed, but for validation
        # the exact timestamp on the snapshot might not matter as much as the structural values.
        timestamp = 0
        
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

    def reset(self) -> None:
        from reference_engine.models import SessionState
        self._engine = MatchingEngine(self._instruments)
        for symbol, book in self._engine._books.items():
            book._session_state = SessionState.CONTINUOUS
