import time
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from dashboard.dependencies import get_state_cache
from dashboard.services.state_cache import StateCache

router = APIRouter(tags=["Federation Layer"])

# Pydantic Schemas
class NodeCapabilitiesSchema(BaseModel):
    supported_domains: List[str]
    max_concurrent_jobs: int
    memory_mb: float
    cpu_cores: int

class NodeInfoSchema(BaseModel):
    node_id: str
    hostname: str
    version: str
    public_key: str
    roles: List[str]
    capabilities: NodeCapabilitiesSchema
    registered_at: int
    last_seen: int
    load: float
    status: str

class DistributedJobSchema(BaseModel):
    job_id: str
    task_type: str
    payload: Dict[str, Any]
    status: str
    assigned_node_id: Optional[str] = None
    created_at: int
    started_at: Optional[int] = None
    completed_at: Optional[int] = None
    retry_count: int
    max_retries: int
    error: Optional[str] = None

class FederationRegisterRequest(BaseModel):
    node_id: str
    hostname: str
    version: str
    public_key: str
    roles: List[str]
    capabilities: NodeCapabilitiesSchema

class FederationRemoveRequest(BaseModel):
    node_id: str

class FederationSyncRequest(BaseModel):
    peer_node_id: str
    peer_manifest: Dict[str, str]

class FederationRepairRequest(BaseModel):
    artifact_id: str
    correct_data: str  # Hex or base64 or raw string

# ── Public Endpoints ─────────────────────────────────────────────────────────

@router.get("/api/public/federation/nodes", response_model=List[NodeInfoSchema])
async def get_nodes(cache: StateCache = Depends(get_state_cache)):
    nodes = cache.get_nodes()
    res = []
    for n in nodes:
        is_dict = isinstance(n, dict)
        caps_obj = n.get("capabilities", {}) if is_dict else getattr(n, "capabilities", None) or {}
        caps = {
            "supported_domains": caps_obj.get("supported_domains", []) if isinstance(caps_obj, dict) else getattr(caps_obj, "supported_domains", []),
            "max_concurrent_jobs": caps_obj.get("max_concurrent_jobs", 4) if isinstance(caps_obj, dict) else getattr(caps_obj, "max_concurrent_jobs", 4),
            "memory_mb": caps_obj.get("memory_mb", 8192.0) if isinstance(caps_obj, dict) else getattr(caps_obj, "memory_mb", 8192.0),
            "cpu_cores": caps_obj.get("cpu_cores", 4) if isinstance(caps_obj, dict) else getattr(caps_obj, "cpu_cores", 4),
        }
        raw_roles = n.get("roles", []) if is_dict else getattr(n, "roles", [])
        roles = [r.value if hasattr(r, "value") else str(r) for r in raw_roles]
        res.append({
            "node_id": n.get("node_id") if is_dict else getattr(n, "node_id", None),
            "hostname": n.get("hostname", "") if is_dict else getattr(n, "hostname", ""),
            "version": n.get("version", "") if is_dict else getattr(n, "version", ""),
            "public_key": n.get("public_key", "") if is_dict else getattr(n, "public_key", ""),
            "roles": roles,
            "capabilities": caps,
            "registered_at": n.get("registered_at", 0) if is_dict else getattr(n, "registered_at", 0),
            "last_seen": n.get("last_seen", 0) if is_dict else getattr(n, "last_seen", 0),
            "load": n.get("load", 0.0) if is_dict else getattr(n, "load", 0.0),
            "status": n.get("status", "ACTIVE") if is_dict else getattr(n, "status", "ACTIVE")
        })
    return res

@router.get("/api/public/federation/jobs", response_model=List[DistributedJobSchema])
async def get_jobs(cache: StateCache = Depends(get_state_cache)):
    jobs = cache.get_jobs()
    res = []
    for j in jobs:
        is_dict = isinstance(j, dict)
        status_val = j.get("status") if is_dict else getattr(j, "status", None)
        status_str = status_val.value if hasattr(status_val, "value") else str(status_val) if status_val else "PENDING"
        res.append({
            "job_id": j.get("job_id") if is_dict else getattr(j, "job_id", None),
            "task_type": j.get("task_type", "") if is_dict else getattr(j, "task_type", ""),
            "payload": j.get("payload", {}) if is_dict else getattr(j, "payload", {}) or {},
            "status": status_str,
            "assigned_node_id": j.get("assigned_node_id") if is_dict else getattr(j, "assigned_node_id", None),
            "created_at": j.get("created_at", 0) if is_dict else getattr(j, "created_at", 0),
            "started_at": j.get("started_at") if is_dict else getattr(j, "started_at", None),
            "completed_at": j.get("completed_at") if is_dict else getattr(j, "completed_at", None),
            "retry_count": j.get("retry_count", 0) if is_dict else getattr(j, "retry_count", 0),
            "max_retries": j.get("max_retries", 3) if is_dict else getattr(j, "max_retries", 3),
            "error": j.get("error") if is_dict else getattr(j, "error", None)
        })
    return res

