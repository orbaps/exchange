from typing import Dict, List
from validation_engine.snapshots import EngineSnapshot, OrderSnapshot, TradeSnapshot, BookSnapshot
from validation_engine.result import ValidationResult, Mismatch, MismatchType

class StateComparator:
    """Compares the actual engine state against the expected ground truth."""
    
    def compare_snapshots(self, expected: EngineSnapshot, actual: EngineSnapshot) -> ValidationResult:
        """Compares two complete engine snapshots."""
        result = ValidationResult()
        
        # Compare order books
        expected_books = expected.book_snapshots
        actual_books = actual.book_snapshots
        for symbol, exp_book in expected_books.items():
            if symbol not in actual_books:
                result.add_fail(Mismatch(MismatchType.BOOK_STATE, exp_book, None, f"Missing book for {symbol}"))
            else:
                self.compare_books(exp_book, actual_books[symbol], result)
                
        # Compare orders
        expected_orders_map = expected.order_snapshots
        actual_orders_map = actual.order_snapshots
        for symbol, exp_orders in expected_orders_map.items():
            act_orders = actual_orders_map.get(symbol, {})
            if len(exp_orders) != len(act_orders):
                result.add_fail(Mismatch(MismatchType.ORDER_STATE, len(exp_orders), len(act_orders), f"[{symbol}] Order count mismatch"))
            
            for order_id, exp_order in exp_orders.items():
                if order_id not in act_orders:
                    result.add_fail(Mismatch(MismatchType.ORDER_STATE, exp_order, None, f"[{symbol}] Missing order {order_id}"))
                else:
                    self.compare_orders(exp_order, act_orders[order_id], symbol, result)
                    
        # Compare trades
        expected_trades_map = expected.trade_snapshots
        actual_trades_map = actual.trade_snapshots
        for symbol, exp_trades in expected_trades_map.items():
            act_trades = actual_trades_map.get(symbol, [])
            if len(exp_trades) != len(act_trades):
                result.add_fail(Mismatch(MismatchType.TRADE_STATE, len(exp_trades), len(act_trades), f"[{symbol}] Trade count mismatch"))
                
            for i in range(min(len(exp_trades), len(act_trades))):
                self.compare_trades(exp_trades[i], act_trades[i], symbol, i, result)
                
        return result

    def compare_orders(self, expected: OrderSnapshot, actual: OrderSnapshot, symbol: str, result: ValidationResult) -> None:
        """Compares two order snapshots."""
        matched = True
        
        if expected.status != actual.status:
            matched = False
            result.add_fail(Mismatch(MismatchType.ORDER_STATE, expected.status, actual.status, f"[{symbol}] Order {expected.order_id} status mismatch"))
            
        if expected.remaining_quantity != actual.remaining_quantity:
            matched = False
            result.add_fail(Mismatch(MismatchType.ORDER_STATE, expected.remaining_quantity, actual.remaining_quantity, f"[{symbol}] Order {expected.order_id} remaining qty mismatch"))
            
        if expected.filled_quantity != actual.filled_quantity:
            matched = False
            result.add_fail(Mismatch(MismatchType.ORDER_STATE, expected.filled_quantity, actual.filled_quantity, f"[{symbol}] Order {expected.order_id} filled qty mismatch"))
            
        if matched:
            result.add_pass()

    def compare_trades(self, expected: TradeSnapshot, actual: TradeSnapshot, symbol: str, index: int, result: ValidationResult) -> None:
        """Compares two trade snapshots."""
        matched = True
        
        if expected.price != actual.price:
            matched = False
            result.add_fail(Mismatch(MismatchType.TRADE_STATE, expected.price, actual.price, f"[{symbol}] Trade idx {index} price mismatch"))
            
        if expected.quantity != actual.quantity:
            matched = False
            result.add_fail(Mismatch(MismatchType.TRADE_STATE, expected.quantity, actual.quantity, f"[{symbol}] Trade idx {index} quantity mismatch"))
            
        if matched:
            result.add_pass()

    def compare_books(self, expected: BookSnapshot, actual: BookSnapshot, result: ValidationResult) -> None:
        """Compares two order book snapshots."""
        symbol = expected.instrument
        matched = True
        
        if expected.best_bid != actual.best_bid:
            matched = False
            result.add_fail(Mismatch(MismatchType.BOOK_STATE, expected.best_bid, actual.best_bid, f"[{symbol}] Best bid mismatch"))
            
        if expected.bid_depth != actual.bid_depth:
            matched = False
            result.add_fail(Mismatch(MismatchType.BOOK_STATE, expected.bid_depth, actual.bid_depth, f"[{symbol}] Bid depth mismatch"))
            
        if expected.best_ask != actual.best_ask:
            matched = False
            result.add_fail(Mismatch(MismatchType.BOOK_STATE, expected.best_ask, actual.best_ask, f"[{symbol}] Best ask mismatch"))
            
        if expected.ask_depth != actual.ask_depth:
            matched = False
            result.add_fail(Mismatch(MismatchType.BOOK_STATE, expected.ask_depth, actual.ask_depth, f"[{symbol}] Ask depth mismatch"))
            
        if matched:
            result.add_pass()
