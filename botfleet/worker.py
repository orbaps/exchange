from typing import List
from botfleet.config import BotConfig
from botfleet.bot import TradingBot
from botfleet.events import TradingEvent

class BotWorker:
    """Executes a subset of bots to generate an event stream deterministically."""
    
    def __init__(self, worker_id: int, configs: List[BotConfig]):
        self.worker_id = worker_id
        self.configs = configs
        
    def generate_events(self, worker_seed: int, duration_seconds: float):
        """
        Generates events deterministically using Poisson arrivals.
        Yields batches of events to avoid memory explosion.
        """
        from botfleet.orderflow import OrderFlowManager
        bots = []
        for idx, cfg in enumerate(self.configs):
            bot_seed = worker_seed + idx
            bots.append(TradingBot(cfg, bot_seed))
            
        all_bot_events = []
        for bot in bots:
            profile = OrderFlowManager.get_profile(bot.config.regime)
            effective_rate = bot.config.order_rate * profile.order_rate_multiplier
            if effective_rate <= 0:
                continue
                
            current_time_ns = int(bot.prng.random() * (1e9 / effective_rate))
            end_time_ns = int(duration_seconds * 1e9)
            
            while current_time_ns < end_time_ns:
                event = bot.next_event()
                if event:
                    event.timestamp_ns = current_time_ns
                    all_bot_events.append(event)
                
                # Poisson arrival
                interarrival_ns = int(bot.prng.expovariate(effective_rate) * 1e9)
                current_time_ns += max(1, interarrival_ns)
                
        all_bot_events.sort(key=lambda e: (e.timestamp_ns, e.bot_id))
        
        # Yield in chunks
        chunk_size = 10000
        for i in range(0, len(all_bot_events), chunk_size):
            yield all_bot_events[i:i+chunk_size]
