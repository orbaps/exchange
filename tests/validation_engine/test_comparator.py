import unittest
from validation_engine.snapshots import EngineSnapshot, OrderSnapshot
from validation_engine.comparator import StateComparator

class TestComparator(unittest.TestCase):

    def test_comparator_symmetry(self):
        comp = StateComparator()
        
        expected = EngineSnapshot(
            book_snapshots={},
            order_snapshots={
                "TEST": {
                    1: OrderSnapshot(order_id=1, status="NEW", remaining_quantity=100, filled_quantity=0)
                }
            },
            trade_snapshots={}
        )
        
        actual = EngineSnapshot(
            book_snapshots={},
            order_snapshots={
                "TEST": {
                    1: OrderSnapshot(order_id=1, status="NEW", remaining_quantity=100, filled_quantity=0),
                    2: OrderSnapshot(order_id=2, status="NEW", remaining_quantity=50, filled_quantity=0)
                }
            },
            trade_snapshots={}
        )
        
        result = comp.compare_snapshots(expected, actual)
        
        self.assertLess(result.correctness_score, 100.0)
        self.assertGreater(result.failed_checks, 0)
        
        # Verify the extra order generated a specific mismatch string
        mismatch_strs = [err.details for err in result.mismatches]
        self.assertTrue(any("Unexpected extra order 2" in msg for msg in mismatch_strs))

if __name__ == '__main__':
    unittest.main()
