import time
import random
import hashlib
from typing import Dict, Any, Optional, List, Tuple

from federation.security import FederationVerifier
from federation.registry import FederationRegistry
from federation.models import NodeInfo, NodeCapabilities, NodeRole
from federation.jobs import DistributedJob, JobStatus, JobResult
from federation.clock import global_clock
from federation.replication.messages import TransportEnvelope

class FederationServer:
    """Simulated cluster entrypoint verifying cryptographic signatures before routing requests."""
    
    def __init__(self, registry: FederationRegistry, public_keys: Optional[Dict[str, str]] = None):
        self.registry = registry
        self.public_keys = public_keys or {}  # node_id -> PEM public key
        self.received_jobs: List[DistributedJob] = []

    def set_node_key(self, node_id: str, public_key_pem: str):
        self.public_keys[node_id] = public_key_pem

    def handle_register(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_id = envelope.get("node_id")
        pub_key = envelope.get("payload", {}).get("public_key") or self.public_keys.get(node_id)
        
        if not pub_key:
            return {"status": "ERROR", "message": "Missing public key for verification"}
            
        # Register public key for future verification
        self.set_node_key(node_id, pub_key)
        
        # Verify signature
        if not FederationVerifier.verify_message(envelope, pub_key):
            return {"status": "ERROR", "message": "Invalid cryptographic signature"}
            
        # Parse payload
        payload = envelope["payload"]
        caps = payload.get("capabilities", {})
        capabilities = NodeCapabilities(
            supported_domains=caps.get("supported_domains", []),
            max_concurrent_jobs=caps.get("max_concurrent_jobs", 4),
            memory_mb=caps.get("memory_mb", 8192.0),
            cpu_cores=caps.get("cpu_cores", 4)
        )
        
        roles = [NodeRole(r) for r in payload.get("roles", [])]
        node = NodeInfo(
            node_id=node_id,
            hostname=payload["hostname"],
            version=payload.get("version", "1.0.0"),
            public_key=pub_key,
            roles=roles,
            capabilities=capabilities,
            registered_at=int(time.time()),
            last_seen=int(time.time())
        )
        
        self.registry.register_node(node)
        return {"status": "SUCCESS", "message": "Registration successful"}

    def handle_heartbeat(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_id = envelope.get("node_id")
        pub_key = self.public_keys.get(node_id)
        
        if not pub_key:
            return {"status": "ERROR", "message": "Node public key not registered"}
            
        if not FederationVerifier.verify_message(envelope, pub_key):
            return {"status": "ERROR", "message": "Invalid cryptographic signature"}
            
        payload = envelope.get("payload", {})
        load = payload.get("load", 0.0)
        
        success = self.registry.heartbeat(node_id, load)
        if success:
            return {"status": "SUCCESS"}
        return {"status": "ERROR", "message": "Node heartbeat failed"}

    def handle_job_dispatch(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_id = envelope.get("node_id")
        pub_key = self.public_keys.get(node_id)
        
        if not pub_key:
            return {"status": "ERROR", "message": "Node public key not registered"}
            
        if not FederationVerifier.verify_message(envelope, pub_key):
            return {"status": "ERROR", "message": "Invalid cryptographic signature"}
            
        payload = envelope.get("payload", {})
        job_id = payload.get("job_id")
        task_type = payload.get("task_type")
        payload_data = payload.get("payload_data", {})
        
        job = DistributedJob(
            job_id=job_id,
            task_type=task_type,
            payload=payload_data,
            status=JobStatus.ASSIGNED,
            assigned_node_id=node_id,
            created_at=int(time.time())
        )
        self.received_jobs.append(job)
        return {"status": "SUCCESS", "message": f"Job {job.job_id} dispatched to runner"}


class FederationClient:
    """Outbound cluster client wrapping payload envelopes in security signatures."""
    
    def __init__(self, node_id: str, private_key_pem: str):
        self.node_id = node_id
        self.private_key_pem = private_key_pem

    def register_payload(self, hostname: str, roles: List[NodeRole], capabilities: NodeCapabilities, public_key_pem: str) -> Dict[str, Any]:
        payload = {
            "hostname": hostname,
            "roles": [r.value for r in roles],
            "version": "1.0.0",
            "public_key": public_key_pem,
            "capabilities": {
                "supported_domains": capabilities.supported_domains,
                "max_concurrent_jobs": capabilities.max_concurrent_jobs,
                "memory_mb": capabilities.memory_mb,
                "cpu_cores": capabilities.cpu_cores
            }
        }
        return FederationVerifier.sign_message(self.node_id, self.private_key_pem, payload)

    def heartbeat_payload(self, load: float = 0.0) -> Dict[str, Any]:
        payload = {
            "load": load
        }
        return FederationVerifier.sign_message(self.node_id, self.private_key_pem, payload)

    def dispatch_job_payload(self, job_id: str, task_type: str, payload_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "job_id": job_id,
            "task_type": task_type,
            "payload_data": payload_data
        }
        return FederationVerifier.sign_message(self.node_id, self.private_key_pem, payload)


# ── Phase 7.2 Network Simulator Extensions ─────────────────────────────────────

class LinkProperties:
    """Directional link parameters for latency, drops, and blockages."""
    def __init__(self, latency: float = 0.0, drop_rate: float = 0.0, blocked: bool = False):
        self.latency: float = latency
        self.drop_rate: float = drop_rate
        self.blocked: bool = blocked

class DeterministicNetworkSimulator:
    """Deterministic, socketless network simulator modeling asymmetric/directional links and delay delivery."""

    def __init__(self, transport: Any):
        self.transport = transport
        self.transport.network_simulator = self
        self._links: Dict[Tuple[str, str], LinkProperties] = {}
        self._delivery_queue: List[Tuple[float, TransportEnvelope]] = []
        
        # Metrics tracking
        self.sent_packets: int = 0
        self.delivered_packets: int = 0
        self.dropped_packets: int = 0

    def set_link(self, from_node: str, to_node: str, latency: float = 0.0, drop_rate: float = 0.0, blocked: bool = False) -> None:
        """Configure parameters for a directional link from from_node to to_node."""
        self._links[(from_node, to_node)] = LinkProperties(latency, drop_rate, blocked)

    def get_link(self, from_node: str, to_node: str) -> LinkProperties:
        """Get directional link parameters, defaulting to a healthy, instant link."""
        return self._links.get((from_node, to_node), LinkProperties(0.0, 0.0, False))

    def route(self, envelope: TransportEnvelope) -> None:
        """Route the envelope through link simulation."""
        self.sent_packets += 1
        link = self.get_link(envelope.sender_id, envelope.receiver_id)
        
        if link.blocked:
            self.dropped_packets += 1
            return

        # Deterministic drop check based on message hash
        if link.drop_rate > 0.0:
            h = int(hashlib.sha256(envelope.message_id.encode("utf-8")).hexdigest(), 16)
            rng = random.Random(h % 1000000)
            if rng.random() < link.drop_rate:
                self.dropped_packets += 1
                return

        # Schedule delivery with injected latency
        delivery_time = global_clock.now() + link.latency
        self._delivery_queue.append((delivery_time, envelope))
        self._delivery_queue.sort(key=lambda x: x[0])

    def process_deliveries(self) -> int:
        """Deliver all messages that are due. Returns the count of delivered messages."""
        now = global_clock.now()
        delivered_count = 0
        
        to_deliver = []
        remaining = []
        for delivery_time, env in self._delivery_queue:
            if delivery_time <= now:
                to_deliver.append(env)
            else:
                remaining.append((delivery_time, env))
                
        self._delivery_queue = remaining
        
        for env in to_deliver:
            self.transport.deliver_immediately(env)
            self.delivered_packets += 1
            delivered_count += 1
            
        return delivered_count

    def clear(self) -> None:
        """Reset simulator state."""
        self._links.clear()
        self._delivery_queue.clear()
        self.sent_packets = 0
        self.delivered_packets = 0
        self.dropped_packets = 0
