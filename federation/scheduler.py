import random
import hashlib
from typing import List, Dict, Any, Optional
from federation.models import NodeInfo, NodeRole
from federation.jobs import DistributedJob, JobStatus

class DistributedScheduler:
    """Deterministic scheduler for assigning execution jobs to federation worker nodes."""
    
    def __init__(self):
        self._rr_counter = 0

    def assign_work(
        self,
        job: DistributedJob,
        active_nodes: List[NodeInfo],
        mode: str = "ROUND_ROBIN",
        seed: int = 42
    ) -> Optional[str]:
        """
        Deterministically assign a job to a node from a list of active nodes.
        Returns the node_id of the assigned node or None if no suitable node is found.
        """
        if not active_nodes:
            return None

        # Always sort nodes by node_id to preserve absolute determinism
        sorted_nodes = sorted(active_nodes, key=lambda n: n.node_id)
        mode = mode.upper()

        if mode == "ROUND_ROBIN":
            assigned_id = sorted_nodes[self._rr_counter % len(sorted_nodes)].node_id
            self._rr_counter += 1
            return assigned_id

        elif mode == "LEAST_LOADED":
            # Select the node with the lowest current load. Tie-break via node_id (implicit by sort)
            least_loaded_node = min(sorted_nodes, key=lambda n: n.load)
            return least_loaded_node.node_id

        elif mode == "CAPABILITY_MATCH":
            # Expect job payload to contain required domain in "category" or "domain"
            required_domain = job.payload.get("category") or job.payload.get("domain")
            if not required_domain:
                # Fallback to round robin if no specific capability requested
                return sorted_nodes[self._rr_counter % len(sorted_nodes)].node_id

            matching_nodes = [
                n for n in sorted_nodes
                if required_domain in n.capabilities.supported_domains
            ]
            if not matching_nodes:
                # Fallback to all nodes if no node supports it specifically, to prevent stalling
                matching_nodes = sorted_nodes
                
            # Pick least loaded matching node
            chosen_node = min(matching_nodes, key=lambda n: n.load)
            return chosen_node.node_id

        elif mode == "RANDOM_SEEDED":
            # Generate deterministic seed combining tournament seed + job_id hash
            job_hash = int(hashlib.sha256(job.job_id.encode("utf-8")).hexdigest(), 16)
            combined_seed = seed + (job_hash % 1000000)
            rng = random.Random(combined_seed)
            return rng.choice(sorted_nodes).node_id

        return None

    def rebalance(
        self,
        jobs: List[DistributedJob],
        active_nodes: List[NodeInfo]
    ) -> List[DistributedJob]:
        """
        Rebalances pending/assigned jobs among currently active nodes to match load constraints.
        Updates job.assigned_node_id and returns the updated jobs list.
        """
        if not active_nodes:
            # Clear assignments if no nodes are active
            for job in jobs:
                if job.status in (JobStatus.PENDING, JobStatus.ASSIGNED):
                    job.assigned_node_id = None
                    job.status = JobStatus.PENDING
            return jobs

        sorted_nodes = sorted(active_nodes, key=lambda n: n.node_id)
        
        # We reassign PENDING/ASSIGNED jobs to achieve a balanced load
        # For simplicity, assign jobs sequentially to nodes
        idx = 0
        for job in jobs:
            if job.status in (JobStatus.PENDING, JobStatus.ASSIGNED):
                job.assigned_node_id = sorted_nodes[idx % len(sorted_nodes)].node_id
                job.status = JobStatus.ASSIGNED
                idx += 1
        return jobs

    def cancel(self, job: DistributedJob) -> bool:
        if job.status in (JobStatus.PENDING, JobStatus.ASSIGNED, JobStatus.RUNNING, JobStatus.RETRYING):
            job.status = JobStatus.CANCELLED
            return True
        return False

    def retry(self, job: DistributedJob) -> bool:
        if job.status in (JobStatus.FAILED, JobStatus.RETRYING):
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.RETRYING
                return True
            else:
                job.status = JobStatus.FAILED
        return False
