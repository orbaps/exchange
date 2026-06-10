import json
import hashlib
import os
from typing import List
from analytics.events import AnalyticsEvent, AnalyticsEventType

class AnalyticsJournal:
    """Appends JSONL logs with canonical SHA256 validation to local disk."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        # Ensure dir exists
        os.makedirs(os.path.dirname(self.filepath) or '.', exist_ok=True)
        
    def write_events(self, events: List[AnalyticsEvent]) -> str:
        """Appends events to the journal and returns the canonical SHA256 hash of the appended chunk."""
        dicts = []
        with open(self.filepath, 'a') as f:
            for e in events:
                data = {
                    "event_id": e.event_id,
                    "timestamp_ns": e.timestamp_ns,
                    "event_type": e.event_type.value,
                    "source": e.source,
                    "payload": e.payload
                }
                dicts.append(data)
                f.write(json.dumps(data, sort_keys=True) + '\n')
                
        canonical_str = json.dumps(dicts, sort_keys=True)
        return hashlib.sha256(canonical_str.encode()).hexdigest()
