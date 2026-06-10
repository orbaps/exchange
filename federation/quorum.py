from typing import List

class QuorumManager:
    """Manages quorum calculations, split-brain detection, and partition capability validation."""

    @staticmethod
    def calculate_quorum(total_count: int) -> int:
        """Calculate the quorum size (majority) for a given total node count."""
        if total_count <= 0:
            return 0
        return (total_count // 2) + 1

    def is_quorum_present(self, active_nodes: List[str], total_nodes: List[str]) -> bool:
        """Check if active nodes constitute a quorum of the total nodes."""
        quorum_needed = self.calculate_quorum(len(total_nodes))
        # Filter active_nodes to only count valid cluster members
        valid_active = [n for n in active_nodes if n in total_nodes]
        return len(valid_active) >= quorum_needed

    def is_majority_partition(self, partition_nodes: List[str], total_nodes: List[str]) -> bool:
        """Determine if a partition group has Read + Write capabilities (has quorum majority)."""
        return self.is_quorum_present(partition_nodes, total_nodes)

    def detect_split_brain(self, partition_a: List[str], partition_b: List[str], total_nodes: List[str]) -> bool:
        """
        Detect if a split-brain condition could occur.
        Returns True if a partition is disjoint such that no single partition contains a strict majority,
        which prevents any partition from obtaining write permission (hence preventing split-brain writes).
        """
        # If the partitions overlap, it's not a clean partition.
        overlap = set(partition_a).intersection(set(partition_b))
        if overlap:
            return False
            
        has_majority_a = self.is_majority_partition(partition_a, total_nodes)
        has_majority_b = self.is_majority_partition(partition_b, total_nodes)
        
        # If neither has a majority, split-brain writing is prevented, but quorum is lost.
        # If both somehow have a majority (mathematically impossible if disjoint), return True.
        if has_majority_a and has_majority_b:
            return True
            
        return False

    def validate_leader(self, leader_id: str, active_nodes: List[str], total_nodes: List[str]) -> bool:
        """Validate if the current leader resides within a partition that has active quorum."""
        if leader_id not in active_nodes:
            return False
        return self.is_quorum_present(active_nodes, total_nodes)