@router.get("/api/public/federation/health")
async def get_health(cache: StateCache = Depends(get_state_cache)):
    health = cache.get_federation_health()
    if not health:
        return {"status": "HEALTHY", "node_count": len(cache.get_nodes()), "expired_pruned": 0}
    return health

@router.get("/api/public/federation/replay")
async def get_replay(cache: StateCache = Depends(get_state_cache)):
    replay_data = cache.get_federation_replay()
    if not replay_data:
        return {"timeline": [], "event_count": 0}
    return replay_data

@router.get("/api/public/federation/leaderboard")
async def get_leaderboard(cache: StateCache = Depends(get_state_cache)):
    lb = cache.get_federated_leaderboard()
    if not lb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No federated leaderboard merged snapshot available yet."
        )
    return lb

# ── Admin Endpoints ──────────────────────────────────────────────────────────

@router.post("/api/admin/federation/register")
async def admin_register(req: FederationRegisterRequest, cache: StateCache = Depends(get_state_cache)):
    from federation.models import NodeInfo, NodeCapabilities, NodeRole
    
    caps = NodeCapabilities(
        supported_domains=req.capabilities.supported_domains,
        max_concurrent_jobs=req.capabilities.max_concurrent_jobs,
        memory_mb=req.capabilities.memory_mb,
        cpu_cores=req.capabilities.cpu_cores
    )
    roles = [NodeRole(r) for r in req.roles]
    node = NodeInfo(
        node_id=req.node_id,
        hostname=req.hostname,
        version=req.version,
        public_key=req.public_key,
        roles=roles,
        capabilities=caps,
        registered_at=int(time.time()),
        last_seen=int(time.time())
    )
    
    cache.set_nodes([node])
    return {"status": "SUCCESS", "message": f"Node {req.node_id} manually registered by admin."}

@router.post("/api/admin/federation/remove")
async def admin_remove(req: FederationRemoveRequest, cache: StateCache = Depends(get_state_cache)):
    cache.remove_node_from_cache(req.node_id)
    return {"status": "SUCCESS", "message": f"Node {req.node_id} manually removed by admin."}

@router.post("/api/admin/federation/rebalance")
async def admin_rebalance(cache: StateCache = Depends(get_state_cache)):
    from federation.scheduler import DistributedScheduler
    from federation.models import NodeInfo
    
    jobs = cache.get_jobs()
    nodes = cache.get_nodes()
    
    scheduler = DistributedScheduler()
    node_infos = []
    for n in nodes:
        if isinstance(n, dict):
            from federation.models import NodeCapabilities, NodeRole
            caps = NodeCapabilities(**n["capabilities"])
            roles = [NodeRole(r) for r in n["roles"]]
            node_infos.append(NodeInfo(
                node_id=n["node_id"],
                hostname=n["hostname"],
                version=n["version"],
                public_key=n["public_key"],
                roles=roles,
                capabilities=caps,
                registered_at=n["registered_at"],
                last_seen=n["last_seen"],
                load=n["load"],
                status=n["status"]
            ))
        else:
            node_infos.append(n)
            
    job_objs = []
    for j in jobs:
        if isinstance(j, dict):
            from federation.jobs import JobStatus, DistributedJob
            job_objs.append(DistributedJob(
                job_id=j["job_id"],
                task_type=j["task_type"],
                payload=j["payload"],
                status=JobStatus(j["status"]),
                assigned_node_id=j["assigned_node_id"],
                created_at=j["created_at"],
                retry_count=j["retry_count"],
                max_retries=j["max_retries"],
                error=j["error"]
            ))
        else:
            job_objs.append(j)
            
    rebalanced = scheduler.rebalance(job_objs, node_infos)
    cache.set_jobs(rebalanced)
    
    return {"status": "SUCCESS", "message": "Jobs rebalanced across nodes."}

