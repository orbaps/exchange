import threading
from typing import Dict, Any, List, Optional
from dashboard.models.schemas import (
    LeaderboardSnapshotResponse,
    TournamentResponse,
    DeploymentHealthResponse,
    AnalyticsSummaryResponse,
    DeploymentRecordResponse
)

class StateCache:
    """In-memory cache for all dashboard summary states, ensuring fast GET responses."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_leaderboard: Optional[LeaderboardSnapshotResponse] = None
        self._latest_tournament: Optional[TournamentResponse] = None
        self._latest_health: List[DeploymentHealthResponse] = []
        self._latest_analytics: Optional[AnalyticsSummaryResponse] = None
        self._deployments: Dict[str, DeploymentRecordResponse] = {}
        # Evaluation Framework additions
        self._evaluations: Dict[str, Any] = {}
        self._benchmarks: Dict[str, Any] = {}
        self._profiles: Dict[str, Any] = {}  # contestant_id -> list of SkillProfile
        self._adversarial_logs: List[Any] = []
        self._reports: Dict[str, Any] = {}  # campaign_id -> report
        # Federation Layer additions
        self._nodes: Dict[str, Any] = {}
        self._jobs: Dict[str, Any] = {}
        self._federation_health: Dict[str, Any] = {}
        self._replication_status: Dict[str, Any] = {}
        self._federation_replay: Dict[str, Any] = {}
        self._federated_leaderboard: Optional[Any] = None
        # Phase 8.0 Orchestration additions
        self._orchestration_status: Dict[str, Any] = {}
        self._orchestration_health: Dict[str, Any] = {}
        self._orchestration_anomalies: List[Any] = []
        self._orchestration_actions: List[Any] = []
        self._orchestration_policies: List[Any] = []
        self._orchestration_forecast: Dict[str, Any] = {}

    # ── Leaderboard ───────────────────────────────────────────────────────────
    def set_leaderboard(self, snapshot: LeaderboardSnapshotResponse):
        with self._lock:
            self._latest_leaderboard = snapshot

    def get_leaderboard(self) -> Optional[LeaderboardSnapshotResponse]:
        with self._lock:
            return self._latest_leaderboard

    # ── Tournament ────────────────────────────────────────────────────────────
    def set_tournament(self, tournament: TournamentResponse):
        with self._lock:
            self._latest_tournament = tournament

    def get_tournament(self) -> Optional[TournamentResponse]:
        with self._lock:
            return self._latest_tournament

    # ── Health ────────────────────────────────────────────────────────────────
    def set_health(self, health_list: List[DeploymentHealthResponse]):
        with self._lock:
            self._latest_health = health_list

    def get_health(self) -> List[DeploymentHealthResponse]:
        with self._lock:
            return list(self._latest_health)

    # ── Analytics ─────────────────────────────────────────────────────────────
    def set_analytics(self, analytics: AnalyticsSummaryResponse):
        with self._lock:
            self._latest_analytics = analytics

    def get_analytics(self) -> Optional[AnalyticsSummaryResponse]:
        with self._lock:
            return self._latest_analytics

    # ── Deployments ───────────────────────────────────────────────────────────
    def upsert_deployment(self, record: DeploymentRecordResponse):
        with self._lock:
            self._deployments[record.deployment_id] = record

    def get_deployments(self) -> List[DeploymentRecordResponse]:
        with self._lock:
            # Return sorted by created_at descending
            return sorted(self._deployments.values(), key=lambda d: d.created_at, reverse=True)

    def get_deployment(self, deployment_id: str) -> Optional[DeploymentRecordResponse]:
        with self._lock:
            return self._deployments.get(deployment_id)
            
    def get_latest_deployment_by_submission(self, submission_id: str) -> Optional[DeploymentRecordResponse]:
        with self._lock:
            recs = [r for r in self._deployments.values() if r.submission_id == submission_id]
            if not recs:
                return None
            return max(recs, key=lambda r: r.created_at)

    # ── Evaluation ────────────────────────────────────────────────────────────
    def add_evaluation(self, evaluation: Any):
        with self._lock:
            self._evaluations[evaluation["campaign_id"]] = evaluation

    def get_evaluations(self) -> List[Any]:
        with self._lock:
            return list(self._evaluations.values())

    def get_evaluation(self, campaign_id: str) -> Optional[Any]:
        with self._lock:
            return self._evaluations.get(campaign_id)

    # ── Benchmarks ────────────────────────────────────────────────────────────
    def set_benchmarks(self, benchmarks: List[Any]):
        with self._lock:
            for b in benchmarks:
                b_id = getattr(b, "benchmark_id", None) or b.get("benchmark_id")
                if b_id:
                    self._benchmarks[b_id] = b

    def get_benchmarks(self) -> List[Any]:
        with self._lock:
            return list(self._benchmarks.values())

    # ── Profiles ──────────────────────────────────────────────────────────────
    def set_profile(self, contestant_id: str, profiles: List[Any]):
        with self._lock:
            self._profiles[contestant_id] = profiles

    def get_profiles(self) -> Dict[str, List[Any]]:
        with self._lock:
            return dict(self._profiles)

    # ── Adversarial ───────────────────────────────────────────────────────────
    def add_adversarial_log(self, log: Any):
        with self._lock:
            self._adversarial_logs.append(log)

    def get_adversarial_logs(self) -> List[Any]:
        with self._lock:
            return list(self._adversarial_logs)

    # ── Reports ───────────────────────────────────────────────────────────────
    def set_report(self, campaign_id: str, report: Any):
        with self._lock:
            self._reports[campaign_id] = report

    def get_reports(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._reports)

    def get_report(self, campaign_id: str) -> Optional[Any]:
        with self._lock:
            return self._reports.get(campaign_id)

    # ── Federation Nodes ──────────────────────────────────────────────────────
    def set_nodes(self, nodes: List[Any]):
        with self._lock:
            for n in nodes:
                n_id = getattr(n, "node_id", None) or n.get("node_id")
                if n_id:
                    self._nodes[n_id] = n

    def update_node_heartbeat(self, node_id: str, load: float, timestamp: int):
        with self._lock:
            if node_id in self._nodes:
                node = self._nodes[node_id]
                if isinstance(node, dict):
                    node["load"] = load
                    node["last_seen"] = timestamp
                    node["status"] = "ACTIVE"
                else:
                    node.load = load
                    node.last_seen = timestamp
                    node.status = "ACTIVE"

    def get_nodes(self) -> List[Any]:
        with self._lock:
            return list(self._nodes.values())

    def remove_node_from_cache(self, node_id: str):
        with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]

    # ── Federation Jobs ───────────────────────────────────────────────────────
    def set_jobs(self, jobs: List[Any]):
        with self._lock:
            for j in jobs:
                j_id = getattr(j, "job_id", None) or j.get("job_id")
                if j_id:
                    self._jobs[j_id] = j

    def update_job_status(self, job_id: str, status: str, node_id: Optional[str] = None, score: Optional[float] = None, error: Optional[str] = None, timestamp: Optional[int] = None):
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                if isinstance(job, dict):
                    job["status"] = status
                    if node_id is not None:
                        job["assigned_node_id"] = node_id
                    if score is not None:
                        if "payload" not in job:
                            job["payload"] = {}
                        job["payload"]["score"] = score
                    if error is not None:
                        job["error"] = error
                    if status == "COMPLETED" and timestamp is not None:
                        job["completed_at"] = timestamp
                    elif status == "RUNNING" and timestamp is not None:
                        job["started_at"] = timestamp
                else:
                    job.status = status
                    if node_id is not None:
                        job.assigned_node_id = node_id
                    if score is not None:
                        if not job.payload:
                            job.payload = {}
                        job.payload["score"] = score
                    if error is not None:
                        job.error = error
                    if status == "COMPLETED" and timestamp is not None:
                        job.completed_at = timestamp
                    elif status == "RUNNING" and timestamp is not None:
                        job.started_at = timestamp
            else:
                self._jobs[job_id] = {
                    "job_id": job_id,
                    "task_type": "BENCHMARK_EXECUTION",
                    "payload": {"score": score} if score is not None else {},
                    "status": status,
                    "assigned_node_id": node_id,
                    "created_at": timestamp or 0,
                    "started_at": timestamp if status == "RUNNING" else None,
                    "completed_at": timestamp if status == "COMPLETED" else None,
                    "retry_count": 0,
                    "max_retries": 3,
                    "error": error
                }

    def get_jobs(self) -> List[Any]:
        with self._lock:
            return list(self._jobs.values())

    # ── Federation Health ─────────────────────────────────────────────────────
    def set_federation_health(self, health: Dict[str, Any]):
        with self._lock:
            self._federation_health = health

    def get_federation_health(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._federation_health)

    # ── Replication Status ────────────────────────────────────────────────────
    def set_replication_status(self, status: Dict[str, Any]):
        with self._lock:
            self._replication_status = status

    def get_replication_status(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._replication_status)

    # ── Federation Replay ─────────────────────────────────────────────────────
    def set_federation_replay(self, replay_data: Dict[str, Any]):
        with self._lock:
            self._federation_replay = replay_data

    def get_federation_replay(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._federation_replay)

    # ── Federated Leaderboard ─────────────────────────────────────────────────
    def set_federated_leaderboard(self, lb: Any):
        with self._lock:
            self._federated_leaderboard = lb

    def get_federated_leaderboard(self) -> Optional[Any]:
        with self._lock:
            return self._federated_leaderboard

    # ── Orchestration status ──────────────────────────────────────────────────
    def set_orchestration_status(self, val: Dict[str, Any]):
        with self._lock:
            self._orchestration_status = val

    def get_orchestration_status(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._orchestration_status)

    # ── Orchestration health ──────────────────────────────────────────────────
    def set_orchestration_health(self, val: Dict[str, Any]):
        with self._lock:
            self._orchestration_health = val

    def get_orchestration_health(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._orchestration_health)

    # ── Orchestration anomalies ───────────────────────────────────────────────
    def set_orchestration_anomalies(self, val: List[Any]):
        with self._lock:
            self._orchestration_anomalies = list(val)

    def get_orchestration_anomalies(self) -> List[Any]:
        with self._lock:
            return list(self._orchestration_anomalies)

    # ── Orchestration actions ─────────────────────────────────────────────────
    def set_orchestration_actions(self, val: List[Any]):
        with self._lock:
            self._orchestration_actions = list(val)

    def get_orchestration_actions(self) -> List[Any]:
        with self._lock:
            return list(self._orchestration_actions)

    # ── Orchestration policies ────────────────────────────────────────────────
    def set_orchestration_policies(self, val: List[Any]):
        with self._lock:
            self._orchestration_policies = list(val)

    def get_orchestration_policies(self) -> List[Any]:
        with self._lock:
            return list(self._orchestration_policies)

    # ── Orchestration forecast ────────────────────────────────────────────────
    def set_orchestration_forecast(self, val: Dict[str, Any]):
        with self._lock:
            self._orchestration_forecast = val

    def get_orchestration_forecast(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._orchestration_forecast)
            
    def clear(self):
        with self._lock:
            self._latest_leaderboard = None
            self._latest_tournament = None
            self._latest_health = []
            self._latest_analytics = None
            self._deployments.clear()
            self._evaluations.clear()
            self._benchmarks.clear()
            self._profiles.clear()
            self._adversarial_logs.clear()
            self._reports.clear()
            self._nodes.clear()
            self._jobs.clear()
            self._federation_health.clear()
            self._replication_status.clear()
            self._federation_replay.clear()
            self._federated_leaderboard = None
            self._orchestration_status.clear()
            self._orchestration_health.clear()
            self._orchestration_anomalies.clear()
            self._orchestration_actions.clear()
            self._orchestration_policies.clear()
            self._orchestration_forecast.clear()
