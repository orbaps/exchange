import os
import json
import hashlib
from typing import Dict, Any, Optional

class SnapshotManager:
    """Manages creation, loading, and checksum verification of cluster state snapshots."""

    def __init__(self, store_dir: str = "federation_run_snapshots"):
        self.store_dir: str = store_dir
        os.makedirs(self.store_dir, exist_ok=True)

    def _get_filepath(self, snapshot_id: str) -> str:
        return os.path.join(self.store_dir, f"snapshot_{snapshot_id}.json")

    def _calculate_checksum(self, last_included_index: int, last_included_term: int, state: Dict[str, Any]) -> str:
        serialized_state = json.dumps(state, sort_keys=True)
        payload = f"{last_included_index}:{last_included_term}:{serialized_state}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def create_snapshot(self, snapshot_id: str, state: Dict[str, Any], last_included_index: int, last_included_term: int) -> str:
        """Create a state snapshot and write it to disk."""
        filepath = self._get_filepath(snapshot_id)
        checksum = self._calculate_checksum(last_included_index, last_included_term, state)
        
        snapshot_data = {
            "snapshot_id": snapshot_id,
            "last_included_index": last_included_index,
            "last_included_term": last_included_term,
            "state": state,
            "checksum": checksum
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2, sort_keys=True)
            
        return filepath

    def load_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Load a state snapshot from disk and verify its integrity."""
        filepath = self._get_filepath(snapshot_id)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Snapshot file not found: {filepath}")
            
        with open(filepath, "r", encoding="utf-8") as f:
            snapshot_data = json.load(f)
            
        # Verify checksum
        calculated = self._calculate_checksum(
            snapshot_data["last_included_index"],
            snapshot_data["last_included_term"],
            snapshot_data["state"]
        )
        if snapshot_data["checksum"] != calculated:
            raise ValueError(
                f"Snapshot corruption detected: expected checksum '{snapshot_data['checksum']}', "
                f"but calculated '{calculated}'."
            )
            
        return snapshot_data

    def verify_snapshot(self, snapshot_id: str) -> bool:
        """Verify the integrity of a snapshot on disk."""
        try:
            self.load_snapshot(snapshot_id)
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """Remove all snapshot files in the store directory."""
        if os.path.exists(self.store_dir):
            for file in os.listdir(self.store_dir):
                if file.startswith("snapshot_") and file.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.store_dir, file))
                    except OSError:
                        pass
