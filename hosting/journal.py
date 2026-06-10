import hashlib
import json
import os
from typing import List


class HostingJournal:
    """Append-only JSONL audit log for hosting lifecycle events.

    Every write returns a canonical SHA256 of the appended chunk, allowing
    the test suite to verify exact replay fidelity.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    def append(self, event_type: str, data: dict) -> str:
        """Append one event; return SHA256 of the line written."""
        record = {"event_type": event_type, **data}
        line   = json.dumps(record, sort_keys=True)
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return hashlib.sha256(line.encode()).hexdigest()

    def append_batch(self, events: List[dict]) -> str:
        """Append multiple events; return SHA256 of the entire batch."""
        lines = []
        with open(self.filepath, "a", encoding="utf-8") as f:
            for record in events:
                line = json.dumps(record, sort_keys=True)
                f.write(line + "\n")
                lines.append(line)
        canonical = json.dumps(events, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
