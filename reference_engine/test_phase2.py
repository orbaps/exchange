from __future__ import annotations

import unittest
from contracts.domain import MatchingAlgorithm, SmpMode, Side, OrderType, TimeInForce, ExecType, RejectReason, OrderState
from contracts.instruments import InstrumentDefinition
from reference_engine.models import (
    InstrumentDefinition as RefInstrumentDefinition,
    Side,
    OrderType as RefOrderType,
    TimeInForce as RefTimeInForce,
    ExecType as RefExecType,
    RejectReason as RefRejectReason,
    OrderState as RefOrderState,
    MatchingAlgorithm as RefMatchingAlgorithm,
    SmpMode as RefSmpMode,
    Order,
    ExecutionReport,
    Fill,
    Trade,
    SessionTransition,
    NewOrderRequest,
    CancelOrderRequest,
    BookSnapshot,
    SessionState as RefSessionState
)
from reference_engine.price_level import PriceLevelImpl
from reference_engine.order_book import OrderBook

class TestInstrumentDefinition(unittest.TestCase):
    def test_validation_success(self) -> None:
        inst = InstrumentDefinition(
            symbol="BTC-USD",
            tick_size=100,
            lot_size=10,
            max_order_qty=10000,
            price_band_lower=90000,
            price_band_upper=110000,
            matching_algorithm=MatchingAlgorithm.PRICE_TIME_FIFO,
            smp_mode=SmpMode.SMP_CANCEL_NEWEST,
            prorata_threshold=500
        )
        self.assertEqual(inst.symbol, "BTC-USD")
        self.assertTrue(inst.isTickAligned(200))
        self.assertFalse(inst.isTickAligned(150))
        self.assertTrue(inst.isLotAligned(20))
        self.assertFalse(inst.isLotAligned(15))
        self.assertTrue(inst.isWithinBands(100000))
        self.assertFalse(inst.isWithinBands(80000))

    def test_validation_errors(self) -> None:
        with self.assertRaises(ValueError):
            InstrumentDefinition("BTC-USD", -5, 10, 10000, 90000, 110000, MatchingAlgorithm.PRICE_TIME_FIFO, SmpMode.SMP_CANCEL_NEWEST, 500)
        with self.assertRaises(TypeError):
            InstrumentDefinition("", 100, 10, 10000, 90000, 110000, MatchingAlgorithm.PRICE_TIME_FIFO, SmpMode.SMP_CANCEL_NEWEST, 500)

class TestRefInstrumentDefinition(unittest.TestCase):
    def test_validation_success(self) -> None:
        inst = RefInstrumentDefinition(
            symbol="BTC-USD",
            tick_size=100,
            lot_size=10,
            max_order_qty=10000,
            price_band_lower=90000,
            price_band_upper=110000,
            matching_algorithm=RefMatchingAlgorithm.PRICE_TIME_FIFO if 'RefMatchingAlgorithm' in globals() else MatchingAlgorithm.PRICE_TIME_FIFO, # handle mapping or direct import
            smp_mode=RefSmpMode.SMP_CANCEL_NEWEST if 'RefSmpMode' in globals() else SmpMode.SMP_CANCEL_NEWEST,
            prorata_threshold=500
        )
        self.assertEqual(inst.symbol, "BTC-USD")
        self.assertTrue(inst.is_tick_aligned(200))
        self.assertFalse(inst.is_tick_aligned(150))
        self.assertTrue(inst.is_lot_aligned(20))
        self.assertFalse(inst.is_lot_aligned(15))
        self.assertTrue(inst.is_within_bands(100000))
        self.assertFalse(inst.is_within_bands(80000))

