import json
import os
from typing import List


class HostingReplay:
    """Loads and re-emits hosting journal events for debugging and auditing."""

    @staticmethod
    def load(filepath: str) -> List[dict]:
        events = []
        if not os.path.exists(filepath):
            return events
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    events.append(json.loads(stripped))
        return events

    @staticmethod
    def filter_by_type(events: List[dict], event_type: str) -> List[dict]:
        return [e for e in events if e.get("event_type") == event_type]

    @staticmethod
    def filter_by_submission(events: List[dict], submission_id: str) -> List[dict]:
        return [e for e in events if e.get("submission_id") == submission_id]
