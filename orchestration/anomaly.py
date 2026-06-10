from typing import List, Dict, Tuple
from orchestration.models import AnomalyRecord, NodeOrchestrationMetrics

class AnomalyDetector:
    """Detects system resource anomalies, election storms, lag spikes, and cluster reconfigurations churn."""
    
    def __init__(self):
        self.anomaly_counter = 0

    def _next_id(self, prefix: str) -> str:
        self.anomaly_counter += 1
        return f"anom_{prefix}_{self.anomaly_counter}"

    def detect_anomalies(
        self,
        node_metrics: Dict[str, List[NodeOrchestrationMetrics]],
        election_timestamps: List[float],
        membership_change_timestamps: List[float],
        partition_toggle_counts: Dict[str, int],
        now: float
    ) -> List[AnomalyRecord]:
        """
        Analyze current metrics and events to detect active anomalies.
        """
        anomalies = []
        
        # 1. Analyze resource metrics per node
        for node_id, history in node_metrics.items():
            if not history:
                continue
            
            latest = history[-1]
            
            # CPU Spike Check
            if latest.cpu_usage > 90.0:
                anomalies.append(AnomalyRecord(
                    anomaly_id=self._next_id("cpu"),
                    node_id=node_id,
                    type="CPU_SPIKE",
                    severity="HIGH",
                    timestamp=latest.timestamp,
                    details=f"CPU usage at {latest.cpu_usage}% exceeds critical threshold of 90%"
                ))
            elif len(history) >= 2:
                prev = history[-2]
                cpu_delta = latest.cpu_usage - prev.cpu_usage
                if cpu_delta > 50.0:
                    anomalies.append(AnomalyRecord(
                        anomaly_id=self._next_id("cpu"),
                        node_id=node_id,
                        type="CPU_SPIKE",
                        severity="MEDIUM",
                        timestamp=latest.timestamp,
                        details=f"CPU usage surged abruptly by {cpu_delta}% in one interval (from {prev.cpu_usage}% to {latest.cpu_usage}%)"
                    ))
            
            # Memory Pressure Check
            if latest.memory_usage > 90.0:
                anomalies.append(AnomalyRecord(
                    anomaly_id=self._next_id("mem"),
                    node_id=node_id,
                    type="MEM_PRESSURE",
                    severity="HIGH",
                    timestamp=latest.timestamp,
                    details=f"Memory usage at {latest.memory_usage}% exceeds critical threshold of 90%"
                ))
            elif latest.memory_usage > 80.0:
                anomalies.append(AnomalyRecord(
                    anomaly_id=self._next_id("mem"),
                    node_id=node_id,
                    type="MEM_PRESSURE",
                    severity="MEDIUM",
                    timestamp=latest.timestamp,
                    details=f"Memory usage is high at {latest.memory_usage}%"
                ))
            
            # Replication Lag Check
            if latest.replication_lag > 100:
                anomalies.append(AnomalyRecord(
                    anomaly_id=self._next_id("replag"),
                    node_id=node_id,
                    type="REP_LAG",
                    severity="HIGH",
                    timestamp=latest.timestamp,
                    details=f"Replication lag of {latest.replication_lag} log entries exceeds warning threshold of 100"
                ))
            elif latest.replication_lag > 20:
                anomalies.append(AnomalyRecord(
                    anomaly_id=self._next_id("replag"),
                    node_id=node_id,
                    type="REP_LAG",
                    severity="MEDIUM",
                    timestamp=latest.timestamp,
                    details=f"Replication lag is elevated at {latest.replication_lag} entries"
                ))
            
            # Partition Instability Check
            toggles = partition_toggle_counts.get(node_id, 0)
            if toggles > 3:
                anomalies.append(AnomalyRecord(
                    anomaly_id=self._next_id("part"),
                    node_id=node_id,
                    type="PARTITION_INSTABILITY",
                    severity="HIGH",
                    timestamp=latest.timestamp,
                    details=f"Partition toggled {toggles} times, indicating flapping connection stability"
                ))

        # 2. Election Storm Check
        recent_elections = [t for t in election_timestamps if now - t <= 30.0]
        if len(recent_elections) > 3:
            anomalies.append(AnomalyRecord(
                anomaly_id=self._next_id("storm"),
                node_id="cluster",
                type="ELECTION_STORM",
                severity="HIGH",
                timestamp=now,
                details=f"Detected election storm with {len(recent_elections)} elections within 30 virtual seconds"
            ))

        # 3. Membership Churn Check
        recent_changes = [t for t in membership_change_timestamps if now - t <= 100.0]
        if len(recent_changes) > 2:
            anomalies.append(AnomalyRecord(
                anomaly_id=self._next_id("churn"),
                node_id="cluster",
                type="MEMB_CHURN",
                severity="HIGH",
                timestamp=now,
                details=f"Detected high configuration membership churn: {len(recent_changes)} changes within 100 virtual seconds"
            ))

        return anomalies
