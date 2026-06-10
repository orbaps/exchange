import concurrent.futures
from typing import List, Dict, Tuple
import time

from botfleet.config import FleetConfig, BotConfig
from botfleet.events import TradingEvent
from botfleet.worker import BotWorker

def _run_worker(worker_id: int, configs: List[BotConfig], worker_seed: int, duration_seconds: float) -> List[TradingEvent]:
    worker = BotWorker(worker_id, configs)
    events = []
    for chunk in worker.generate_events(worker_seed, duration_seconds):
        events.extend(chunk)
    return events

class BotOrchestrator:
    """Manages the BotFleet by splitting load across workers."""
    
    def __init__(self, fleet_config: FleetConfig, num_workers: int = 4):
        self.fleet_config = fleet_config
        self.num_workers = num_workers
        
    def generate_fleet_events(self) -> Tuple[List[TradingEvent], float]:
        """Runs the generation using multiprocessing. Returns events and runtime_ms."""
        start_time = time.perf_counter()
        
        # Partition bots across workers
        bots_per_worker = max(1, self.fleet_config.num_bots // self.num_workers)
        
        strategies = ["RandomTrader", "MarketMaker", "MomentumTrader", "NoiseTrader"]
        
        worker_tasks = []
        for w in range(self.num_workers):
            start_idx = w * bots_per_worker
            # Last worker takes any remaining bots
            end_idx = self.fleet_config.num_bots if w == self.num_workers - 1 else (w + 1) * bots_per_worker
            
            worker_configs = []
            for b in range(start_idx, end_idx):
                strat = strategies[b % len(strategies)]
                worker_configs.append(BotConfig(
                    bot_id=f"bot_{b}",
                    strategy=strat,
                    order_rate=self.fleet_config.events_per_second / self.fleet_config.num_bots,
                    max_position=100,
                    instrument="BTC-USD",
                    regime=self.fleet_config.regime
                ))
            
            worker_seed = self.fleet_config.seed + w
            worker_tasks.append((w, worker_configs, worker_seed, self.fleet_config.duration_seconds))
            
        all_events = []
        # Use ProcessPoolExecutor to generate load concurrently
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [
                executor.submit(_run_worker, w_id, cfgs, w_seed, dur)
                for (w_id, cfgs, w_seed, dur) in worker_tasks
                if cfgs
            ]
            
            for future in concurrent.futures.as_completed(futures):
                all_events.extend(future.result())
                
        # Master sort
        all_events.sort(key=lambda e: (e.timestamp_ns, e.bot_id))
        
        runtime_ms = (time.perf_counter() - start_time) * 1000.0
        return all_events, runtime_ms