@router.post("/api/admin/federation/sync")
async def admin_sync(req: FederationSyncRequest, cache: StateCache = Depends(get_state_cache)):
    from federation.artifacts import ArtifactReplicator
    replicator = ArtifactReplicator(store_dir="federation_run_artifacts")
    out_of_sync = replicator.sync(req.peer_node_id, req.peer_manifest)
    
    sync_status = {
        "peer_node_id": req.peer_node_id,
        "out_of_sync_keys": out_of_sync,
        "status": "COMPLETED" if not out_of_sync else "PENDING_SYNC"
    }
    cache.set_replication_status(sync_status)
    return {"status": "SUCCESS", "out_of_sync": out_of_sync}

@router.post("/api/admin/federation/repair")
async def admin_repair(req: FederationRepairRequest, cache: StateCache = Depends(get_state_cache)):
    from federation.artifacts import ArtifactReplicator
    replicator = ArtifactReplicator(store_dir="federation_run_artifacts")
    
    data_bytes = req.correct_data.encode("utf-8")
    repaired = replicator.repair(req.artifact_id, data_bytes)
    
    rep_status = cache.get_replication_status() or {}
    rep_status["status"] = "REPAIRED"
    if "out_of_sync_keys" in rep_status and req.artifact_id in rep_status["out_of_sync_keys"]:
        rep_status["out_of_sync_keys"].remove(req.artifact_id)
    cache.set_replication_status(rep_status)
    
    return {"status": "SUCCESS", "repaired": repaired}

# ── HA & Consensus Endpoints ──────────────────────────────────────────────────

class AdminElectionRequest(BaseModel):
    node_id: Optional[str] = None

class AdminCheckpointRequest(BaseModel):
    checkpoint_id: str

class AdminRecoverRequest(BaseModel):
    wal_path: str
    snapshot_id: Optional[str] = None

class AdminLockRequest(BaseModel):
    lock_name: str
    client_id: str
    lease_duration: float

class AdminUnlockRequest(BaseModel):
    lock_name: str
    client_id: str

@router.get("/api/public/federation/leader")
async def get_federation_leader(cache: StateCache = Depends(get_state_cache)):
    leader_id = getattr(cache, "_current_leader", "node_1")
    term = getattr(cache, "_current_term", 1)
    state = getattr(cache, "_leader_state", "LEADER")
    return {
        "leader_id": leader_id,
        "term": term,
        "state": state
    }

@router.get("/api/public/federation/consensus")
async def get_federation_consensus(cache: StateCache = Depends(get_state_cache)):
    return {
        "term": getattr(cache, "_current_term", 1),
        "commit_index": getattr(cache, "_commit_index", 0),
        "last_applied": getattr(cache, "_last_applied", 0),
        "entries_count": getattr(cache, "_entries_count", 0),
        "replication_lag": getattr(cache, "_replication_lag", {})
    }

@router.get("/api/public/federation/quorum")
async def get_federation_quorum(cache: StateCache = Depends(get_state_cache)):
    return {
        "quorum_size": getattr(cache, "_quorum_size", 2),
        "quorum_present": getattr(cache, "_quorum_present", True),
        "active_nodes": getattr(cache, "_active_nodes", ["node_1", "node_2", "node_3"]),
        "total_nodes": getattr(cache, "_total_nodes", ["node_1", "node_2", "node_3"])
    }

@router.get("/api/public/federation/snapshots")
async def get_federation_snapshots(cache: StateCache = Depends(get_state_cache)):
    return getattr(cache, "_snapshots", [])

@router.get("/api/public/federation/recovery")
async def get_federation_recovery(cache: StateCache = Depends(get_state_cache)):
    return {
        "last_recovery_timestamp": getattr(cache, "_last_recovery_timestamp", 0.0),
        "recovery_events": getattr(cache, "_recovery_events", [])
    }

@router.post("/api/admin/federation/election")
async def admin_election(req: AdminElectionRequest, cache: StateCache = Depends(get_state_cache)):
    node_id = req.node_id or "node_1"
    cache._current_leader = node_id
    cache._leader_state = "LEADER"
    cache._current_term = getattr(cache, "_current_term", 0) + 1
    
    # Publish event
    from analytics.events import AnalyticsEventType
    from dashboard.dependencies import get_event_bridge
    bridge = get_event_bridge()
    if bridge and bridge.analytics_bus:
        from analytics.events import AnalyticsEvent
        evt = AnalyticsEvent(
            event_id=f"evt_elec_{int(time.time()*1000)}",
            timestamp_ns=int(time.time()*1e9),
            event_type=AnalyticsEventType.LEADER_ELECTED,
            source="AdminElection",
            payload={"leader_id": node_id, "term": cache._current_term}
        )
        bridge.analytics_bus.publish(evt)
        
    return {"status": "SUCCESS", "message": f"Election triggered. Node {node_id} elected leader."}

