import os
import hashlib
from typing import Dict, Any, List, Optional
from analytics.bus import AnalyticsEventBus
from analytics.events import AnalyticsEvent, AnalyticsEventType

class ArtifactReplicator:
    """Handles secure replication, SHA256 integrity verification, and repair of competition assets."""
    
    def __init__(self, store_dir: str, analytics_bus: Optional[AnalyticsEventBus] = None):
        self.store_dir = store_dir
        self.analytics_bus = analytics_bus
        os.makedirs(self.store_dir, exist_ok=True)

    def _publish_event(self, event_type: AnalyticsEventType, payload: dict):
        if self.analytics_bus:
            import time
            evt = AnalyticsEvent(
                event_id=f"evt_rep_{time.time_ns()}",
                timestamp_ns=time.time_ns(),
                event_type=event_type,
                source="ArtifactReplicator",
                payload=payload
            )
            self.analytics_bus.publish(evt)

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def verify(self, data: bytes, expected_hash: str) -> bool:
        computed = self.compute_sha256(data)
        return computed == expected_hash

    def push(self, artifact_id: str, data: bytes, destination_node_id: str) -> bool:
        """Saves artifact locally (representing receipt of push) and validates hash."""
        h = self.compute_sha256(data)
        filepath = os.path.join(self.store_dir, artifact_id)
        
        with open(filepath, "wb") as f:
            f.write(data)
            
        self._publish_event(AnalyticsEventType.ARTIFACT_REPLICATED, {
            "artifact_id": artifact_id,
            "direction": "PUSH",
            "peer_node_id": destination_node_id,
            "size_bytes": len(data),
            "hash": h
        })
        return True

    def pull(self, artifact_id: str, source_node_id: str) -> Optional[bytes]:
        """Reads local artifact to send to a peer."""
        filepath = os.path.join(self.store_dir, artifact_id)
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, "rb") as f:
            data = f.read()
            
        h = self.compute_sha256(data)
        self._publish_event(AnalyticsEventType.ARTIFACT_REPLICATED, {
            "artifact_id": artifact_id,
            "direction": "PULL",
            "peer_node_id": source_node_id,
            "size_bytes": len(data),
            "hash": h
        })
        return data

    def get_local_manifest(self) -> Dict[str, str]:
        """Returns mapping of local artifact_id -> sha256 hash."""
        manifest = {}
        if not os.path.exists(self.store_dir):
            return manifest
            
        for f in os.listdir(self.store_dir):
            filepath = os.path.join(self.store_dir, f)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as file_obj:
                    data = file_obj.read()
                manifest[f] = self.compute_sha256(data)
        return manifest

    def sync(self, peer_node_id: str, peer_manifest: Dict[str, str]) -> List[str]:
        """
        Compares peer manifest with local manifest.
        Returns a list of artifact IDs that need to be pulled/synced from the peer.
        """
        local_manifest = self.get_local_manifest()
        out_of_sync = []
        
        for art_id, peer_hash in peer_manifest.items():
            if art_id not in local_manifest or local_manifest[art_id] != peer_hash:
                out_of_sync.append(art_id)
                
        self._publish_event(AnalyticsEventType.FEDERATION_SYNC_COMPLETED, {
            "peer_node_id": peer_node_id,
            "artifacts_out_of_sync_count": len(out_of_sync)
        })
        return out_of_sync

    def repair(self, artifact_id: str, correct_data: bytes) -> bool:
        """Overwrites local artifact with correct_data and verifies hash."""
        filepath = os.path.join(self.store_dir, artifact_id)
        with open(filepath, "wb") as f:
            f.write(correct_data)
        return True
