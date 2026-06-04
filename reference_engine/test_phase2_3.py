import unittest
from reference_engine.models import (
    Order, Side, OrderType, TimeInForce, OrderState, ExecType, RejectReason,
    CancelOrderRequest, NewOrderRequest, ExecutionReport
)
from reference_engine.order_manager import OrderManager
from reference_engine.trade_manager import TradeManager

class TestOrderManager(unittest.TestCase):
    def setUp(self):
        self.manager = OrderManager()

    def test_add_order(self):
        order = Order(1, "cl-1", "BTC-USD", Side.BUY, OrderType.LIMIT, 10000, 10, TimeInForce.GTC, "A", 1)
        self.manager.add_order(order)
        self.assertEqual(self.manager.get_order(1), order)
        self.assertEqual(self.manager.get_order_by_client_id("cl-1"), order)
        self.assertTrue(self.manager.has_client_order_id("cl-1"))
        
        # Test duplicates
        with self.assertRaises(ValueError):
            self.manager.add_order(order)

    def test_cancel_active_order(self):
        order = Order(1, "cl-1", "BTC-USD", Side.BUY, OrderType.LIMIT, 10000, 10, TimeInForce.GTC, "A", 1)
        self.manager.add_order(order)
        
        req = CancelOrderRequest(2, 2000, 1, "cl-1", "BTC-USD")
        report = self.manager.cancel_order(req)
        
        self.assertEqual(report.exec_type, ExecType.CANCELED)
        self.assertEqual(order.state, OrderState.CANCELED)
        
    def test_cancel_unknown_order(self):
        req = CancelOrderRequest(2, 2000, 999, "unknown", "BTC-USD")
        report = self.manager.cancel_order(req)
        self.assertEqual(report.exec_type, ExecType.REJECTED)
        self.assertEqual(report.reject_reason, RejectReason.UNKNOWN_ORDER_ID)

    def test_cancel_terminal_order(self):
        order = Order(1, "cl-1", "BTC-USD", Side.BUY, OrderType.LIMIT, 10000, 10, TimeInForce.GTC, "A", 1)
        self.manager.add_order(order)
        
        # Fill it completely so it's terminal
        order.fill(10, 10000, 2, 2, 2000)
        
        req = CancelOrderRequest(3, 3000, 1, "cl-1", "BTC-USD")
        report = self.manager.cancel_order(req)
        
        self.assertEqual(report.exec_type, ExecType.REJECTED)
        self.assertEqual(report.reject_reason, RejectReason.ORDER_ALREADY_TERMINAL)

    def test_remove_terminal_orders(self):
        o1 = Order(1, "cl-1", "BTC-USD", Side.BUY, OrderType.LIMIT, 10000, 10, TimeInForce.GTC, "A", 1)
        o2 = Order(2, "cl-2", "BTC-USD", Side.SELL, OrderType.LIMIT, 10000, 20, TimeInForce.GTC, "B", 2)
        
        self.manager.add_order(o1)
        self.manager.add_order(o2)
        
        # Make o1 terminal
        o1.cancel(3, 3, 3000)
        
        self.manager.remove_terminal_orders()
        
        self.assertIsNone(self.manager.get_order(1))
        self.assertFalse(self.manager.has_client_order_id("cl-1"))
        
        self.assertEqual(self.manager.get_order(2), o2)
        self.assertTrue(self.manager.has_client_order_id("cl-2"))


class TestTradeManager(unittest.TestCase):
    def setUp(self):
        self.manager = TradeManager()

    def test_add_and_get_trades(self):
        trade1 = self.manager.add_trade("BTC-USD", 10000, 10, 1, 2)
        trade2 = self.manager.add_trade("BTC-USD", 10050, 5, 3, 2)
        
        self.assertEqual(trade1.match_id, 1)
        self.assertEqual(trade2.match_id, 2)
        self.assertEqual(trade1.buyer_order_id, 1)
        self.assertEqual(trade2.buyer_order_id, 3)
        
        all_trades = self.manager.get_trades()
        self.assertEqual(len(all_trades), 2)
        
        order2_trades = self.manager.get_trades_by_order(2)
        self.assertEqual(len(order2_trades), 2)
        
        order1_trades = self.manager.get_trades_by_order(1)
        self.assertEqual(len(order1_trades), 1)
        self.assertEqual(order1_trades[0].match_id, 1)

if __name__ == "__main__":
    unittest.main()
