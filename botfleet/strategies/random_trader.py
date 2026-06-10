import uuid
import time
from typing import Optional
from botfleet.strategies import TradingStrategy
from botfleet.events import TradingEvent, EventType
from botfleet.orderflow import OrderFlowManager

class RandomTrader(TradingStrategy):
    """Submits uniform random orders within defined boundaries."""
    
    def __init__(self, config, prng):
        super().__init__(config, prng)
        self.profile = OrderFlowManager.get_profile(self.config.regime)
        self.base_price = 10000
        
    def generate_event(self) -> Optional[TradingEvent]:
        # Simple implementation: either NEW_ORDER or CANCEL
        # In a real bot, we'd track open orders to cancel them, but for load gen we can emit random CANCELs
        
        event_id = str(uuid.UUID(int=self.prng.getrandbits(128)))
        
        rand_val = self.prng.random()
        
        if rand_val < self.profile.cancel_rate:
            event_type = EventType.CANCEL
            order_id = str(uuid.UUID(int=self.prng.getrandbits(128)))
            price = 0
            qty = 0
            side = "BUY"
        elif rand_val < self.profile.cancel_rate + self.profile.market_order_ratio:
            event_type = EventType.MARKET_ORDER
            order_id = None
            price = 0
            qty = self.prng.randint(1, 10)
            side = self.prng.choice(["BUY", "SELL"])
        else:
            event_type = EventType.NEW_ORDER
            order_id = None
            price = self.base_price + self.prng.randint(-50, 50) + self.profile.price_drift
            qty = self.prng.randint(1, 10)
            side = self.prng.choice(["BUY", "SELL"])
            
        return TradingEvent(
            event_id=event_id,
            timestamp_ns=time.time_ns(), # This will be overridden by the worker, but provided here as fallback
            bot_id=self.config.bot_id,
            instrument=self.config.instrument,
            event_type=event_type,
            quantity=qty,
            price=price,
            side=side,
            order_id=order_id
        )
        
    def reset(self) -> None:
        self.base_price = 10000
