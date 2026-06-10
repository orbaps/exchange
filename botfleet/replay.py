import json
from typing import List
from botfleet.events import TradingEvent

class ReplayExporter:
    """Exports and imports bot fleet events to jsonl for deterministic replay."""
    
    @staticmethod
    def save_events(events: List[TradingEvent], filepath: str) -> None:
        with open(filepath, 'w') as f:
            for e in events:
                data = {
                    "event_id": e.event_id,
                    "timestamp_ns": e.timestamp_ns,
                    "bot_id": e.bot_id,
                    "instrument": e.instrument,
                    "event_type": e.event_type.value,
                    "quantity": e.quantity,
                    "price": e.price,
                    "side": e.side,
                    "order_id": e.order_id
                }
                f.write(json.dumps(data) + '\n')
                
    @staticmethod
    def load_events(filepath: str) -> List[TradingEvent]:
        from botfleet.events import EventType
        events = []
        with open(filepath, 'r') as f:
            for line in f:
                data = json.loads(line)
                events.append(TradingEvent(
                    event_id=data["event_id"],
                    timestamp_ns=data["timestamp_ns"],
                    bot_id=data["bot_id"],
                    instrument=data["instrument"],
                    event_type=EventType(data["event_type"]),
                    quantity=data["quantity"],
                    price=data["price"],
                    side=data["side"],
                    order_id=data.get("order_id")
                ))
        return events
