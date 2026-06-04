import unittest
import os
import tempfile

from reference_engine.engine import MatchingEngine
from reference_engine.events import EventBus
from reference_engine.models import (
    InstrumentDefinition, MatchingAlgorithm, SmpMode, Side, OrderType,
    TimeInForce, SessionState, NewOrderRequest, CancelOrderRequest, SessionTransition
)
from sequencer.journal import JournalWriter, JournalReader, JournalRecord
from validation_engine.ground_truth import GroundTruthGenerator
from validation_engine.replay_verifier import ReplayVerifier
from reference_engine.replay.engine import ReplayEngine

class TestGoldenScenarios(unittest.TestCase):
    
    def setUp(self):
        self.inst = InstrumentDefinition(
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
        
        self.bus = EventBus()
        self.live_engine = MatchingEngine([self.inst])
        self.ground_truth = GroundTruthGenerator(self.live_engine, self.bus)
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.journal_path = os.path.join(self.temp_dir.name, "journal.jsonl")
        self.writer = JournalWriter(self.journal_path)
        
        # Route events to Live Engine and Journal
        self._seq = 1
        self._time = 1000
        
    def tearDown(self):
        self.writer.close()
        self.temp_dir.cleanup()
        
    def _send(self, req):
        # 1. Journal the Request
        if isinstance(req, NewOrderRequest):
            payload = {
                "sequence_no": req.sequence_no,
                "timestamp_ns": req.timestamp_ns,
                "order_id": req.order_id,
                "client_order_id": req.client_order_id,
                "symbol": req.symbol,
                "side": req.side.name,
                "order_type": req.order_type.name,
                "price": req.price,
                "quantity": req.quantity,
                "tif": req.tif.name,
                "party_id": req.party_id,
                "stop_price": req.stop_price
            }
            event_type = "NewOrderRequest"
        elif isinstance(req, CancelOrderRequest):
            payload = {
                "sequence_no": req.sequence_no,
                "timestamp_ns": req.timestamp_ns,
                "order_id": req.order_id,
                "client_order_id": req.client_order_id,
                "symbol": req.symbol
            }
            event_type = "CancelOrderRequest"
        elif isinstance(req, SessionTransition):
            payload = {
                "sequence_no": req.sequence_no,
                "timestamp_ns": req.timestamp_ns,
                "symbol": req.symbol,
                "from_state": req.from_state.name,
                "to_state": req.to_state.name
            }
            event_type = "SessionTransition"
            
        self.writer.append(req.timestamp_ns, event_type, req.symbol, payload)
        
        # 2. Process in Live Engine
        outputs = self.live_engine.on_message(req)
        
        # 3. Publish Outputs to EventBus to generate Snapshots
        if outputs:
            for out in outputs:
                self.bus.publish(out)
                
    def _verify_replay(self):
        self.writer.flush()
        self.writer.close()
        
        reader = JournalReader(self.journal_path)
        records = reader.read_all()
        reader.close()
        
        replay_engine = ReplayEngine(MatchingEngine([self.inst]))
        result = replay_engine.replay(records)
        
        verifier = ReplayVerifier()
        verification = verifier.verify(result, self.ground_truth.records)
        self.assertTrue(verification.is_valid, f"Replay Verification Failed: {verification.errors}")
        
    def test_scenario_1_simple_fill(self):
        self._send(SessionTransition(1, 1000, "TEST", SessionState.CLOSED, SessionState.CONTINUOUS))
        self._send(NewOrderRequest(2, 2000, 1, "c1", "TEST", Side.BUY, OrderType.LIMIT, 50, 100, TimeInForce.GTC, "F1"))
        self._send(NewOrderRequest(3, 3000, 2, "c2", "TEST", Side.SELL, OrderType.LIMIT, 50, 100, TimeInForce.GTC, "F2"))
        
        book = self.live_engine.get_book("TEST")
        self.assertEqual(len(book.order_index), 0)
        self.assertEqual(len(book._trade_manager.get_trades()), 1)
        
        self._verify_replay()
        
    def test_scenario_2_partial_fill(self):
        self._send(SessionTransition(1, 1000, "TEST", SessionState.CLOSED, SessionState.CONTINUOUS))
        self._send(NewOrderRequest(2, 2000, 1, "c1", "TEST", Side.BUY, OrderType.LIMIT, 50, 100, TimeInForce.GTC, "F1"))
        self._send(NewOrderRequest(3, 3000, 2, "c2", "TEST", Side.SELL, OrderType.LIMIT, 50, 20, TimeInForce.GTC, "F2"))
        
        book = self.live_engine.get_book("TEST")
        self.assertEqual(len(book.order_index), 1)
        self.assertEqual(book.order_index[1].leaves_qty, 80)
        self.assertEqual(len(book._trade_manager.get_trades()), 1)
        
        self._verify_replay()
        
    def test_scenario_3_fifo(self):
        self._send(SessionTransition(1, 1000, "TEST", SessionState.CLOSED, SessionState.CONTINUOUS))
        self._send(NewOrderRequest(2, 2000, 1, "c1", "TEST", Side.BUY, OrderType.LIMIT, 50, 100, TimeInForce.GTC, "F1"))
        self._send(NewOrderRequest(3, 3000, 2, "c2", "TEST", Side.BUY, OrderType.LIMIT, 50, 100, TimeInForce.GTC, "F2"))
        self._send(NewOrderRequest(4, 4000, 3, "c3", "TEST", Side.SELL, OrderType.LIMIT, 50, 150, TimeInForce.GTC, "F3"))
        
        book = self.live_engine.get_book("TEST")
        self.assertEqual(len(book.order_index), 1)
        self.assertEqual(book.order_index[2].leaves_qty, 50)
        self.assertEqual(len(book._trade_manager.get_trades()), 2)
        
        self._verify_replay()
        
    def test_scenario_4_multi_level_fill(self):
        self._send(SessionTransition(1, 1000, "TEST", SessionState.CLOSED, SessionState.CONTINUOUS))
        self._send(NewOrderRequest(2, 2000, 1, "c1", "TEST", Side.SELL, OrderType.LIMIT, 50, 20, TimeInForce.GTC, "F1"))
        self._send(NewOrderRequest(3, 3000, 2, "c2", "TEST", Side.SELL, OrderType.LIMIT, 51, 30, TimeInForce.GTC, "F2"))
        self._send(NewOrderRequest(4, 4000, 3, "c3", "TEST", Side.SELL, OrderType.LIMIT, 52, 40, TimeInForce.GTC, "F3"))
        
        self._send(NewOrderRequest(5, 5000, 4, "c4", "TEST", Side.BUY, OrderType.LIMIT, 52, 70, TimeInForce.GTC, "F4"))
        
        book = self.live_engine.get_book("TEST")
        self.assertEqual(len(book.order_index), 1)
        self.assertEqual(book.order_index[3].leaves_qty, 20)
        self.assertEqual(len(book._trade_manager.get_trades()), 3)
        
        self._verify_replay()
        
    def test_scenario_5_cancel_after_partial(self):
        self._send(SessionTransition(1, 1000, "TEST", SessionState.CLOSED, SessionState.CONTINUOUS))
        self._send(NewOrderRequest(2, 2000, 1, "c1", "TEST", Side.BUY, OrderType.LIMIT, 50, 100, TimeInForce.GTC, "F1"))
        self._send(NewOrderRequest(3, 3000, 2, "c2", "TEST", Side.SELL, OrderType.LIMIT, 50, 40, TimeInForce.GTC, "F2"))
        
        book = self.live_engine.get_book("TEST")
        self.assertEqual(book.order_index[1].leaves_qty, 60)
        
        self._send(CancelOrderRequest(4, 4000, 1, "c1", "TEST"))
        self.assertEqual(len(book.order_index), 0)
        self.assertEqual(len(book._trade_manager.get_trades()), 1)
        
        self._verify_replay()

if __name__ == "__main__":
    unittest.main()
