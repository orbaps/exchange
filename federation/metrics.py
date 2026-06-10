from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class ConsensusMetrics:
    """Tracks performance and operational metrics of the replicated consensus layer."""
    sent_messages: int = 0
    received_messages: int = 0
    dropped_messages: int = 0
    election_events: int = 0
    snapshot_installations: int = 0
    snapshot_install_duration: float = 0.0
    membership_reconfigurations: int = 0
    lease_renewal_rate: float = 1.0
    commit_throughput: float = 0.0
    
    # Follower lag histogram: tracks frequency of lag sizes
    # Map node_id -> list of counts: [lag_0_to_2, lag_3_to_5, lag_6_to_10, lag_11_plus]
    follower_lag_histogram: Dict[str, List[int]] = field(default_factory=dict)
    
    # Live replication latency in virtual seconds
    replication_latency: Dict[str, float] = field(default_factory=dict)

    def record_lag(self, follower_id: str, lag: int) -> None:
        """Update the lag histogram for a specific follower."""
        if follower_id not in self.follower_lag_histogram:
            self.follower_lag_histogram[follower_id] = [0, 0, 0, 0]
            
        hist = self.follower_lag_histogram[follower_id]
        if lag <= 2:
            hist[0] += 1
        elif lag <= 5:
            hist[1] += 1
        elif lag <= 10:
            hist[2] += 1
        else:
            hist[3] += 1

    def record_latency(self, follower_id: str, latency: float) -> None:
        """Update replication latency metrics."""
        self.replication_latency[follower_id] = latency
