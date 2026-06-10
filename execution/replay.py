import json
import hashlib
from typing import List
from dataclasses import dataclass
from execution.events import ExecutionEvent

@dataclass
class ExecutionReplayResult:
    event_count: int
    success_count: int
    failure_count: int
    sha256: str

class ExecutionReplayExporter:
    """Exports and imports execution events for determinism and debugging."""
    
    @staticmethod
    def save_events(events: List[ExecutionEvent], filepath: str) -> ExecutionReplayResult:
        success = 0
        failure = 0
        dicts = []
        
        with open(filepath, 'w') as f:
            for e in events:
                if e.success:
                    success += 1
                else:
                    failure += 1
                    
                data = {
                    "event_id": e.event_id,
                    "execution_sequence_id": e.execution_sequence_id,
                    "worker_id": e.worker_id,
                    "session_id": e.session_id,
                    "dispatch_timestamp_ns": e.dispatch_timestamp_ns,
                    "completion_timestamp_ns": e.completion_timestamp_ns,
                    "success": e.success,
                    "error": e.error,
                    "trading_event_id": e.trading_event.event_id
                }
                dicts.append(data)
                f.write(json.dumps(data, sort_keys=True) + '\n')
                
        # Canonical hash
        canonical_str = json.dumps(dicts, sort_keys=True)
        h = hashlib.sha256(canonical_str.encode()).hexdigest()
        
        return ExecutionReplayResult(
            event_count=len(events),
            success_count=success,
            failure_count=failure,
            sha256=h
        )
