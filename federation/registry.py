import time
import threading
from typing import Dict, List, Optional
from analytics.bus import AnalyticsEventBus
from analytics.events import AnalyticsEvent, AnalyticsEventType
from federation.models import NodeInfo, NodeRole

class FederationRegistry:
    """Thread-safe registry for tracking active federation nodes and their roles/capabilities."""
    
    def __init__(self, analytics_bus: Optional[AnalyticsEventBus] = None):
        self.analytics_bus = analytics_bus
        self._nodes: Dict[str, NodeInfo] = {}
        self._lock = threading.Lock()
        self.heartbeat_timeout = 30.0  # 30 seconds

    def _publish_event(self, event_type: AnalyticsEventType, payload: dict):
        if self.analytics_bus:
            evt = AnalyticsEvent(
                event_id=f"evt_fed_{time.time_ns()}",
                timestamp_ns=time.time_ns(),
                event_type=event_type,
                source="FederationRegistry",
                payload=payload
            )
            self.analytics_bus.publish(evt)

    def register_node(self, node: NodeInfo) -> bool:
        with self._lock:
            is_new = node.node_id not in self._nodes
            node.last_seen = int(time.time())
            node.status = "ACTIVE"
            self._nodes[node.node_id] = node
            
        if is_new:
            self._publish_event(AnalyticsEventType.NODE_REGISTERED, {
                "node_id": node.node_id,
                "hostname": node.hostname,
                "roles": [r.value for r in node.roles],
                "version": node.version
            })
        return True

    def remove_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id in self._nodes:
                node = self._nodes.pop(node_id)
                self._publish_event(AnalyticsEventType.NODE_REMOVED, {
                    "node_id": node_id,
                    "hostname": node.hostname
                })
                return True
        return False

    def heartbeat(self, node_id: str, load: float = 0.0) -> bool:
        with self._lock:
            if node_id in self._nodes:
                node = self._nodes[node_id]
                node.last_seen = int(time.time())
                node.load = load
                node.status = "ACTIVE"
                
                self._publish_event(AnalyticsEventType.NODE_HEARTBEAT, {
                    "node_id": node_id,
                    "load": load
                })
                return True
        return False

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        with self._lock:
            node = self._nodes.get(node_id)
            if node and node.status == "ACTIVE":
                return node
        return None

    def list_nodes(self) -> List[NodeInfo]:
        with self._lock:
            return [n for n in self._nodes.values() if n.status == "ACTIVE"]

    def discover_nodes(self, role: Optional[NodeRole] = None) -> List[NodeInfo]:
        with self._lock:
            res = []
            for n in self._nodes.values():
                if n.status == "ACTIVE":
                    if role is None or role in n.roles:
                        res.append(n)
            return res

    def cleanup_expired_nodes(self) -> List[str]:
        now = int(time.time())
        expired_ids = []
        with self._lock:
            for node_id, node in list(self._nodes.items()):
                if now - node.last_seen > self.heartbeat_timeout:
                    node.status = "EXPIRED"
                    self._nodes.pop(node_id)
                    expired_ids.append(node_id)
                    
        for node_id in expired_ids:
            self._publish_event(AnalyticsEventType.NODE_REMOVED, {
                "node_id": node_id,
                "reason": "heartbeat_timeout"
            })
        return expired_ids
