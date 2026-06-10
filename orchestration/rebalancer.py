from typing import List, Dict, Any, Tuple
from federation.jobs import DistributedJob, JobStatus
from federation.models import NodeInfo

class WorkloadRebalancer:
    """Balances jobs across cluster nodes using Round Robin, Least Loaded, or Capacity Aware algorithms."""

    def rebalance_workload(
        self,
        jobs: List[Any],
        nodes: List[Any],
        mode: str = "ROUND_ROBIN"
    ) -> Tuple[List[Any], str]:
        """
        Rebalances PENDING or ASSIGNED jobs across the given active nodes.
        Returns a tuple of (updated_jobs, explanation_string).
        """
        if not nodes:
            # Clear assignments if no nodes are active
            for job in jobs:
                if hasattr(job, "status"):
                    if job.status in (JobStatus.PENDING, JobStatus.ASSIGNED):
                        job.assigned_node_id = None
                        job.status = JobStatus.PENDING
                elif isinstance(job, dict):
                    if job.get("status") in ("PENDING", "ASSIGNED"):
                        job["assigned_node_id"] = None
                        job["status"] = "PENDING"
            return jobs, "No active nodes available; cleared all assignments."

        # Sort nodes by node_id to maintain absolute determinism
        sorted_nodes = sorted(nodes, key=lambda n: getattr(n, "node_id", "") or n.get("node_id", ""))
        mode = mode.upper()
        
        # Prepare helper to read metric or default
        def get_node_id(node: Any) -> str:
            return getattr(node, "node_id", None) or node.get("node_id")

        def get_node_load(node: Any) -> float:
            return getattr(node, "load", 0.0) or node.get("load", 0.0)

        # 1. ROUND_ROBIN
        if mode == "ROUND_ROBIN":
            idx = 0
            for job in jobs:
                node = sorted_nodes[idx % len(sorted_nodes)]
                nid = get_node_id(node)
                if hasattr(job, "status"):
                    if job.status in (JobStatus.PENDING, JobStatus.ASSIGNED):
                        job.assigned_node_id = nid
                        job.status = JobStatus.ASSIGNED
                        idx += 1
                elif isinstance(job, dict):
                    if job.get("status") in ("PENDING", "ASSIGNED"):
                        job["assigned_node_id"] = nid
                        job["status"] = "ASSIGNED"
                        idx += 1
            explanation = f"Workload rebalanced using Round Robin algorithm across {len(nodes)} nodes."
            return jobs, explanation

        # 2. LEAST_LOADED
        elif mode == "LEAST_LOADED":
            # Track load per node in-memory during reassignment
            node_loads = {get_node_id(n): get_node_load(n) for n in sorted_nodes}
            
            for job in jobs:
                is_target = False
                if hasattr(job, "status") and job.status in (JobStatus.PENDING, JobStatus.ASSIGNED):
                    is_target = True
                elif isinstance(job, dict) and job.get("status") in ("PENDING", "ASSIGNED"):
                    is_target = True
                
                if is_target:
                    # Pick node with lowest load, tie-break on node_id (implicit by sorted_nodes)
                    chosen_nid = min(node_loads.keys(), key=lambda nid: node_loads[nid])
                    node_loads[chosen_nid] += 1.0  # Increment load for subsequent assignments
                    
                    if hasattr(job, "status"):
                        job.assigned_node_id = chosen_nid
                        job.status = JobStatus.ASSIGNED
                    else:
                        job["assigned_node_id"] = chosen_nid
                        job["status"] = "ASSIGNED"
            explanation = f"Workload rebalanced using Least Loaded algorithm. Final dynamic loads: {node_loads}."
            return jobs, explanation

        # 3. CAPACITY_AWARE
        elif mode == "CAPACITY_AWARE":
            # Remaining Capacity = memory * cores * (1.0 - load)
            node_caps = {}
            for n in sorted_nodes:
                nid = get_node_id(n)
                # Extract capacities
                cores = 4
                mem = 8192.0
                if hasattr(n, "capabilities"):
                    caps = n.capabilities
                    cores = getattr(caps, "cpu_cores", 4)
                    mem = getattr(caps, "memory_mb", 8192.0)
                elif isinstance(n, dict) and "capabilities" in n:
                    caps = n["capabilities"]
                    cores = caps.get("cpu_cores", 4)
                    mem = caps.get("memory_mb", 8192.0)
                
                load = get_node_load(n)
                # Compute starting capacity
                node_caps[nid] = mem * cores * (1.0 - min(0.99, load))

            for job in jobs:
                is_target = False
                if hasattr(job, "status") and job.status in (JobStatus.PENDING, JobStatus.ASSIGNED):
                    is_target = True
                elif isinstance(job, dict) and job.get("status") in ("PENDING", "ASSIGNED"):
                    is_target = True

                if is_target:
                    # Pick node with maximum remaining capacity
                    chosen_nid = max(node_caps.keys(), key=lambda nid: node_caps[nid])
                    # Deduct capacity for this assignment
                    node_caps[chosen_nid] = max(100.0, node_caps[chosen_nid] - 500.0)
                    
                    if hasattr(job, "status"):
                        job.assigned_node_id = chosen_nid
                        job.status = JobStatus.ASSIGNED
                    else:
                        job["assigned_node_id"] = chosen_nid
                        job["status"] = "ASSIGNED"
            explanation = f"Workload rebalanced using Capacity Aware algorithm. Final capacity indexes: {node_caps}."
            return jobs, explanation

        return jobs, f"Unsupported rebalancing mode {mode}. Workload left unmodified."
