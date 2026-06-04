import unittest
from typing import List

from reference_engine.events import EventBus, ReplayLog
from reference_engine.engine import MatchingEngine
from reference_engine.models import (
    InstrumentDefinition, MatchingAlgorithm, SmpMode, Side, OrderType,
    TimeInForce, SessionState, NewOrderRequest, CancelOrderRequest,
    SessionTransition, ExecutionReport, ReplaceOrderRequest
)

class TestReplayEngine(unittest.TestCase):
    def setUp(self):
        # Create a basic instrument
        self.inst = InstrumentDefinition(
            symbol="ETH-USD",
            tick_size=10,
            lot_size=1,
            max_order_qty=1000,
            price_band_lower=1000,
            price_band_upper=50000,
            matching_algorithm=MatchingAlgorithm.PRICE_TIME_FIFO,
            smp_mode=SmpMode.SMP_DISABLED,
            prorata_threshold=0
        )
        
        # Engine A (live)
        self.engine_live = MatchingEngine([self.inst])
        
        # Engine B (replay)
        self.engine_replay = MatchingEngine([self.inst])
        
        self.bus = EventBus()
        self.log = ReplayLog()
        
        # Subscribe log to all incoming requests
        self.bus.subscribe(NewOrderRequest, self.log.append)
        self.bus.subscribe(CancelOrderRequest, self.log.append)
        self.bus.subscribe(ReplaceOrderRequest, self.log.append)
        self.bus.subscribe(SessionTransition, self.log.append)
        
        self.live_outputs: List[ExecutionReport] = []

        # Subscribe the live engine to process events off the bus
        def handle_event(event):
            outputs = self.engine_live.on_message(event)
            if outputs:
                self.live_outputs.extend(outputs)

        self.bus.subscribe(NewOrderRequest, handle_event)
        self.bus.subscribe(CancelOrderRequest, handle_event)
        self.bus.subscribe(ReplaceOrderRequest, handle_event)
        self.bus.subscribe(SessionTransition, handle_event)

    def test_replay_verification(self):
        # Publish events (deterministic sequence)
        
        # 1. Open session
        self.bus.publish(SessionTransition(1, 1000, "ETH-USD", SessionState.CLOSED, SessionState.CONTINUOUS))
        
        # 2. Add some resting liquidity
        self.bus.publish(NewOrderRequest(2, 2000, 10, "cl-1", "ETH-USD", Side.SELL, OrderType.LIMIT, 30000, 10, TimeInForce.GTC, "FIRM_A"))
        self.bus.publish(NewOrderRequest(3, 3000, 11, "cl-2", "ETH-USD", Side.SELL, OrderType.LIMIT, 30000, 20, TimeInForce.GTC, "FIRM_B"))
        
        # 3. Add an aggressive taker that partially sweeps
        self.bus.publish(NewOrderRequest(4, 4000, 12, "cl-3", "ETH-USD", Side.BUY, OrderType.LIMIT, 30000, 15, TimeInForce.GTC, "FIRM_C"))
        
        # 4. Cancel remaining of first resting order (it filled 10, so it's fully filled and terminal anyway)
        # Wait, order 10 is fully filled. Order 11 is partially filled (5 from 12 matched with 11).
        # Let's cancel order 11.
        self.bus.publish(CancelOrderRequest(5, 5000, 11, "cl-2", "ETH-USD"))
        
        # Ensure live outputs were generated
        self.assertTrue(len(self.live_outputs) > 0)
        
        # Now replay the log into Engine B
        replay_outputs = self.log.replay(self.engine_replay)
        
        # Verification 1: Outputs exactly match
        self.assertEqual(len(self.live_outputs), len(replay_outputs))
        for live_rpt, replay_rpt in zip(self.live_outputs, replay_outputs):
            self.assertEqual(live_rpt, replay_rpt)
            
        # Verification 2: State exactly matches
        live_book = self.engine_live.get_book("ETH-USD")
        replay_book = self.engine_replay.get_book("ETH-USD")
        
        # Check active orders count
        self.assertEqual(
            len(live_book.order_index),
            len(replay_book.order_index)
        )
        
        # Check trades count
        self.assertEqual(
            len(live_book._trade_manager.get_trades()),
            len(replay_book._trade_manager.get_trades())
        )
        
        # Check depths
        self.assertEqual(len(live_book.asks), len(replay_book.asks))
        self.assertEqual(len(live_book.bids), len(replay_book.bids))
        
        # Deep inspection of the trades
        live_trades = live_book._trade_manager.get_trades()
        replay_trades = replay_book._trade_manager.get_trades()
        for lt, rt in zip(live_trades, replay_trades):
            self.assertEqual(lt, rt)

if __name__ == "__main__":
    unittest.main()
