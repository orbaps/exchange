from federation.clock import DeterministicClock
from strategic.models import ClusterProfile, OptimizationAlgorithm, OptimizationScore
from typing import List

class FederationOptimizer:
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def optimize_workload(self, clusters: List[ClusterProfile], algorithm: OptimizationAlgorithm) -> List[OptimizationScore]:
        scores = []
        for cluster in clusters:
            if algorithm == OptimizationAlgorithm.LEAST_LOADED:
                # Lower cpu/mem is better (higher score)
                score = 100.0 - ((cluster.cpu_utilization + cluster.memory_utilization) / 2.0)
                rationale = f"Avg load: {(cluster.cpu_utilization + cluster.memory_utilization) / 2.0}%"
            elif algorithm == OptimizationAlgorithm.CAPACITY_AWARE:
                # Favors clusters with more active nodes
                score = cluster.active_nodes * 10.0 - cluster.cpu_utilization
                rationale = f"Nodes: {cluster.active_nodes}, CPU: {cluster.cpu_utilization}%"
            elif algorithm == OptimizationAlgorithm.RISK_AWARE:
                # Penalizes bad health
                penalty = 50.0 if cluster.health_status != "HEALTHY" else 0.0
                score = 100.0 - cluster.cpu_utilization - penalty
                rationale = f"Health: {cluster.health_status}, Penalty: {penalty}"
            else:
                score = 0.0
                rationale = "Unknown algorithm"
                
            scores.append(OptimizationScore(cluster.cluster_id, score, algorithm, rationale))
            
        # Deterministic sort: score descending, then cluster_id ascending
        scores.sort(key=lambda x: (-x.score, x.cluster_id))
        return scores
