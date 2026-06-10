import uuid
from typing import Optional
from botfleet.strategies import TradingStrategy
from botfleet.events import TradingEvent, EventType
from botfleet.orderflow import OrderFlowManager

class NoiseTrader(TradingStrategy):
    """High-frequency random noise, emphasizes replaces and cancels."""
    
    def __init__(self, config, prng):
        super().__init__(config, prng)
        self.profile = OrderFlowManager.get_profile(self.config.regime)
        
    def generate_event(self) -> Optional[TradingEvent]:
        event_id = str(uuid.UUID(int=self.prng.getrandbits(128)))
        rand_val = self.prng.random()
        
        # Amplified cancel rate for noise traders
        if rand_val < self.profile.cancel_rate * 1.5:
            event_type = EventType.CANCEL
            order_id = str(uuid.UUID(int=self.prng.getrandbits(128)))
            price = 0
            qty = 0
        elif rand_val < (self.profile.cancel_rate * 1.5) + 0.3: # 30% replaces
            event_type = EventType.REPLACE
            order_id = str(uuid.UUID(int=self.prng.getrandbits(128)))
            price = 10000 + self.prng.randint(-100, 100)
            qty = self.prng.randint(1, 100)
        else:
            event_type = EventType.NEW_ORDER
            order_id = None
            price = 10000 + self.prng.randint(-200, 200)
            qty = self.prng.randint(1, 5)
            
        return TradingEvent(
            event_id=event_id,
            timestamp_ns=0,
            bot_id=self.config.bot_id,
            instrument=self.config.instrument,
            event_type=event_type,
            quantity=qty,
            price=price,
            side=self.prng.choice(["BUY", "SELL"]),
            order_id=order_id
        )
        
    def reset(self) -> None:
        pass