class TestOrderLifecycle(unittest.TestCase):
    def test_order_creation_and_fill(self) -> None:
        order = Order(
            order_id=1,
            client_order_id="cl-1",
            symbol="BTC-USD",
            side=Side.BUY,
            order_type=RefOrderType.LIMIT,
            price=10000,
            original_qty=100,
            tif=RefTimeInForce.GFD,
            party_id="firm-A",
            sequence_no=10
        )
        self.assertEqual(order.leaves_qty, 100)
        self.assertEqual(order.cumulative_qty, 0)
        self.assertEqual(order.state, RefOrderState.NEW)
        self.assertTrue(order.is_active())
        self.assertFalse(order.is_terminal())

        # Test partial fill
        report = order.fill(qty=40, fill_price=10000, execution_id=101, sequence_no=11, timestamp_ns=1000000)
        self.assertEqual(order.leaves_qty, 60)
        self.assertEqual(order.cumulative_qty, 40)
        self.assertEqual(order.state, RefOrderState.PARTIALLY_FILLED)
        self.assertEqual(report.exec_type, RefExecType.PARTIALLY_FILLED)
        self.assertEqual(report.last_qty, 40)
        self.assertEqual(report.leaves_qty, 60)
        self.assertEqual(report.cumulative_qty, 40)

        # Test complete fill
        report2 = order.fill(qty=60, fill_price=10000, execution_id=102, sequence_no=12, timestamp_ns=2000000)
        self.assertEqual(order.leaves_qty, 0)
        self.assertEqual(order.cumulative_qty, 100)
        self.assertEqual(order.state, RefOrderState.FILLED)
        self.assertEqual(report2.exec_type, RefExecType.FILLED)
        self.assertTrue(order.is_terminal())
        self.assertFalse(order.is_active())

    def test_order_cancel(self) -> None:
        order = Order(
            order_id=2,
            client_order_id="cl-2",
            symbol="BTC-USD",
            side=Side.SELL,
            order_type=RefOrderType.LIMIT,
            price=10100,
            original_qty=50,
            tif=RefTimeInForce.GTC,
            party_id="firm-B",
            sequence_no=20
        )
        report = order.cancel(execution_id=103, sequence_no=21, timestamp_ns=3000000)
        self.assertEqual(order.leaves_qty, 0)
        self.assertEqual(order.canceled_qty, 50)
        self.assertEqual(order.state, RefOrderState.CANCELED)
        self.assertEqual(report.exec_type, RefExecType.CANCELED)
        self.assertTrue(order.is_terminal())

    def test_order_replace(self) -> None:
        order = Order(
            order_id=3,
            client_order_id="cl-3",
            symbol="BTC-USD",
            side=Side.BUY,
            order_type=RefOrderType.LIMIT,
            price=10000,
            original_qty=100,
            tif=RefTimeInForce.GFD,
            party_id="firm-A",
            sequence_no=30
        )
        report = order.replace(new_price=10050, new_qty=120, new_order_id=4, execution_id=104, sequence_no=31, timestamp_ns=4000000)
        self.assertEqual(order.state, RefOrderState.REPLACED)
        self.assertEqual(report.exec_type, RefExecType.REPLACED)
        self.assertEqual(report.last_price, 10050)
        self.assertEqual(report.last_qty, 120)

class TestPriceLevel(unittest.TestCase):
    def test_fifo_ordering(self) -> None:
        lvl = PriceLevelImpl(price=10000)
        self.assertEqual(lvl.price, 10000)
        self.assertTrue(lvl.is_empty())

        order1 = Order(1, "cl-1", "BTC-USD", Side.BUY, RefOrderType.LIMIT, 10000, 10, RefTimeInForce.GTC, "A", 1)
        order2 = Order(2, "cl-2", "BTC-USD", Side.BUY, RefOrderType.LIMIT, 10000, 20, RefTimeInForce.GTC, "B", 2)

        lvl.add_order(order1)
        lvl.add_order(order2)
        self.assertEqual(lvl.order_count, 2)
        self.assertEqual(lvl.total_quantity, 30)
        self.assertEqual(lvl.front().order_id, 1)

        # Iterate and assert FIFO ordering
        orders = list(lvl)
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].order_id, 1)
        self.assertEqual(orders[1].order_id, 2)

        removed = lvl.remove_order(1)
        self.assertEqual(removed.order_id, 1)
        self.assertEqual(lvl.order_count, 1)
        self.assertEqual(lvl.front().order_id, 2)

