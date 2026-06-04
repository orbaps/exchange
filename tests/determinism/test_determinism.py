import unittest
import os
import tempfile
import random
import hashlib

from reference_engine.engine import MatchingEngine
from reference_engine.events import EventBus
from reference_engine.models import (
    InstrumentDefinition, MatchingAlgorithm, SmpMode, Side, OrderType,
    TimeInForce, SessionState, NewOrderRequest, CancelOrderRequest, SessionTransition
)
from sequencer.journal import JournalWriter, JournalReader
from validation_engine.ground_truth import GroundTruthGenerator
from reference_engine.replay.engine import ReplayEngine

class TestDeterminism(unittest.TestCase):
    
    def _run_scenario(self, seed: int):
        random.seed(seed)
        
        inst = InstrumentDefinition(
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
        
        bus = EventBus()
        live_engine = MatchingEngine([inst])
        ground_truth = GroundTruthGenerator(live_engine, bus)
        
        temp_dir = tempfile.TemporaryDirectory()
        journal_path = os.path.join(temp_dir.name, "journal.jsonl")
        writer = JournalWriter(journal_path)
        
        def _send(req):
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
                
            writer.append(req.timestamp_ns, event_type, req.symbol, payload)
            outputs = live_engine.on_message(req)
            if outputs:
                for out in outputs:
                    bus.publish(out)

        # 1. Open
        _send(SessionTransition(1, 1000, "TEST", SessionState.CLOSED, SessionState.CONTINUOUS))
        
        seq = 2
        active_orders = []
        
        # Simulate 100 randomized events
        for _ in range(100):
            action = random.choice(["NEW", "NEW", "NEW", "CANCEL"])
            if action == "NEW" or not active_orders:
                side = random.choice([Side.BUY, Side.SELL])
                price = random.randint(40, 60)
                qty = random.randint(10, 100)
                order_id = seq
                req = NewOrderRequest(seq, seq * 1000, order_id, f"c{seq}", "TEST", side, OrderType.LIMIT, price, qty, TimeInForce.GTC, "F1")
                _send(req)
                active_orders.append(order_id)
            else:
                order_id = random.choice(active_orders)
                req = CancelOrderRequest(seq, seq * 1000, order_id, f"c{seq}", "TEST")
                _send(req)
                active_orders.remove(order_id)
            seq += 1
            
        writer.flush()
        writer.close()
        
        # Calculate Journal Hash
        with open(journal_path, 'rb') as f:
            journal_hash = hashlib.sha256(f.read()).hexdigest()
            
        # Extract ground truth hash (str representation)
        truth_hash = hashlib.sha256(str(ground_truth.records).encode('utf-8')).hexdigest()
        
        temp_dir.cleanup()
        return journal_hash, truth_hash

    def test_determinism_100_runs(self):
        # We run the exact same seed 100 times to ensure bit-identical determinism
        base_seed = 42
        
        # Get baseline
        base_journal_hash, base_truth_hash = self._run_scenario(base_seed)
        
        # Run 99 more times and compare
        for i in range(99):
            journal_hash, truth_hash = self._run_scenario(base_seed)
            self.assertEqual(journal_hash, base_journal_hash, f"Journal deviation at run {i}")
            self.assertEqual(truth_hash, base_truth_hash, f"Ground Truth deviation at run {i}")

if __name__ == "__main__":
    unittest.main()
