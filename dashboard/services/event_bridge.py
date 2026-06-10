import asyncio
import logging
from typing import Optional, List
from analytics.events import AnalyticsEvent, AnalyticsEventType
from dashboard.services.state_cache import StateCache
from dashboard.services.channel_manager import ChannelManager
from dashboard.models.schemas import (
    LeaderboardSnapshotResponse,
    LeaderboardEntryResponse,
    TournamentResponse,
    TournamentStageResponse,
    DeploymentHealthResponse,
    AnalyticsSummaryResponse
)

logger = logging.getLogger(__name__)

class EventBridge:
    """Subscribes to AnalyticsEventBus and forwards events to WebSocket clients & StateCache."""
    
    def __init__(self, state_cache: StateCache, channel_manager: ChannelManager):
        self.state_cache = state_cache
        self.channel_manager = channel_manager
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def handle_event(self, event: AnalyticsEvent):
        """Callback for AnalyticsEventBus. Can be invoked from any runner/worker thread."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._process_event(event), self.loop)
        else:
            # Fallback if no loop is running yet (e.g. startup / tests)
            logger.debug(f"EventBridge received event but event loop is not active: {event.event_type}")

    async def _process_event(self, event: AnalyticsEvent):
        import time
        try:
            event_type = event.event_type
            payload = event.payload
            
            # 1. Update State Cache and broadcast to matching WS channel
            if event_type == AnalyticsEventType.LEADERBOARD_UPDATE:
                snapshot = self._parse_leaderboard_snapshot(payload)
                if snapshot:
                    self.state_cache.set_leaderboard(snapshot)
                await self.channel_manager.broadcast("leaderboard", payload)
                
            elif event_type in (
                AnalyticsEventType.TOURNAMENT_STARTED,
                AnalyticsEventType.STAGE_STARTED,
                AnalyticsEventType.STAGE_COMPLETED,
                AnalyticsEventType.ADVANCEMENT,
                AnalyticsEventType.ELIMINATION,
                AnalyticsEventType.WINNER_DECLARED
            ):
                # We broadcast the tournament progress event
                await self.channel_manager.broadcast("tournament", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.SESSION_HEALTH:
                # Expect payload to contain list of health reports or a single report
                health_reports = self._parse_health_reports(payload)
                if health_reports:
                    self.state_cache.set_health(health_reports)
                await self.channel_manager.broadcast("health", payload)
                
            elif event_type in (
                AnalyticsEventType.EXECUTION_UPDATE,
                AnalyticsEventType.TELEMETRY_UPDATE,
                AnalyticsEventType.SCORE_UPDATE
            ):
                summary = self._update_analytics_summary(event_type, payload)
                if summary:
                    self.state_cache.set_analytics(summary)
                await self.channel_manager.broadcast("analytics", {
                    "event_type": event_type.value,
                    "payload": payload
                })

            elif event_type == AnalyticsEventType.EVALUATION_STARTED:
                self.state_cache.add_evaluation({
                    "campaign_id": payload["campaign_id"],
                    "contestant_id": payload["contestant_id"],
                    "status": "RUNNING",
                    "average_score": 0.0,
                    "overall_grade": "D",
                    "created_at": time.time_ns(),
                    "updated_at": time.time_ns()
                })
                await self.channel_manager.broadcast("tournament", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.EVALUATION_COMPLETED:
                eval_data = self.state_cache.get_evaluation(payload["campaign_id"])
                if not eval_data:
                    eval_data = {
                        "campaign_id": payload["campaign_id"],
                        "contestant_id": payload["contestant_id"],
                        "created_at": time.time_ns(),
                    }
                eval_data.update({
                    "status": "COMPLETED",
                    "average_score": payload["average_score"],
                    "overall_grade": payload["overall_grade"],
                    "updated_at": time.time_ns()
                })
                self.state_cache.add_evaluation(eval_data)
                
                # Also update LeaderboardEntry in cached leaderboard if it exists
                leaderboard = self.state_cache.get_leaderboard()
                if leaderboard:
                    for entry in leaderboard.entries:
                        if entry.contestant_id == payload["contestant_id"]:
                            entry.evaluation_score = payload["average_score"]
                            entry.skill_grade = payload["overall_grade"]
                    self.state_cache.set_leaderboard(leaderboard)
                    
                await self.channel_manager.broadcast("tournament", {
                    "event_type": event_type.value,
                    "payload": payload
                })

            elif event_type == AnalyticsEventType.PROFILE_UPDATED:
                self.state_cache.set_profile(payload["contestant_id"], payload["profiles"])
                leaderboard = self.state_cache.get_leaderboard()
                if leaderboard:
                    for entry in leaderboard.entries:
                        if entry.contestant_id == payload["contestant_id"]:
                            entry.benchmark_count = len(payload["profiles"])
                    self.state_cache.set_leaderboard(leaderboard)
                    
                await self.channel_manager.broadcast("leaderboard", {
                    "event_type": event_type.value,
                    "payload": payload
                })

            elif event_type == AnalyticsEventType.REPORT_GENERATED:
                self.state_cache.set_report(payload["campaign_id"], {
                    "campaign_id": payload["campaign_id"],
                    "contestant_id": payload["contestant_id"],
                    "markdown_report": payload.get("markdown", ""),
                    "html_report": payload.get("html", ""),
                    "json_report": payload.get("json", "")
                })

            elif event_type == AnalyticsEventType.ADVERSARIAL_TEST_COMPLETED:
                self.state_cache.add_adversarial_log({
                    "attack_id": payload["attack_id"],
                    "attack_type": payload["attack_type"],
                    "severity": payload["severity"],
                    "success": payload["success"],
                    "notes": payload.get("notes", ""),
                    "timestamp": time.time_ns()
                })
                await self.channel_manager.broadcast("analytics", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.NODE_REGISTERED:
                self.state_cache.set_nodes([payload])
                await self.channel_manager.broadcast("federation", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.NODE_REMOVED:
                node_id = payload.get("node_id")
                if node_id:
                    self.state_cache.remove_node_from_cache(node_id)
                await self.channel_manager.broadcast("federation", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.NODE_HEARTBEAT:
                node_id = payload.get("node_id")
                if node_id:
                    self.state_cache.update_node_heartbeat(
                        node_id,
                        payload.get("load", 0.0),
                        int(time.time())
                    )
                await self.channel_manager.broadcast("federation", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.JOB_ASSIGNED:
                job_id = payload.get("job_id")
                if job_id:
                    self.state_cache.update_job_status(
                        job_id,
                        "ASSIGNED",
                        node_id=payload.get("node_id"),
                        timestamp=int(time.time())
                    )
                await self.channel_manager.broadcast("federation", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.JOB_COMPLETED:
                job_id = payload.get("job_id")
                if job_id:
                    self.state_cache.update_job_status(
                        job_id,
                        "COMPLETED",
                        node_id=payload.get("node_id"),
                        score=payload.get("score"),
                        timestamp=int(time.time())
                    )
                await self.channel_manager.broadcast("federation", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.JOB_FAILED:
                job_id = payload.get("job_id")
                if job_id:
                    self.state_cache.update_job_status(
                        job_id,
                        "FAILED",
                        node_id=payload.get("node_id"),
                        error=payload.get("error"),
                        timestamp=int(time.time())
                    )
                await self.channel_manager.broadcast("federation", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.ARTIFACT_REPLICATED:
                self.state_cache.set_replication_status({
                    "last_artifact_id": payload.get("artifact_id"),
                    "last_peer_node_id": payload.get("peer_node_id"),
                    "direction": payload.get("direction"),
                    "size_bytes": payload.get("size_bytes"),
                    "hash": payload.get("hash"),
                    "timestamp": int(time.time())
                })
                await self.channel_manager.broadcast("federation", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
            elif event_type == AnalyticsEventType.FEDERATION_SYNC_COMPLETED:
                self.state_cache.set_replication_status({
                    "peer_node_id": payload.get("peer_node_id"),
                    "artifacts_out_of_sync_count": payload.get("artifacts_out_of_sync_count"),
                    "status": "COMPLETED" if payload.get("artifacts_out_of_sync_count", 0) == 0 else "PENDING_SYNC",
                    "timestamp": int(time.time())
                })
                await self.channel_manager.broadcast("federation", {
                    "event_type": event_type.value,
                    "payload": payload
                })
                
        except Exception as e:
            logger.error(f"Error processing event {event.event_type} in EventBridge: {e}", exc_info=True)

    def _parse_leaderboard_snapshot(self, payload: dict) -> Optional[LeaderboardSnapshotResponse]:
        try:
            # We construct LeaderboardSnapshotResponse from raw dictionary payload
            entries = []
            for e in payload.get("entries", []):
                entries.append(LeaderboardEntryResponse(
                    contestant_id=e["contestant_id"],
                    rank=e["rank"],
                    score=e["score"],
                    average_correctness=e.get("average_correctness", 0.0),
                    average_latency=e.get("average_latency", 0.0),
                    average_tps=e.get("average_tps", 0.0),
                    success_rate=e.get("success_rate", 0.0),
                    campaign_id=e.get("campaign_id", ""),
                    rating_grade=e.get("rating_grade", "D"),
                    previous_rank=e.get("previous_rank"),
                    tournament_id=e.get("tournament_id"),
                    stage_id=e.get("stage_id")
                ))
            return LeaderboardSnapshotResponse(
                snapshot_id=payload["snapshot_id"],
                campaign_id=payload["campaign_id"],
                timestamp=str(payload.get("timestamp", "")),
                entries=entries,
                tournament_id=payload.get("tournament_id"),
                stage_id=payload.get("stage_id"),
                entry_count=payload.get("entry_count", len(entries)),
                generated_at=payload.get("generated_at", ""),
                load_profile=payload.get("load_profile", "N/A"),
                event_count=payload.get("event_count", 0),
                campaign_size=payload.get("campaign_size", 0),
                worker_count=payload.get("worker_count", 0),
                execution_tps=payload.get("execution_tps", 0.0)
            )
        except Exception as e:
            logger.warning(f"Failed to parse leaderboard snapshot in EventBridge: {e}")
            return None

    def _parse_health_reports(self, payload: dict) -> List[DeploymentHealthResponse]:
        try:
            # Payload could be a single health record or dict of them
            reports = []
            records = payload if isinstance(payload, list) else [payload]
            for r in records:
                if "container_id" in r:
                    reports.append(DeploymentHealthResponse(
                        submission_id=r.get("submission_id", ""),
                        container_id=r["container_id"],
                        status=r.get("status", "UNKNOWN"),
                        uptime_ns=r.get("uptime_ns", 0),
                        restart_count=r.get("restart_count", 0),
                        failure_count=r.get("failure_count", 0),
                        last_heartbeat=r.get("last_heartbeat", 0)
                    ))
            return reports
        except Exception as e:
            logger.warning(f"Failed to parse health reports in EventBridge: {e}")
            return []

    def _update_analytics_summary(self, event_type: AnalyticsEventType, payload: dict) -> Optional[AnalyticsSummaryResponse]:
        try:
            current = self.state_cache.get_analytics()
            if not current:
                current = AnalyticsSummaryResponse(
                    total_scenarios_run=0,
                    successful_runs=0,
                    failed_runs=0,
                    avg_correctness=0.0,
                    avg_latency_ms=0.0,
                    avg_tps=0.0,
                    overall_success_rate=0.0
                )
                
            if event_type == AnalyticsEventType.EXECUTION_UPDATE:
                current.total_scenarios_run += 1
                if payload.get("status") == "SUCCESS":
                    current.successful_runs += 1
                else:
                    current.failed_runs += 1
                if current.total_scenarios_run > 0:
                    current.overall_success_rate = (current.successful_runs / current.total_scenarios_run) * 100.0
                    
            elif event_type == AnalyticsEventType.TELEMETRY_UPDATE:
                # Update rolling averages
                latency = payload.get("framework_latency", {}).get("avg_ms", 0.0)
                tps = payload.get("framework_tps", {}).get("tps", 0.0)
                count = current.total_scenarios_run or 1
                current.avg_latency_ms = (current.avg_latency_ms * (count - 1) + latency) / count
                current.avg_tps = (current.avg_tps * (count - 1) + tps) / count
                
            elif event_type == AnalyticsEventType.SCORE_UPDATE:
                correctness = payload.get("score_result", {}).get("correctness_score", 0.0)
                count = current.total_scenarios_run or 1
                current.avg_correctness = (current.avg_correctness * (count - 1) + correctness) / count
                
            return current
        except Exception as e:
            logger.warning(f"Failed to update analytics summary in EventBridge: {e}")
            return None
