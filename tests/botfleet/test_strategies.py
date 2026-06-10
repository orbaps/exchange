import unittest
import random
from collections import Counter
from botfleet.config import BotConfig
from botfleet.events import EventType
from botfleet.orderflow import MarketRegime

class TestStrategies(unittest.TestCase):
    
    def _get_config(self, strat: str, regime: MarketRegime):
        return BotConfig(bot_id="b1", strategy=strat, order_rate=100.0, max_position=100, instrument="BTC-USD", regime=regime)
        
    def test_event_mix(self):
        """NoiseTrader should produce more cancels and replaces than MarketMaker."""
        mm_cfg = self._get_config("MarketMaker", MarketRegime.CALM)
        nt_cfg = self._get_config("NoiseTrader", MarketRegime.CALM)
        
        prng1 = random.Random(42)
        prng2 = random.Random(42)
        
        from botfleet.bot import TradingBot
        mm_bot = TradingBot(mm_cfg, bot_seed=42)
        nt_bot = TradingBot(nt_cfg, bot_seed=42)
        
        mm_events = [mm_bot.next_event() for _ in range(1000)]
        nt_events = [nt_bot.next_event() for _ in range(1000)]
        
        mm_types = Counter(e.event_type for e in mm_events if e)
        nt_types = Counter(e.event_type for e in nt_events if e)
        
        # Noise trader should have replaces, MarketMaker shouldn't.
        self.assertTrue(nt_types[EventType.REPLACE] > 0)
        self.assertEqual(mm_types[EventType.REPLACE], 0)
        
        # Noise trader should have more cancels than MarketMaker under CALM.
        # CALM MM cancel rate = 10%. CALM Noise cancel rate = 15%.
        self.assertTrue(nt_types[EventType.CANCEL] > mm_types[EventType.CANCEL])

    def test_regime_transitions(self):
        """CALM -> FLASH_CRASH should dramatically increase market orders."""
        from botfleet.bot import TradingBot
        
        calm_cfg = self._get_config("MomentumTrader", MarketRegime.CALM)
        crash_cfg = self._get_config("MomentumTrader", MarketRegime.FLASH_CRASH)
        
        calm_bot = TradingBot(calm_cfg, bot_seed=42)
        crash_bot = TradingBot(crash_cfg, bot_seed=42)
        
        calm_events = [calm_bot.next_event() for _ in range(1000)]
        crash_events = [crash_bot.next_event() for _ in range(1000)]
        
        calm_types = Counter(e.event_type for e in calm_events if e)
        crash_types = Counter(e.event_type for e in crash_events if e)
        
        # FLASH_CRASH market order ratio is 0.50, CALM is 0.05
        # Momentum trader doubles this ratio.
        self.assertTrue(crash_types[EventType.MARKET_ORDER] > calm_types[EventType.MARKET_ORDER] * 2)

if __name__ == '__main__':
    unittest.main()