@router.post("/api/admin/federation/checkpoint")
async def admin_checkpoint(req: AdminCheckpointRequest, cache: StateCache = Depends(get_state_cache)):
    # Simulate checkpoint creation
    snapshots = getattr(cache, "_snapshots", [])
    snapshots.append({
        "snapshot_id": req.checkpoint_id,
        "last_included_index": getattr(cache, "_commit_index", 0),
        "last_included_term": getattr(cache, "_current_term", 1),
        "timestamp": time.time()
    })
    cache._snapshots = snapshots
    
    # Publish event
    from analytics.events import AnalyticsEventType
    from dashboard.dependencies import get_event_bridge
    bridge = get_event_bridge()
    if bridge and bridge.analytics_bus:
        from analytics.events import AnalyticsEvent
        evt = AnalyticsEvent(
            event_id=f"evt_chk_{int(time.time()*1000)}",
            timestamp_ns=int(time.time()*1e9),
            event_type=AnalyticsEventType.CHECKPOINT_CREATED,
            source="AdminCheckpoint",
            payload={"checkpoint_id": req.checkpoint_id}
        )
        bridge.analytics_bus.publish(evt)
        
    return {"status": "SUCCESS", "message": f"Checkpoint {req.checkpoint_id} created successfully."}

@router.post("/api/admin/federation/recover")
async def admin_recover(req: AdminRecoverRequest, cache: StateCache = Depends(get_state_cache)):
    # Simulate recovery
    cache._last_recovery_timestamp = time.time()
    events = getattr(cache, "_recovery_events", [])
    events.append({
        "event": "RECOVERY_COMPLETED",
        "timestamp": time.time(),
        "wal_path": req.wal_path,
        "snapshot_id": req.snapshot_id
    })
    cache._recovery_events = events
    
    # Publish event
    from analytics.events import AnalyticsEventType
    from dashboard.dependencies import get_event_bridge
    bridge = get_event_bridge()
    if bridge and bridge.analytics_bus:
        from analytics.events import AnalyticsEvent
        evt = AnalyticsEvent(
            event_id=f"evt_rec_{int(time.time()*1000)}",
            timestamp_ns=int(time.time()*1e9),
            event_type=AnalyticsEventType.RECOVERY_COMPLETED,
            source="AdminRecovery",
            payload={"wal_path": req.wal_path}
        )
        bridge.analytics_bus.publish(evt)
        
    return {"status": "SUCCESS", "message": f"Recovery completed from WAL {req.wal_path}."}

@router.post("/api/admin/federation/lock")
async def admin_lock(req: AdminLockRequest, cache: StateCache = Depends(get_state_cache)):
    locks = getattr(cache, "_active_locks", {})
    locks[req.lock_name] = {
        "client_id": req.client_id,
        "expires_at": time.time() + req.lease_duration
    }
    cache._active_locks = locks
    
    # Publish event
    from analytics.events import AnalyticsEventType
    from dashboard.dependencies import get_event_bridge
    bridge = get_event_bridge()
    if bridge and bridge.analytics_bus:
        from analytics.events import AnalyticsEvent
        evt = AnalyticsEvent(
            event_id=f"evt_lock_{int(time.time()*1000)}",
            timestamp_ns=int(time.time()*1e9),
            event_type=AnalyticsEventType.LOCK_ACQUIRED,
            source="AdminLock",
            payload={"lock_name": req.lock_name, "client_id": req.client_id}
        )
        bridge.analytics_bus.publish(evt)
        
    return {"status": "SUCCESS", "message": f"Lock {req.lock_name} acquired by {req.client_id}."}

@router.post("/api/admin/federation/unlock")
async def admin_unlock(req: AdminUnlockRequest, cache: StateCache = Depends(get_state_cache)):
    locks = getattr(cache, "_active_locks", {})
    if req.lock_name in locks:
        del locks[req.lock_name]
    cache._active_locks = locks
    
    # Publish event
    from analytics.events import AnalyticsEventType
    from dashboard.dependencies import get_event_bridge
    bridge = get_event_bridge()
    if bridge and bridge.analytics_bus:
        from analytics.events import AnalyticsEvent
        evt = AnalyticsEvent(
            event_id=f"evt_unl_{int(time.time()*1000)}",
            timestamp_ns=int(time.time()*1e9),
            event_type=AnalyticsEventType.LOCK_RELEASED,
            source="AdminUnlock",
            payload={"lock_name": req.lock_name, "client_id": req.client_id}
        )
        bridge.analytics_bus.publish(evt)
        
    return {"status": "SUCCESS", "message": f"Lock {req.lock_name} released."}

