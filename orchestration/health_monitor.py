from typing import Dict, List, Any, Optional
from federation.health import ClusterHealth, ReplicaState
from orchestration.models import NodeOrchestrationMetrics

class HealthMonitor:
    """Monitors cluster replica nodes, computes pressure metrics, and tracks historical trends."""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.metrics_history: Dict[str, List[NodeOrchestrationMetrics]] = {}

    def record_metrics(self, metrics: NodeOrchestrationMetrics) -> None:
        """Record node metrics and keep historical metrics within sliding window size."""
        node_id = metrics.node_id
        if node_id not in self.metrics_history:
            self.metrics_history[node_id] = []
        
        history = self.metrics_history[node_id]
        history.append(metrics)
        if len(history) > self.window_size:
            history.pop(0)

    def calculate_health(self, node_id: str, replica_state: ReplicaState) -> Dict[str, float]:
        """
        Compute CPU pressure, memory pressure, and composite health score for a node.
        Returns:
            Dict containing cpu_pressure, memory_pressure, and health_score
        """
        history = self.metrics_history.get(node_id, [])
        if not history:
            return {
                "cpu_pressure": 0.0,
                "memory_pressure": 0.0,
                "health_score": 100.0
            }
        
        # Calculate sliding window average pressure
        avg_cpu = sum(m.cpu_usage for m in history) / len(history)
        avg_mem = sum(m.memory_usage for m in history) / len(history)
        avg_lag = sum(m.replication_lag for m in history) / len(history)
        
        # CPU/Mem pressure scores are the averages directly
        cpu_pressure = avg_cpu
        memory_pressure = avg_mem
        
        # Penalties:
        # 1. Replication lag penalty
        lag_penalty = min(50.0, avg_lag * 0.5)
        
        # 2. State penalty
        state_penalty = 0.0
        if replica_state == ReplicaState.PARTITIONED:
            state_penalty = 80.0
        elif replica_state == ReplicaState.LAGGING:
            state_penalty = 20.0
        elif replica_state == ReplicaState.SYNCING:
            state_penalty = 10.0
        elif replica_state == ReplicaState.RECOVERING:
            state_penalty = 30.0
            
        base_score = 100.0 - (cpu_pressure * 0.3 + memory_pressure * 0.3 + lag_penalty + state_penalty)
        health_score = max(0.0, min(100.0, base_score))
        
        return {
            "cpu_pressure": cpu_pressure,
            "memory_pressure": memory_pressure,
            "health_score": health_score
        }

    def update_cluster_health(self, cluster_health: ClusterHealth, active_anomalies_count: int = 0) -> None:
        """Aggregates individual node pressures into cluster-wide values and updates ClusterHealth."""
        total_cpu_pressure = 0.0
        total_mem_pressure = 0.0
        total_health_score = 0.0
        nodes_count = len(cluster_health.replica_states)
        
        node_health_states: Dict[str, str] = {}
        
        for node_id, state in cluster_health.replica_states.items():
            metrics_summary = self.calculate_health(node_id, state)
            cpu_p = metrics_summary["cpu_pressure"]
            mem_p = metrics_summary["memory_pressure"]
            h_score = metrics_summary["health_score"]
            
            total_cpu_pressure += cpu_p
            total_mem_pressure += mem_p
            total_health_score += h_score
            
            # Save node specific health status (HEALTHY, DEGRADED, CRITICAL)
            if h_score >= 80.0:
                node_health_states[node_id] = "HEALTHY"
            elif h_score >= 40.0:
                node_health_states[node_id] = "DEGRADED"
            else:
                node_health_states[node_id] = "CRITICAL"
        
        if nodes_count > 0:
            cluster_health.cpu_pressure_score = total_cpu_pressure / nodes_count
            cluster_health.memory_pressure_score = total_mem_pressure / nodes_count
            cluster_health.health_score = total_health_score / nodes_count
        else:
            cluster_health.cpu_pressure_score = 0.0
            cluster_health.memory_pressure_score = 0.0
            cluster_health.health_score = 100.0
            
        cluster_health.anomaly_count = active_anomalies_count
        cluster_health.node_health_states = node_health_states
