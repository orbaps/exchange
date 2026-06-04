from __future__ import annotations

from typing import List, Dict, Optional
from reference_engine.models import (
    Order, InstrumentDefinition, SessionState, BookSnapshot,
    NewOrderRequest, CancelOrderRequest, ReplaceOrderRequest,
    SessionTransition, ExecutionReport, RejectReason, Fill,
    ExecType, Side
)
from reference_engine.price_level import PriceLevelImpl
from reference_engine.matching import MatcherStrategy
from reference_engine.smp import SmpHandler
from reference_engine.stop import StopOrderRegistry

# ---
# Order Book class representing per-symbol state
# ---

class OrderBook:
    """Manages the full limit order book, session state, and order lifecycle for a single symbol."""

    def __init__(
        self,
        symbol: str,
        instrument: InstrumentDefinition,
        matcher: MatcherStrategy,
        smp_handler: SmpHandler,
        stop_orders: StopOrderRegistry,
    ) -> None:
        """Initializes the OrderBook with symbol, configuration, and helpers."""
        from reference_engine.order_manager import OrderManager
        from reference_engine.trade_manager import TradeManager
        
        self._symbol = symbol
        self._instrument = instrument
        self._matcher = matcher
        self._smp_handler = smp_handler
        self._stop_orders = stop_orders
        
        self._bids: Dict[int, PriceLevelImpl] = {}
        self._asks: Dict[int, PriceLevelImpl] = {}
        
        self._order_manager = OrderManager()
        self._trade_manager = TradeManager()
        
        self._session_state = SessionState.CLOSED
        self._last_trade_price = 0

    @property
    def symbol(self) -> str:
        """Returns the symbol associated with this order book."""
        return self._symbol

    @property
    def instrument(self) -> InstrumentDefinition:
        """Returns the instrument definition/configuration."""
        return self._instrument

    @property
    def bids(self) -> Dict[int, PriceLevelImpl]:
        """Returns active buy levels sorted descending by price."""
        # Standard dict sorted keys descending
        return {price: self._bids[price] for price in sorted(self._bids.keys(), reverse=True)}

    @property
    def asks(self) -> Dict[int, PriceLevelImpl]:
        """Returns active sell levels sorted ascending by price."""
        return {price: self._asks[price] for price in sorted(self._asks.keys())}

    @property
    def order_index(self) -> Dict[int, Order]:
        """Returns direct lookup map of active/registered order IDs to Order objects."""
        return self._order_manager._orders

    @property
    def client_order_id_index(self) -> Dict[str, int]:
        """Returns mapping of active client order IDs to system order IDs."""
        return self._order_manager._client_order_id_index

    @property
    def session_state(self) -> SessionState:
        """Returns the current session state of the instrument's book."""
        return self._session_state

    @property
    def last_trade_price(self) -> int:
        """Returns the price of the last execution/trade on this symbol."""
        return self._last_trade_price

    def process_new_order(self, request: NewOrderRequest) -> List[ExecutionReport]:
        """Validates, routes, and processes a NewOrderRequest, executing matches or booking it."""
        reject = self.validate_order(request)
        if reject:
            report = ExecutionReport(
                sequence_no=request.sequence_no,
                timestamp_ns=request.timestamp_ns,
                execution_id=0, # or generated
                order_id=request.order_id,
                client_order_id=request.client_order_id,
                symbol=self._symbol,
                side=request.side,
                exec_type=ExecType.REJECTED,
                last_price=0,
                last_qty=0,
                leaves_qty=0,
                cumulative_qty=0,
                original_qty=request.quantity,
                reject_reason=reject,
                match_order_id=0,
            )
            return [report]

        order = Order(
            order_id=request.order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            price=request.price,
            original_qty=request.quantity,
            tif=request.tif,
            party_id=request.party_id,
            sequence_no=request.sequence_no,
            stop_price=request.stop_price if hasattr(request, 'stop_price') else None,
        )

        reports = []
        new_report = ExecutionReport(
            sequence_no=request.sequence_no,
            timestamp_ns=request.timestamp_ns,
            execution_id=request.sequence_no,
            order_id=order.order_id,
            client_order_id=order.client_order_id,
            symbol=self._symbol,
            side=order.side,
            exec_type=ExecType.NEW,
            last_price=0,
            last_qty=0,
            leaves_qty=order.leaves_qty,
            cumulative_qty=0,
            original_qty=order.original_qty,
            reject_reason=RejectReason.REJECT_REASON_UNSPECIFIED,
            match_order_id=0,
        )
        reports.append(new_report)

        fills, maker_reports = self.match_aggressive_order(order, request.sequence_no, request.timestamp_ns)
            
        reports.extend(maker_reports)

        if order.leaves_qty > 0:
            from reference_engine.models import OrderType
            if order.order_type == OrderType.LIMIT:
                self.book_order(order)
            elif order.order_type == OrderType.MARKET:
                expire_report = order.expire(
                    execution_id=request.sequence_no,
                    sequence_no=request.sequence_no,
                    timestamp_ns=request.timestamp_ns
                )
                reports.append(expire_report)
                self._order_manager.remove_terminal_orders()

        return reports

    def process_cancel_order(self, request: CancelOrderRequest) -> ExecutionReport:
        """Processes a CancelOrderRequest, removing the order if valid and active."""
        order = self._order_manager.get_order(request.order_id)
        report = self._order_manager.cancel_order(request)
        
        if order and order.is_terminal():
            # Remove from depth
            side_depth = self._bids if order.side == Side.BUY else self._asks
            level = side_depth.get(order.price)
            if level:
                level.remove_order(order.order_id)
                if level.is_empty():
                    side_depth.pop(order.price)
                    
            self._order_manager.remove_terminal_orders()
            
        return report

    def process_replace_order(self, request: ReplaceOrderRequest) -> List[ExecutionReport]:
        """Processes a ReplaceOrderRequest, canceling the old order and inserting the new one."""
        raise NotImplementedError

    def process_session_transition(self, transition: SessionTransition) -> List[ExecutionReport]:
        """Handles session transitions, executing auctions or clearing state as necessary."""
        self._session_state = transition.to_state
        return []

    def get_snapshot(self, sequence_no: int, timestamp_ns: int) -> BookSnapshot:
        """Generates a BookSnapshot containing the current bids/asks depth."""
        from reference_engine.models import PriceLevel as RefPriceLevel
        bid_levels = [
            RefPriceLevel(price=lvl.price, quantity=lvl.total_quantity, order_count=lvl.order_count)
            for lvl in self.bids.values()
        ]
        ask_levels = [
            RefPriceLevel(price=lvl.price, quantity=lvl.total_quantity, order_count=lvl.order_count)
            for lvl in self.asks.values()
        ]
        return BookSnapshot(
            sequence_no=sequence_no,
            timestamp_ns=timestamp_ns,
            symbol=self._symbol,
            bids=bid_levels,
            asks=ask_levels,
        )

    def validate_order(self, request: NewOrderRequest) -> Optional[RejectReason]:
        """Validates incoming orders against price ticks, lot alignment, price bands, and session rules."""
        if self._session_state == SessionState.CLOSED:
            return RejectReason.SESSION_NOT_ACCEPTING
        if not self._instrument.is_tick_aligned(request.price) and request.price != 0:
            return RejectReason.INVALID_PRICE
        if not self._instrument.is_lot_aligned(request.quantity):
            return RejectReason.INVALID_QUANTITY
        if not self._instrument.is_within_bands(request.price) and request.price != 0:
            return RejectReason.INVALID_PRICE
        if self._order_manager.has_client_order_id(request.client_order_id):
            return RejectReason.DUPLICATE_CLIENT_ORDER_ID
        return None

    def book_order(self, order: Order) -> None:
        """Places a resting order onto the bids or asks depth and indexes it."""
        self._order_manager.add_order(order)

        side_depth = self._bids if order.side == Side.BUY else self._asks
        if order.price not in side_depth:
            side_depth[order.price] = PriceLevelImpl(order.price)
        side_depth[order.price].add_order(order)

    def match_aggressive_order(self, order: Order, sequence_no: int, timestamp_ns: int) -> tuple[List[Fill], List[ExecutionReport]]:
        """Matches an incoming aggressive order against the opposite book side using the configured matcher."""
        fills = []
        reports = []
        
        # Use the sorted property for iterating but modify the underlying dicts
        opposite_depth = self.asks if order.side == Side.BUY else self.bids
        opposite_dict = self._asks if order.side == Side.BUY else self._bids
        
        for price, level in opposite_depth.items():
            if order.leaves_qty == 0:
                break
                
            if order.price > 0: # Limit order
                if order.side == Side.BUY and price > order.price:
                    break
                if order.side == Side.SELL and price < order.price:
                    break
                    
            level_fills = self._matcher.match(order, level)
            for fill in level_fills:
                # Maker report
                maker_order = self._order_manager.get_order(fill.maker_order_id)
                maker_report = maker_order.fill(
                    qty=fill.quantity,
                    fill_price=fill.price,
                    execution_id=sequence_no,
                    sequence_no=sequence_no,
                    timestamp_ns=timestamp_ns
                )
                maker_report.match_order_id = order.order_id
                reports.append(maker_report)
                
                # Taker report
                taker_report = order.fill(
                    qty=fill.quantity,
                    fill_price=fill.price,
                    execution_id=sequence_no,
                    sequence_no=sequence_no,
                    timestamp_ns=timestamp_ns
                )
                taker_report.match_order_id = fill.maker_order_id
                reports.append(taker_report)
                
                # Record trade
                self._trade_manager.add_trade(
                    symbol=self._symbol,
                    price=fill.price,
                    quantity=fill.quantity,
                    buyer_id=order.order_id if order.side == Side.BUY else maker_order.order_id,
                    seller_id=order.order_id if order.side == Side.SELL else maker_order.order_id
                )
                
                # Update last trade price
                self._last_trade_price = fill.price
                
                if maker_order.is_terminal():
                    level.remove_order(maker_order.order_id)
                    self._order_manager.remove_terminal_orders()
            
            fills.extend(level_fills)
            
            if level.is_empty():
                opposite_dict.pop(price)
                
        return fills, reports

    def execute_uncrossing_auction(self) -> List[ExecutionReport]:
        """Triggers the uncrossing auction calculation and applies fills for crossing orders."""
        raise NotImplementedError

    def expire_gfd_orders(self) -> List[ExecutionReport]:
        """Expires GFD (Good For Day) orders from the book, returning execution reports."""
        raise NotImplementedError

    def reload_gtc_orders(self) -> None:
        """Restores GTC orders at session startup."""
        raise NotImplementedError

    def check_and_trigger_stops(self, trade_price: int) -> List[ExecutionReport]:
        """Checks for stop order triggers and transitions triggered stop orders into limit orders."""
        raise NotImplementedError

    def check_price_bands(self, price: int) -> bool:
        """Verifies if a price is within current dynamic or static bands."""
        raise NotImplementedError

