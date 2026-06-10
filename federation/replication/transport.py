import threading
from typing import Dict, Any, List, Optional
from federation.replication.messages import TransportEnvelope

class ConsensusTransport:
    """Thread-safe virtual transport layer for sequenced message routing and delivery without sockets."""

    def __init__(self):
        self._replicas: Dict[str, Any] = {}
        self._sequence_counter: int = 0
        self._lock = threading.Lock()
        self.network_simulator: Optional[Any] = None

    def register_node(self, node_id: str, replica: Any) -> None:
        """Register a replica node to handle incoming envelopes."""
        with self._lock:
            self._replicas[node_id] = replica

    def unregister_node(self, node_id: str) -> None:
        """Remove a replica node registration."""
        with self._lock:
            self._replicas.pop(node_id, None)

    def send(self, sender_id: str, receiver_id: str, message_type: str, payload: Any, term: int = 0, commit_index: int = 0) -> str:
        """Construct and send a sequenced transport envelope."""
        with self._lock:
            self._sequence_counter += 1
            seq_id = self._sequence_counter
            msg_id = f"msg_{sender_id}_{seq_id}"

        envelope = TransportEnvelope(
            message_id=msg_id,
            sequence_id=seq_id,
            origin_term=term,
            origin_commit_index=commit_index,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload
        )

        self.send_envelope(envelope)
        return msg_id

    def broadcast(self, sender_id: str, message_type: str, payload: Any, term: int = 0, commit_index: int = 0) -> List[str]:
        """Broadcast a sequenced envelope to all registered replica nodes except the sender."""
        with self._lock:
            receivers = [nid for nid in self._replicas.keys() if nid != sender_id]

        msg_ids = []
        for receiver_id in receivers:
            msg_id = self.send(sender_id, receiver_id, message_type, payload, term, commit_index)
            msg_ids.append(msg_id)
        return msg_ids

    def send_envelope(self, envelope: TransportEnvelope) -> None:
        """Route the envelope directly or delegate to the deterministic network simulator if present."""
        if self.network_simulator:
            self.network_simulator.route(envelope)
        else:
            self.deliver_immediately(envelope)

    def deliver_immediately(self, envelope: TransportEnvelope) -> None:
        """Deliver the envelope immediately bypass network delay/loss."""
        receiver_id = envelope.receiver_id
        with self._lock:
            replica = self._replicas.get(receiver_id)
        
        if replica and hasattr(replica, "receive_envelope"):
            replica.receive_envelope(envelope)
