import json
import os
from typing import List
from analytics.events import AnalyticsEvent, AnalyticsEventType

class AnalyticsReplay:
    """Decodes JSONL streams to inject historical events identically back onto the bus."""
    
    @staticmethod
    def load_events(filepath: str) -> List[AnalyticsEvent]:
        events = []
        if not os.path.exists(filepath):
            return events
            
        with open(filepath, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                events.append(
                    AnalyticsEvent(
                        event_id=data["event_id"],
                        timestamp_ns=data["timestamp_ns"],
                        event_type=AnalyticsEventType(data["event_type"]),
                        source=data["source"],
                        payload=data["payload"]
                    )
                )
        return events