class TestOrderBook(unittest.TestCase):
    def test_book_sorting_and_snapshot(self) -> None:
        from reference_engine.matching import FifoMatcher
        from reference_engine.smp import SmpHandler
        from reference_engine.stop import StopOrderRegistry

        inst = RefInstrumentDefinition("BTC-USD", 100, 10, 10000, 90000, 110000, RefMatchingAlgorithm.PRICE_TIME_FIFO, RefSmpMode.SMP_DISABLED, 0)
        book = OrderBook("BTC-USD", inst, FifoMatcher(), SmpHandler(RefSmpMode.SMP_DISABLED), StopOrderRegistry())

        # Transition to pre-open/continuous so we accept orders
        book.process_session_transition(SessionTransition(1, 1000, "BTC-USD", RefSessionState.CLOSED, RefSessionState.CONTINUOUS))

        # Add BUY orders at different prices to test descending sorting
        book.process_new_order(NewOrderRequest(2, 2000, 10, "cl-1", "BTC-USD", Side.BUY, RefOrderType.LIMIT, 100000, 10, RefTimeInForce.GTC, "A"))
        book.process_new_order(NewOrderRequest(3, 3000, 11, "cl-2", "BTC-USD", Side.BUY, RefOrderType.LIMIT, 100100, 20, RefTimeInForce.GTC, "A"))

        # Add SELL orders to test ascending sorting
        book.process_new_order(NewOrderRequest(4, 4000, 12, "cl-3", "BTC-USD", Side.SELL, RefOrderType.LIMIT, 100500, 50, RefTimeInForce.GTC, "B"))
        book.process_new_order(NewOrderRequest(5, 5000, 13, "cl-4", "BTC-USD", Side.SELL, RefOrderType.LIMIT, 100400, 30, RefTimeInForce.GTC, "B"))

        # Check bids descending
        bids = list(book.bids.keys())
        self.assertEqual(bids, [100100, 100000])

        # Check asks ascending
        asks = list(book.asks.keys())
        self.assertEqual(asks, [100400, 100500])

        # Generate snapshot
        snap = book.get_snapshot(6, 6000)
        self.assertEqual(snap.symbol, "BTC-USD")
        self.assertEqual(len(snap.bids), 2)
        self.assertEqual(snap.bids[0].price, 100100)
        self.assertEqual(snap.bids[0].quantity, 20)

    def test_matching_scenarios(self) -> None:
        from reference_engine.matching import FifoMatcher
        from reference_engine.smp import SmpHandler
        from reference_engine.stop import StopOrderRegistry

        inst = RefInstrumentDefinition("BTC-USD", 100, 10, 10000, 90000, 110000, RefMatchingAlgorithm.PRICE_TIME_FIFO, RefSmpMode.SMP_DISABLED, 0)
        book = OrderBook("BTC-USD", inst, FifoMatcher(), SmpHandler(RefSmpMode.SMP_DISABLED), StopOrderRegistry())

        # Transition to pre-open/continuous so we accept orders
        book.process_session_transition(SessionTransition(1, 1000, "BTC-USD", RefSessionState.CLOSED, RefSessionState.CONTINUOUS))

        # 1. Add resting SELL orders at different levels (multi-level matching)
        book.process_new_order(NewOrderRequest(2, 2000, 10, "cl-1", "BTC-USD", Side.SELL, RefOrderType.LIMIT, 100400, 30, RefTimeInForce.GTC, "B"))
        book.process_new_order(NewOrderRequest(3, 3000, 11, "cl-2", "BTC-USD", Side.SELL, RefOrderType.LIMIT, 100400, 20, RefTimeInForce.GTC, "C"))
        book.process_new_order(NewOrderRequest(4, 4000, 12, "cl-3", "BTC-USD", Side.SELL, RefOrderType.LIMIT, 100500, 50, RefTimeInForce.GTC, "D"))

        # 2. Add incoming BUY Limit order that crosses multiple levels and partially fills the last one
        reports = book.process_new_order(NewOrderRequest(5, 5000, 13, "cl-match", "BTC-USD", Side.BUY, RefOrderType.LIMIT, 100500, 60, RefTimeInForce.GTC, "A"))
        
        # Expect NEW report + 3 Fills (2 full for 100400, 1 partial for 100500)
        # 1 NEW (BUY)
        # 1 FILL (SELL maker order 10)
        # 1 FILL (BUY taker partial)
        # 1 FILL (SELL maker order 11)
        # 1 FILL (BUY taker partial)
        # 1 FILL (SELL maker order 12)
        # 1 FILL (BUY taker partial/full)
        
        # Check that we got reports
        self.assertTrue(len(reports) > 0)
        new_report = reports[0]
        self.assertEqual(new_report.exec_type, RefExecType.NEW)
        
        # Check order index state
        self.assertTrue(12 in book.order_index) # order 12 should be partially filled
        self.assertFalse(10 in book.order_index) # fully filled
        self.assertFalse(11 in book.order_index) # fully filled
        
        # Order 13 (BUY) should be fully filled and NOT on book
        self.assertFalse(13 in book.order_index)
        
        # Remaining asks: 100500 with qty 50 - (60 - 30 - 20) = 50 - 10 = 40
        self.assertEqual(len(book.asks), 1)
        self.assertEqual(book.asks[100500].total_quantity, 40)
        
        # 3. Add Market Order BUY
        market_reports = book.process_new_order(NewOrderRequest(6, 6000, 14, "cl-mkt", "BTC-USD", Side.BUY, RefOrderType.MARKET, 0, 50, RefTimeInForce.IOC, "A"))
        
        # Should fill 40 from 100500 and then expire the remaining 10
        self.assertEqual(len(book.asks), 0)
        self.assertFalse(12 in book.order_index)
        
        expire_reports = [r for r in market_reports if r.exec_type == RefExecType.EXPIRED]
        self.assertEqual(len(expire_reports), 1)
        self.assertEqual(expire_reports[0].leaves_qty, 0)
        self.assertEqual(expire_reports[0].last_qty, 0) # expire report has last_qty 0 usually, wait, order.expire sets to 0
        self.assertEqual(expire_reports[0].original_qty, 50)
        # Wait, the expire report should reflect the canceled quantity, which is 10.
        # leaves_qty on EXPIRED is 0. cumulative_qty is 40.
        self.assertEqual(expire_reports[0].cumulative_qty, 40)
        
if __name__ == "__main__":
    unittest.main()
