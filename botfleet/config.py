from dataclasses import dataclass
from botfleet.orderflow import MarketRegime

@dataclass
class BotConfig:
    bot_id: str
    strategy: str  # e.g. "RandomTrader", "MarketMaker", "MomentumTrader", "NoiseTrader"
    order_rate: float
    max_position: int
    instrument: str
    regime: MarketRegime = MarketRegime.CALM

@dataclass
class FleetConfig:
    num_bots: int
    duration_seconds: float
    events_per_second: float
    seed: int
    regime: MarketRegime = MarketRegime.CALM
