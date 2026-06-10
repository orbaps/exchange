import time
from botfleet.config import FleetConfig
from botfleet.orderflow import MarketRegime
from botfleet.orchestrator import BotOrchestrator

def run_stress_test():
    print("Starting 10 Million Event BotFleet Stress Test...")
    
    config = FleetConfig(
        num_bots=10000,
        duration_seconds=100.0,
        events_per_second=100000.0, # 100 seconds * 100k eps = 10 million events
        seed=42,
        regime=MarketRegime.VOLATILE
    )
    
    orch = BotOrchestrator(config, num_workers=4)
    events, runtime_ms = orch.generate_fleet_events()
    
    print(f"Generated {len(events)} events.")
    print(f"Generation took: {runtime_ms / 1000.0:.2f} seconds.")
    print(f"Throughput: {len(events) / (runtime_ms / 1000.0):.2f} events/second.")
    
    # Just inspect the last few events
    for e in events[-3:]:
        print(e)
        
if __name__ == '__main__':
    run_stress_test()
