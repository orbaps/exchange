import uuid
from typing import Optional
from botfleet.strategies import TradingStrategy
from botfleet.events import TradingEvent, EventType
from botfleet.orderflow import OrderFlowManager

class MomentumTrader(TradingStrategy):
    """Trend-following trader, often uses market orders to cross spread."""
    
    def __init__(self, config, prng):
        super().__init__(config, prng)
        self.profile = OrderFlowManager.get_profile(self.config.regime)
        self.base_price = 10000
        
    def generate_event(self) -> Optional[TradingEvent]:
        event_id = str(uuid.UUID(int=self.prng.getrandbits(128)))
        
        # High market order probability
        if self.prng.random() < self.profile.market_order_ratio * 2.0:
            return TradingEvent(
                event_id=event_id,
                timestamp_ns=0,
                bot_id=self.config.bot_id,
                instrument=self.config.instrument,
                event_type=EventType.MARKET_ORDER,
                quantity=self.prng.randint(10, 50),
                price=0,
                side=self.prng.choice(["BUY", "SELL"])
            )
            
        qty = self.prng.randint(5, 20)
        # Follow the drift heavily
        price = self.base_price + (self.profile.price_drift * 2) + self.prng.randint(-10, 10)
        
        return TradingEvent(
            event_id=event_id,
            timestamp_ns=0,
            bot_id=self.config.bot_id,
            instrument=self.config.instrument,
            event_type=EventType.NEW_ORDER,
            quantity=qty,
            price=price,
            side=self.prng.choice(["BUY", "SELL"])
        )
        
    def reset(self) -> None:
        self.base_price = 10000
