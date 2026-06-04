from typing import List, Optional
from reference_engine.models import Trade

class TradeManager:
    """Manages the trade store, keeping a chronological log of all executions."""
    
    def __init__(self) -> None:
        """Initializes the TradeManager."""
        self._trades: List[Trade] = []
        self._next_match_id = 1
        
    def add_trade(self, symbol: str, price: int, quantity: int, buyer_id: int, seller_id: int) -> Trade:
        """Creates and stores a new Trade record."""
        trade = Trade(
            match_id=self._next_match_id,
            symbol=symbol,
            price=price,
            quantity=quantity,
            buyer_order_id=buyer_id,
            seller_order_id=seller_id
        )
        self._trades.append(trade)
        self._next_match_id += 1
        return trade
        
    def get_trades(self) -> List[Trade]:
        """Returns the chronological list of all trades."""
        return list(self._trades)
        
    def get_trades_by_order(self, order_id: int) -> List[Trade]:
        """Returns all trades involving a specific order."""
        return [
            t for t in self._trades 
            if t.buyer_order_id == order_id or t.seller_order_id == order_id
        ]
