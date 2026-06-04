from dataclasses import dataclass
from typing import List, Dict, Any
from reference_engine.models import (
    NewOrderRequest, CancelOrderRequest, ReplaceOrderRequest,
    SessionTransition, ExecutionReport, Order, Trade, OrderType, Side, TimeInForce, SessionState
)
from reference_engine.engine import MatchingEngine
from reference_engine.order_book import OrderBook
from sequencer.journal import JournalRecord

@dataclass
class ReplayResult:
    """Encapsulates the final reconstructed state of the engine after replay."""
    orders: Dict[str, Dict[int, Order]]
    trades: Dict[str, List[Trade]]
    orderbooks: Dict[str, OrderBook]
    events: List[ExecutionReport]


class ReplayEngine:
    """Deterministically reconstructs engine state from a sequence of journal records."""
    
    def __init__(self, target_engine: MatchingEngine) -> None:
        """Initializes the ReplayEngine with a virgin target MatchingEngine."""
        self.engine = target_engine
        
    def _parse_payload(self, event_type: str, payload: dict) -> Any:
        """Helper to convert JSON dictionary payload back to a dataclass object."""
        if event_type == "NewOrderRequest":
            # Map enum string representations back to enums if needed
            return NewOrderRequest(
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
        elif event_type == "CancelOrderRequest":
            return CancelOrderRequest(
                sequence_no=payload['sequence_no'],
                timestamp_ns=payload['timestamp_ns'],
                order_id=payload['order_id'],
                client_order_id=payload['client_order_id'],
                symbol=payload['symbol']
            )
        elif event_type == "ReplaceOrderRequest":
            return ReplaceOrderRequest(
                sequence_no=payload['sequence_no'],
                timestamp_ns=payload['timestamp_ns'],
                original_order_id=payload['original_order_id'],
                new_order_id=payload['new_order_id'],
                client_order_id=payload['client_order_id'],
                symbol=payload['symbol'],
                new_price=payload['new_price'],
                new_quantity=payload['new_quantity']
            )
        elif event_type == "SessionTransition":
            return SessionTransition(
                sequence_no=payload['sequence_no'],
                timestamp_ns=payload['timestamp_ns'],
                symbol=payload['symbol'],
                from_state=SessionState[payload['from_state']],
                to_state=SessionState[payload['to_state']]
            )
        return None

    def replay(self, records: List[JournalRecord]) -> ReplayResult:
        """
        Replays all records sequentially into the engine.
        Returns a ReplayResult containing the reconstructed state.
        """
        emitted_events: List[ExecutionReport] = []
        
        for record in records:
            if not record.verify_checksum():
                raise ValueError(f"Checksum verification failed for record {record.record_id}")
                
            request_obj = self._parse_payload(record.event_type, record.payload)
            if request_obj:
                outputs = self.engine.on_message(request_obj)
                if outputs:
                    emitted_events.extend(outputs)
                    
        # Extract final state
        orders: Dict[str, Dict[int, Order]] = {}
        trades: Dict[str, List[Trade]] = {}
        orderbooks: Dict[str, OrderBook] = {}
        
        for symbol, book in self.engine._books.items():
            orderbooks[symbol] = book
            orders[symbol] = dict(book.order_index)
            trades[symbol] = list(book._trade_manager.get_trades())
            
        return ReplayResult(
            orders=orders,
            trades=trades,
            orderbooks=orderbooks,
            events=emitted_events
        )
