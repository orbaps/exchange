import uuid
import time
from typing import Optional
from botfleet.strategies import TradingStrategy
from botfleet.events import TradingEvent, EventType
from botfleet.orderflow import OrderFlowManager

class MarketMaker(TradingStrategy):
    """Provides bid-ask quotes around a fair value."""
    
    def __init__(self, config, prng):
        super().__init__(config, prng)
        self.profile = OrderFlowManager.get_profile(self.config.regime)
        self.fair_value = 10000
        self.next_side = "BUY"
        
    def generate_event(self) -> Optional[TradingEvent]:
        event_id = str(uuid.UUID(int=self.prng.getrandbits(128)))
        
        # Periodically cancel orders or adjust
        if self.prng.random() < self.profile.cancel_rate:
            return TradingEvent(
                event_id=event_id,
                timestamp_ns=0,
                bot_id=self.config.bot_id,
                instrument=self.config.instrument,
                event_type=EventType.CANCEL,
                quantity=0,
                price=0,
                side=self.prng.choice(["BUY", "SELL"]),
                order_id=str(uuid.UUID(int=self.prng.getrandbits(128)))
            )
            
        spread = self.profile.spread_ticks * 5
        qty = self.prng.randint(5, 20)
        
        if self.next_side == "BUY":
            price = self.fair_value - spread + self.profile.price_drift
            side = "BUY"
            self.next_side = "SELL"
        else:
            price = self.fair_value + spread + self.profile.price_drift
            side = "SELL"
            self.next_side = "BUY"
            
        return TradingEvent(
            event_id=event_id,
            timestamp_ns=0,
            bot_id=self.config.bot_id,
            instrument=self.config.instrument,
            event_type=EventType.NEW_ORDER,
            quantity=qty,
            price=price,
            side=side
        )
        
    def reset(self) -> None:
        self.fair_value = 10000
        self.next_side = "BUY"
