from typing import Dict, Optional, List
from reference_engine.models import Order, ExecutionReport, CancelOrderRequest, ReplaceOrderRequest

class OrderManager:
    """Manages the lifecycle and state of orders, providing lookup and modification capabilities."""
    
    def __init__(self) -> None:
        """Initializes the OrderManager."""
        self._orders: Dict[int, Order] = {}
        self._client_order_id_index: Dict[str, int] = {}
        
    def add_order(self, order: Order) -> None:
        """Registers a new order in the manager."""
        if order.order_id in self._orders:
            raise ValueError(f"Order ID {order.order_id} already exists.")
        if order.client_order_id in self._client_order_id_index:
            raise ValueError(f"Client Order ID {order.client_order_id} already exists.")
            
        self._orders[order.order_id] = order
        self._client_order_id_index[order.client_order_id] = order.order_id

    def get_order(self, order_id: int) -> Optional[Order]:
        """Retrieves an order by its internal order ID."""
        return self._orders.get(order_id)
        
    def get_order_by_client_id(self, client_order_id: str) -> Optional[Order]:
        """Retrieves an order by its client order ID."""
        order_id = self._client_order_id_index.get(client_order_id)
        if order_id is not None:
            return self._orders.get(order_id)
        return None

    def has_client_order_id(self, client_order_id: str) -> bool:
        """Checks if a client order ID is already active."""
        return client_order_id in self._client_order_id_index

    def remove_terminal_orders(self) -> None:
        """Cleans up orders that have reached a terminal state."""
        to_remove = [o_id for o_id, order in self._orders.items() if order.is_terminal()]
        for o_id in to_remove:
            order = self._orders.pop(o_id)
            self._client_order_id_index.pop(order.client_order_id, None)

    def cancel_order(self, request: CancelOrderRequest) -> ExecutionReport:
        """Cancels an order based on CancelOrderRequest and returns the ExecutionReport."""
        order = self.get_order(request.order_id)
        if not order:
            from reference_engine.models import ExecutionReport, ExecType, RejectReason, Side
            return ExecutionReport(
                sequence_no=request.sequence_no,
                timestamp_ns=request.timestamp_ns,
                execution_id=0,
                order_id=request.order_id,
                client_order_id=request.client_order_id,
                symbol=request.symbol,
                side=Side.SIDE_UNSPECIFIED,
                exec_type=ExecType.REJECTED,
                last_price=0,
                last_qty=0,
                leaves_qty=0,
                cumulative_qty=0,
                original_qty=0,
                reject_reason=RejectReason.UNKNOWN_ORDER_ID,
                match_order_id=0,
            )
            
        if order.is_terminal():
            from reference_engine.models import ExecutionReport, ExecType, RejectReason
            return ExecutionReport(
                sequence_no=request.sequence_no,
                timestamp_ns=request.timestamp_ns,
                execution_id=0,
                order_id=request.order_id,
                client_order_id=request.client_order_id,
                symbol=request.symbol,
                side=order.side,
                exec_type=ExecType.REJECTED,
                last_price=0,
                last_qty=0,
                leaves_qty=order.leaves_qty,
                cumulative_qty=order.cumulative_qty,
                original_qty=order.original_qty,
                reject_reason=RejectReason.ORDER_ALREADY_TERMINAL,
                match_order_id=0,
            )

        report = order.cancel(
            execution_id=request.sequence_no, 
            sequence_no=request.sequence_no, 
            timestamp_ns=request.timestamp_ns
        )
        # Order is now terminal. It will be cleaned up by OrderBook when processing the cancel
        return report

    @property
    def all_orders(self) -> List[Order]:
        """Returns a list of all active orders."""
        return list(self._orders.values())
