import unittest
from validation_engine.snapshots import EngineSnapshot, OrderSnapshot, TradeSnapshot, BookSnapshot
from validation_engine.comparator import StateComparator
from validation_engine.result import MismatchType
from validation_engine.fingerprint import StateFingerprint

class TestValidationFramework(unittest.TestCase):

    def setUp(self):
        self.comparator = StateComparator()
        
        self.base_book = BookSnapshot(
            instrument="AAPL",
            best_bid=150,
            best_ask=151,
            spread=1,
            bid_depth=100,
            ask_depth=200,
            timestamp=1000
        )
        self.base_order = OrderSnapshot(
            order_id=1,
            status="NEW",
            remaining_quantity=100,
            filled_quantity=0
        )
        self.base_trade = TradeSnapshot(
            trade_id=1,
            price=150,
            quantity=50
        )
        
        self.base_engine = EngineSnapshot(
            book_snapshots={"AAPL": self.base_book},
            order_snapshots={"AAPL": {1: self.base_order}},
            trade_snapshots={"AAPL": [self.base_trade]}
        )

    def test_1_identical_states_pass(self):
        result = self.comparator.compare_snapshots(self.base_engine, self.base_engine)
        self.assertEqual(result.failed_checks, 0)
        self.assertEqual(result.correctness_score, 100.0)

    def test_2_different_order_state_fails(self):
        actual_order = OrderSnapshot(
            order_id=1,
            status="PARTIALLY_FILLED",
            remaining_quantity=50,
            filled_quantity=50
        )
        actual_engine = EngineSnapshot(
            book_snapshots={"AAPL": self.base_book},
            order_snapshots={"AAPL": {1: actual_order}},
            trade_snapshots={"AAPL": [self.base_trade]}
        )
        result = self.comparator.compare_snapshots(self.base_engine, actual_engine)
        self.assertGreater(result.failed_checks, 0)
        self.assertLess(result.correctness_score, 100.0)
        
        mismatches = [m.mismatch_type for m in result.mismatches]
        self.assertIn(MismatchType.ORDER_STATE, mismatches)

    def test_3_different_trade_state_fails(self):
        actual_trade = TradeSnapshot(
            trade_id=1,
            price=149,
            quantity=50
        )
        actual_engine = EngineSnapshot(
            book_snapshots={"AAPL": self.base_book},
            order_snapshots={"AAPL": {1: self.base_order}},
            trade_snapshots={"AAPL": [actual_trade]}
        )
        result = self.comparator.compare_snapshots(self.base_engine, actual_engine)
        self.assertGreater(result.failed_checks, 0)
        
        mismatches = [m.mismatch_type for m in result.mismatches]
        self.assertIn(MismatchType.TRADE_STATE, mismatches)

    def test_4_different_book_state_fails(self):
        actual_book = BookSnapshot(
            instrument="AAPL",
            best_bid=149,
            best_ask=151,
            spread=2,
            bid_depth=100,
            ask_depth=200,
            timestamp=1000
        )
        actual_engine = EngineSnapshot(
            book_snapshots={"AAPL": actual_book},
            order_snapshots={"AAPL": {1: self.base_order}},
            trade_snapshots={"AAPL": [self.base_trade]}
        )
        result = self.comparator.compare_snapshots(self.base_engine, actual_engine)
        self.assertGreater(result.failed_checks, 0)
        
        mismatches = [m.mismatch_type for m in result.mismatches]
        self.assertIn(MismatchType.BOOK_STATE, mismatches)

    def test_5_fingerprint_equality(self):
        hash1 = StateFingerprint.order_hash(self.base_order)
        hash2 = StateFingerprint.order_hash(self.base_order)
        self.assertEqual(hash1, hash2)
        
        book_hash1 = StateFingerprint.book_hash(self.base_book)
        book_hash2 = StateFingerprint.book_hash(self.base_book)
        self.assertEqual(book_hash1, book_hash2)

    def test_6_fingerprint_mismatch(self):
        hash1 = StateFingerprint.order_hash(self.base_order)
        
        diff_order = OrderSnapshot(
            order_id=1,
            status="FILLED",
            remaining_quantity=0,
            filled_quantity=100
        )
        hash2 = StateFingerprint.order_hash(diff_order)
        
        self.assertNotEqual(hash1, hash2)

if __name__ == '__main__':
    unittest.main()
