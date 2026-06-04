from dataclasses import dataclass
from typing import List
from reference_engine.replay.engine import ReplayResult
from validation_engine.ground_truth import ValidationRecord

@dataclass
class ReplayVerificationResult:
    """Result of comparing a replay execution against a ground truth validation sequence."""
    is_valid: bool
    errors: List[str]

class ReplayVerifier:
    """Verifies that the state reconstructed by ReplayEngine perfectly matches GroundTruth."""
    
    def verify(self, replay_result: ReplayResult, ground_truth: List[ValidationRecord]) -> ReplayVerificationResult:
        """Compares the final ReplayResult against the final state in the ground truth."""
        errors = []
        
        if not ground_truth:
            return ReplayVerificationResult(is_valid=True, errors=[])
            
        final_truth = ground_truth[-1]
        
        # 1. Compare Order Books
        for symbol, expected_book in final_truth.expected_book_state.book_snapshots.items():
            if symbol not in replay_result.orderbooks:
                errors.append(f"Symbol {symbol} missing from replay orderbooks.")
                continue
                
            actual_book = replay_result.orderbooks[symbol]
            
            actual_best_bid = max(actual_book.bids.keys()) if actual_book.bids else 0
            actual_bid_depth = sum(lvl.total_quantity for lvl in actual_book.bids.values()) if actual_book.bids else 0
            actual_best_ask = min(actual_book.asks.keys()) if actual_book.asks else 0
            actual_ask_depth = sum(lvl.total_quantity for lvl in actual_book.asks.values()) if actual_book.asks else 0
            
            if actual_best_bid != expected_book.best_bid:
                errors.append(f"[{symbol}] Best bid mismatch: expected {expected_book.best_bid}, got {actual_best_bid}")
            if actual_bid_depth != expected_book.bid_depth:
                errors.append(f"[{symbol}] Bid depth mismatch: expected {expected_book.bid_depth}, got {actual_bid_depth}")
            if actual_best_ask != expected_book.best_ask:
                errors.append(f"[{symbol}] Best ask mismatch: expected {expected_book.best_ask}, got {actual_best_ask}")
            if actual_ask_depth != expected_book.ask_depth:
                errors.append(f"[{symbol}] Ask depth mismatch: expected {expected_book.ask_depth}, got {actual_ask_depth}")

        # 2. Compare Orders
        for symbol, expected_orders in final_truth.expected_order_state.order_snapshots.items():
            if symbol not in replay_result.orders:
                errors.append(f"Symbol {symbol} missing from replay orders.")
                continue
                
            actual_orders = replay_result.orders[symbol]
            
            if len(actual_orders) != len(expected_orders):
                errors.append(f"[{symbol}] Order count mismatch: expected {len(expected_orders)}, got {len(actual_orders)}")
                
            for order_id, expected_order in expected_orders.items():
                if order_id not in actual_orders:
                    errors.append(f"[{symbol}] Order {order_id} missing in replay state.")
                    continue
                    
                actual_order = actual_orders[order_id]
                if actual_order.state.name != expected_order.status:
                    errors.append(f"[{symbol}] Order {order_id} status mismatch: expected {expected_order.status}, got {actual_order.state.name}")
                if actual_order.leaves_qty != expected_order.remaining_quantity:
                    errors.append(f"[{symbol}] Order {order_id} leaves qty mismatch: expected {expected_order.remaining_quantity}, got {actual_order.leaves_qty}")
                if actual_order.cumulative_qty != expected_order.filled_quantity:
                    errors.append(f"[{symbol}] Order {order_id} filled qty mismatch: expected {expected_order.filled_quantity}, got {actual_order.cumulative_qty}")
                    
        # 3. Compare Trades
        for symbol, expected_trades in final_truth.expected_trade_state.trade_snapshots.items():
            if symbol not in replay_result.trades:
                errors.append(f"Symbol {symbol} missing from replay trades.")
                continue
                
            actual_trades = replay_result.trades[symbol]
            
            if len(actual_trades) != len(expected_trades):
                errors.append(f"[{symbol}] Trade count mismatch: expected {len(expected_trades)}, got {len(actual_trades)}")
                
            for i in range(min(len(expected_trades), len(actual_trades))):
                if actual_trades[i].match_id != expected_trades[i].trade_id:
                    errors.append(f"[{symbol}] Trade {i} ID mismatch: expected {expected_trades[i].trade_id}, got {actual_trades[i].match_id}")
                if actual_trades[i].price != expected_trades[i].price:
                    errors.append(f"[{symbol}] Trade {i} price mismatch: expected {expected_trades[i].price}, got {actual_trades[i].price}")
                if actual_trades[i].quantity != expected_trades[i].quantity:
                    errors.append(f"[{symbol}] Trade {i} quantity mismatch: expected {expected_trades[i].quantity}, got {actual_trades[i].quantity}")

        return ReplayVerificationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