@router.get("/api/public/federation/replication")
async def get_replication_view(cache: StateCache = Depends(get_state_cache)):
    return {
        "match_indexes": getattr(cache, "_match_indexes", {}),
        "next_indexes": getattr(cache, "_next_indexes", {}),
        "replication_lag": getattr(cache, "_replication_lag", {}),
        "lease_expired": getattr(cache, "_lease_expired", False),
        "upgrade_policy": getattr(cache, "_upgrade_policy", "BACKWARD_COMPATIBLE")
    }

@router.get("/api/public/federation/topology")
async def get_topology_view(cache: StateCache = Depends(get_state_cache)):
    return {
        "replica_states": getattr(cache, "_replica_states", {"node_1": "HEALTHY", "node_2": "HEALTHY", "node_3": "HEALTHY"}),
        "partition_groups": getattr(cache, "_partition_groups", []),
        "link_properties": getattr(cache, "_link_properties", {})
    }

@router.get("/api/public/federation/membership")
async def get_membership_view(cache: StateCache = Depends(get_state_cache)):
    return {
        "config_state": getattr(cache, "_config_state", "STABLE"),
        "old_nodes": list(getattr(cache, "_old_nodes", ["node_1", "node_2", "node_3"])),
        "new_nodes": list(getattr(cache, "_new_nodes", [])),
        "reconfiguration_count": getattr(cache, "_reconfiguration_count", 0),
        "history": getattr(cache, "_membership_history", [])
    }

# ── Phase 8.0 Autonomous Orchestration & Self-Healing Endpoints ────────────────

class AdminPolicyRequest(BaseModel):
    policy_id: str
    name: str
    rule_expr: str
    action_type: str
    enabled: bool

class AdminHealRequest(BaseModel):
    node_id: str
    action_type: str

class AdminSimulateRequest(BaseModel):
    scenario: str
    node_id: Optional[str] = None
    metric: Optional[str] = None
    value: Optional[float] = None

@router.get("/api/public/orchestration/status")
async def get_orch_status(cache: StateCache = Depends(get_state_cache)):
    status_data = cache.get_orchestration_status()
    if not status_data:
        return {"status": "ACTIVE", "controller_active": True, "last_run_timestamp": 0.0}
    return status_data

@router.get("/api/public/orchestration/health")
async def get_orch_health(cache: StateCache = Depends(get_state_cache)):
    health_data = cache.get_orchestration_health()
    if not health_data:
        return {"health_score": 100.0, "cpu_pressure_score": 0.0, "memory_pressure_score": 0.0, "anomaly_count": 0}
    return health_data

@router.get("/api/public/orchestration/anomalies")
async def get_orch_anomalies(cache: StateCache = Depends(get_state_cache)):
    return cache.get_orchestration_anomalies()

@router.get("/api/public/orchestration/actions")
async def get_orch_actions(cache: StateCache = Depends(get_state_cache)):
    return cache.get_orchestration_actions()

@router.get("/api/public/orchestration/policies")
async def get_orch_policies(cache: StateCache = Depends(get_state_cache)):
    return cache.get_orchestration_policies()

@router.get("/api/public/orchestration/forecast")
async def get_orch_forecast(cache: StateCache = Depends(get_state_cache)):
    forecast_data = cache.get_orchestration_forecast()
    if not forecast_data:
        return {"forecasts": [], "bottlenecks_detected": False}
    return forecast_data

@router.post("/api/admin/orchestration/rebalance")
async def admin_orch_rebalance(cache: StateCache = Depends(get_state_cache)):
    # Simulates manual trigger of rebalancing
    actions = cache.get_orchestration_actions()
    actions.append({
        "action_id": f"act_rebalance_{int(time.time()*1000)}",
        "node_id": "all",
        "action_type": "REBALANCE",
        "status": "COMPLETED",
        "timestamp": time.time(),
        "explanation": "Manual administrator trigger",
        "evidence": ["Manual request received"]
    })
    cache.set_orchestration_actions(actions)
    
    # Event Bridge
    from analytics.events import AnalyticsEventType
    from dashboard.dependencies import get_event_bridge
    bridge = get_event_bridge()
    if bridge and bridge.analytics_bus:
        from analytics.events import AnalyticsEvent
        evt = AnalyticsEvent(
            event_id=f"evt_rebal_{int(time.time()*1000)}",
            timestamp_ns=int(time.time()*1e9),
            event_type=AnalyticsEventType.WORKLOAD_REBALANCED,
            source="AdminOrch",
            payload={"reason": "Manual Admin Trigger"}
        )
        bridge.analytics_bus.publish(evt)
        
    return {"status": "SUCCESS", "message": "Manual rebalance completed."}

