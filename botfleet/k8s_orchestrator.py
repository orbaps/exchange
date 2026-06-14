import os
import json
import signal
import sys
import time
from botfleet.config import FleetConfig
from botfleet.campaign import BotCampaign
from botfleet.orderflow import MarketRegime

SHUTDOWN = False

def handle_signal(signum, frame):
    global SHUTDOWN
    SHUTDOWN = True

def load_config() -> FleetConfig:
    config_path = os.getenv("FLEET_CONFIG_PATH", "/config/fleet-config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            data = json.load(f)
        return FleetConfig(
            num_bots=data.get("num_bots", 10),
            duration_seconds=data.get("duration_seconds", 30.0),
            events_per_second=data.get("events_per_second", 1000.0),
            seed=data.get("seed", 42),
            regime=MarketRegime[data.get("regime", "CALM").upper()],
        )
    return FleetConfig(
        num_bots=int(os.getenv("NUM_BOTS", "10")),
        duration_seconds=float(os.getenv("DURATION_SECONDS", "30.0")),
        events_per_second=float(os.getenv("EVENTS_PER_SECOND", "1000.0")),
        seed=int(os.getenv("SEED", "42")),
        regime=MarketRegime.CALM,
    )

def publish_to_kafka(events, bootstrap_servers: str, topic: str):
    try:
        from aiokafka import AIOKafkaProducer
        import asyncio
        from botfleet.events import TradingEvent

        async def send():
            producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
            await producer.start()
            try:
                for event in events:
                    payload = json.dumps(event.to_dict()).encode()
                    await producer.send(topic, payload)
                await producer.flush()
            finally:
                await producer.stop()

        asyncio.run(send())
    except ImportError:
        import warnings
        warnings.warn("aiokafka not available; skipping Kafka publish")

def main():
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    fleet_config = load_config()
    campaign = BotCampaign("k8s-fleet", fleet_config)
    start = time.perf_counter()
    result = campaign.execute()
    elapsed = time.perf_counter() - start

    print(f"Campaign {campaign.campaign_id}: "
          f"{result.total_events} events in {result.duration_seconds}s "
          f"(generation took {result.generation_runtime_ms:.1f}ms, "
          f"wall clock {elapsed:.2f}s)")

    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
    topic = os.getenv("RESULTS_TOPIC", "botfleet.results")
    if bootstrap and result.generated_events:
        publish_to_kafka(result.generated_events, bootstrap, topic)

    sys.exit(0)

if __name__ == "__main__":
    main()
