import os
import json
from typing import List, Dict, Any
from federation.models import NodeInfo

class DiscoveryService:
    """Manages static peer discovery and local network node announcements."""
    
    def __init__(self, bootstrap_peers_path: str = "federation_peers.json"):
        self.peers_path = bootstrap_peers_path
        self._static_peers: List[Dict[str, Any]] = []
        self._load_peers()

    def _load_peers(self):
        if os.path.exists(self.peers_path):
            try:
                with open(self.peers_path, "r") as f:
                    self._static_peers = json.load(f)
            except Exception:
                self._static_peers = []

    def announce(self, node_info: NodeInfo) -> bool:
        """Saves node info to the static discovery peer file."""
        self._load_peers()
        node_dict = {
            "node_id": node_info.node_id,
            "hostname": node_info.hostname,
            "version": node_info.version,
            "public_key": node_info.public_key,
            "roles": [r.value for r in node_info.roles],
            "capabilities": {
                "supported_domains": node_info.capabilities.supported_domains,
                "max_concurrent_jobs": node_info.capabilities.max_concurrent_jobs,
                "memory_mb": node_info.capabilities.memory_mb,
                "cpu_cores": node_info.capabilities.cpu_cores
            },
            "registered_at": node_info.registered_at,
            "last_seen": node_info.last_seen,
            "load": node_info.load,
            "status": node_info.status
        }
        
        updated = False
        for i, peer in enumerate(self._static_peers):
            if peer["node_id"] == node_info.node_id:
                self._static_peers[i] = node_dict
                updated = True
                break
        if not updated:
            self._static_peers.append(node_dict)
            
        try:
            with open(self.peers_path, "w") as f:
                json.dump(self._static_peers, f, indent=2)
            return True
        except Exception:
            return False

    def discover(self) -> List[Dict[str, Any]]:
        """Reads static peer list representing discovered nodes."""
        self._load_peers()
        return list(self._static_peers)

    def heartbeat(self, node_id: str) -> bool:
        self._load_peers()
        import time
        for peer in self._static_peers:
            if peer["node_id"] == node_id:
                peer["last_seen"] = int(time.time())
                peer["status"] = "ACTIVE"
                try:
                    with open(self.peers_path, "w") as f:
                        json.dump(self._static_peers, f, indent=2)
                    return True
                except Exception:
                    pass
        return False

    def validate(self, node_id: str) -> bool:
        self._load_peers()
        for peer in self._static_peers:
            if peer["node_id"] == node_id:
                return peer.get("status") == "ACTIVE"
        return False