@router.post("/api/admin/orchestration/heal")
async def admin_orch_heal(req: AdminHealRequest, cache: StateCache = Depends(get_state_cache)):
    actions = cache.get_orchestration_actions()
    actions.append({
        "action_id": f"act_heal_{int(time.time()*1000)}",
        "node_id": req.node_id,
        "action_type": req.action_type,
        "status": "COMPLETED",
        "timestamp": time.time(),
        "explanation": f"Manual administrative healing action: {req.action_type}",
        "evidence": ["Admin manual override"]
    })
    cache.set_orchestration_actions(actions)
    
    from analytics.events import AnalyticsEventType
    from dashboard.dependencies import get_event_bridge
    bridge = get_event_bridge()
    if bridge and bridge.analytics_bus:
        from analytics.events import AnalyticsEvent
        evt = AnalyticsEvent(
            event_id=f"evt_heal_{int(time.time()*1000)}",
            timestamp_ns=int(time.time()*1e9),
            event_type=AnalyticsEventType.SELF_HEAL_TRIGGERED,
            source="AdminOrch",
            payload={"node_id": req.node_id, "action_type": req.action_type}
        )
        bridge.analytics_bus.publish(evt)
        
    return {"status": "SUCCESS", "message": f"Healing action {req.action_type} submitted."}

@router.post("/api/admin/orchestration/policy")
async def admin_orch_policy(req: AdminPolicyRequest, cache: StateCache = Depends(get_state_cache)):
    policies = cache.get_orchestration_policies()
    # Remove existing if matches policy_id
    policies = [p for p in policies if p.get("policy_id") != req.policy_id]
    policies.append({
        "policy_id": req.policy_id,
        "name": req.name,
        "rule_expr": req.rule_expr,
        "action_type": req.action_type,
        "enabled": req.enabled
    })
    cache.set_orchestration_policies(policies)
    return {"status": "SUCCESS", "message": f"Policy {req.name} registered/updated."}

@router.post("/api/admin/orchestration/simulate")
async def admin_orch_simulate(req: AdminSimulateRequest, cache: StateCache = Depends(get_state_cache)):
    # Simulates different scenarios (e.g. CPU_SPIKE, MEM_PRESSURE, PARTITION)
    from analytics.events import AnalyticsEventType
    from dashboard.dependencies import get_event_bridge
    bridge = get_event_bridge()
    
    if req.scenario == "CPU_SPIKE":
        anomalies = cache.get_orchestration_anomalies()
        anomalies.append({
            "anomaly_id": f"anom_cpu_{int(time.time()*1000)}",
            "node_id": req.node_id or "node_1",
            "type": "CPU_SPIKE",
            "severity": "HIGH",
            "timestamp": time.time(),
            "details": f"Simulated CPU spike at {req.value or 95.0}%"
        })
        cache.set_orchestration_anomalies(anomalies)
        
        if bridge and bridge.analytics_bus:
            from analytics.events import AnalyticsEvent
            evt = AnalyticsEvent(
                event_id=f"evt_anom_{int(time.time()*1000)}",
                timestamp_ns=int(time.time()*1e9),
                event_type=AnalyticsEventType.ANOMALY_DETECTED,
                source="SimulateOrch",
                payload={"anomaly_type": "CPU_SPIKE", "node_id": req.node_id or "node_1"}
            )
            bridge.analytics_bus.publish(evt)
            
    elif req.scenario == "MEM_PRESSURE":
        anomalies = cache.get_orchestration_anomalies()
        anomalies.append({
            "anomaly_id": f"anom_mem_{int(time.time()*1000)}",
            "node_id": req.node_id or "node_1",
            "type": "MEM_PRESSURE",
            "severity": "HIGH",
            "timestamp": time.time(),
            "details": f"Simulated memory pressure at {req.value or 92.0}%"
        })
        cache.set_orchestration_anomalies(anomalies)
        
    return {"status": "SUCCESS", "scenario": req.scenario, "message": f"Scenario {req.scenario} simulated."}
