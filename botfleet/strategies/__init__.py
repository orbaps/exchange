from abc import ABC, abstractmethod
from typing import Optional
import random
from botfleet.config import BotConfig
from botfleet.events import TradingEvent

class TradingStrategy(ABC):
    """Abstract base class for all bot fleet strategies."""
    
    def __init__(self, config: BotConfig, prng: random.Random):
        self.config = config
        self.prng = prng
    
    @abstractmethod
    def generate_event(self) -> Optional[TradingEvent]:
        """Generates the next event for the bot, if any."""
        pass
        
    @abstractmethod
    def reset(self) -> None:
        """Resets the strategy state."""
        pass
