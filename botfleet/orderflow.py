from enum import Enum
from dataclasses import dataclass

class MarketRegime(Enum):
    CALM = "CALM"
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    VOLATILE = "VOLATILE"
    FLASH_CRASH = "FLASH_CRASH"
    RECOVERY = "RECOVERY"

@dataclass
class RegimeProfile:
    spread_ticks: int
    cancel_rate: float
    order_rate_multiplier: float
    market_order_ratio: float
    price_drift: int

class OrderFlowManager:
    """Provides market regime configuration parameters."""
    
    REGIMES = {
        MarketRegime.CALM: RegimeProfile(
            spread_ticks=1,
            cancel_rate=0.10,
            order_rate_multiplier=1.0,
            market_order_ratio=0.05,
            price_drift=0
        ),
        MarketRegime.TRENDING_UP: RegimeProfile(
            spread_ticks=2,
            cancel_rate=0.20,
            order_rate_multiplier=1.2,
            market_order_ratio=0.15,
            price_drift=5
        ),
        MarketRegime.TRENDING_DOWN: RegimeProfile(
            spread_ticks=2,
            cancel_rate=0.20,
            order_rate_multiplier=1.2,
            market_order_ratio=0.15,
            price_drift=-5
        ),
        MarketRegime.VOLATILE: RegimeProfile(
            spread_ticks=5,
            cancel_rate=0.40,
            order_rate_multiplier=2.0,
            market_order_ratio=0.25,
            price_drift=0
        ),
        MarketRegime.FLASH_CRASH: RegimeProfile(
            spread_ticks=10,
            cancel_rate=0.80,
            order_rate_multiplier=5.0,
            market_order_ratio=0.50,
            price_drift=-50
        ),
        MarketRegime.RECOVERY: RegimeProfile(
            spread_ticks=3,
            cancel_rate=0.30,
            order_rate_multiplier=1.5,
            market_order_ratio=0.20,
            price_drift=10
        )
    }
    
    @classmethod
    def get_profile(cls, regime: MarketRegime) -> RegimeProfile:
        return cls.REGIMES[regime]
