import os
import json
import hashlib
from typing import List, Dict, Any
from federation.clock import global_clock

class CheckpointManager:
    """Manages full system checkpoints (registry, scheduler, and locks) and controls snapshot triggering."""

    SNAPSHOT_INTERVAL_EVENTS: int = 1000
    SNAPSHOT_INTERVAL_SECONDS: float = 300.0

    def __init__(self, store_dir: str = "federation_run_checkpoints"):
        self.store_dir: str = store_dir
        os.makedirs(self.store_dir, exist_ok=True)
        self.last_snapshot_time: float = global_clock.now()
        self.last_snapshot_events: int = 0

    def _get_filepath(self, checkpoint_id: str) -> str:
        return os.path.join(self.store_dir, f"checkpoint_{checkpoint_id}.json")

    def _calculate_checksum(self, registry_state: List[Dict[str, Any]], scheduler_state: Dict[str, Any], locks_state: Dict[str, Any]) -> str:
        serialized_registry = json.dumps(registry_state, sort_keys=True)
        serialized_scheduler = json.dumps(scheduler_state, sort_keys=True)
        serialized_locks = json.dumps(locks_state, sort_keys=True)
        payload = f"{serialized_registry}:{serialized_scheduler}:{serialized_locks}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def create_checkpoint(self, checkpoint_id: str, registry_state: List[Dict[str, Any]], scheduler_state: Dict[str, Any], locks_state: Dict[str, Any]) -> str:
        """Create a checkpoint file holding the complete state of registry, scheduler and locks."""
        filepath = self._get_filepath(checkpoint_id)
        checksum = self._calculate_checksum(registry_state, scheduler_state, locks_state)
        
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "timestamp": global_clock.now(),
            "registry_state": registry_state,
            "scheduler_state": scheduler_state,
            "locks_state": locks_state,
            "checksum": checksum
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, sort_keys=True)
            
        return filepath

    def load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Load and verify a checkpoint from disk."""
        filepath = self._get_filepath(checkpoint_id)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Checkpoint file not found: {filepath}")
            
        with open(filepath, "r", encoding="utf-8") as f:
            checkpoint_data = json.load(f)
            
        # Verify checksum
        calculated = self._calculate_checksum(
            checkpoint_data["registry_state"],
            checkpoint_data["scheduler_state"],
            checkpoint_data["locks_state"]
        )
        if checkpoint_data["checksum"] != calculated:
            raise ValueError(
                f"Checkpoint integrity validation failed: expected checksum '{checkpoint_data['checksum']}', "
                f"but calculated '{calculated}'."
            )
            
        return checkpoint_data

    def should_trigger_snapshot(self, current_events: int, current_time: float) -> bool:
        """Evaluate if snapshot thresholds have been crossed."""
        events_diff = current_events - self.last_snapshot_events
        time_diff = current_time - self.last_snapshot_time
        
        if events_diff >= self.SNAPSHOT_INTERVAL_EVENTS or time_diff >= self.SNAPSHOT_INTERVAL_SECONDS:
            return True
        return False

    def update_snapshot_anchor(self, current_events: int, current_time: float) -> None:
        """Anchor the last snapshot event count and timestamp after a snapshot operation."""
        self.last_snapshot_events = current_events
        self.last_snapshot_time = current_time

    def clear(self) -> None:
        """Remove all checkpoint files in the store directory."""
        if os.path.exists(self.store_dir):
            for file in os.listdir(self.store_dir):
                if file.startswith("checkpoint_") and file.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.store_dir, file))
                    except OSError:
                        pass
