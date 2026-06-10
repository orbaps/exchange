import random
from typing import Optional
from botfleet.config import BotConfig
from botfleet.events import TradingEvent

class TradingBot:
    """Encapsulates a trading strategy and config."""
    
    def __init__(self, config: BotConfig, bot_seed: int):
        self.config = config
        self.prng = random.Random(bot_seed)
        
        # Strategy factory instantiation based on config.strategy string
        if self.config.strategy == "RandomTrader":
            from botfleet.strategies.random_trader import RandomTrader
            self.strategy = RandomTrader(config, self.prng)
        elif self.config.strategy == "MarketMaker":
            from botfleet.strategies.market_maker import MarketMaker
            self.strategy = MarketMaker(config, self.prng)
        elif self.config.strategy == "MomentumTrader":
            from botfleet.strategies.momentum import MomentumTrader
            self.strategy = MomentumTrader(config, self.prng)
        elif self.config.strategy == "NoiseTrader":
            from botfleet.strategies.noise import NoiseTrader
            self.strategy = NoiseTrader(config, self.prng)
        else:
            raise ValueError(f"Unknown strategy: {self.config.strategy}")
            
    def next_event(self) -> Optional[TradingEvent]:
        return self.strategy.generate_event()
        
    def reset(self) -> None:
        self.strategy.reset()
