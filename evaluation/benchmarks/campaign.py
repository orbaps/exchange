import uuid
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from evaluation.benchmarks.models import BenchmarkSuite, Benchmark
from evaluation.judge.judges import RuleBasedJudge, CompositeJudge, RubricJudge, JudgeResult, JudgeExplanation
from evaluation.profiles.generator import ProfileGenerator, SkillProfile
from evaluation.journal import EvaluationJournal
from analytics.bus import AnalyticsEventBus
from analytics.events import AnalyticsEvent, AnalyticsEventType

# Import Leaderboard models for updating the entry
from leaderboard.models import LeaderboardEntry

@dataclass
class EvaluationCampaign:
    campaign_id: str
    name: str
    suites: List[BenchmarkSuite]
    contestant_id: str
    seed: int = 42
    adversarial_cases: List[Any] = field(default_factory=list)

class EvaluationCampaignRunner:
    """Orchestrates running multi-suite evaluation campaigns and aggregates skill profiles."""
    
    def __init__(
        self,
        journal: EvaluationJournal,
        analytics_bus: Optional[AnalyticsEventBus] = None,
        judge: Optional[RuleBasedJudge] = None
    ):
        self.journal = journal
        self.analytics_bus = analytics_bus
        self.judge = judge or RuleBasedJudge()

    def _publish_event(self, event_type: AnalyticsEventType, payload: dict):
        if self.analytics_bus:
            event = AnalyticsEvent(
                event_id=f"evt_eval_{time.time_ns()}",
                timestamp_ns=time.time_ns(),
                event_type=event_type,
                source="EvaluationCampaignRunner",
                payload=payload
            )
            self.analytics_bus.publish(event)

    def run(
        self,
        campaign: EvaluationCampaign,
        contestant_agent: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Run the evaluation campaign against a contestant agent.
        If no contestant agent is provided, a deterministic mock evaluator is used.
        """
        self._publish_event(AnalyticsEventType.EVALUATION_STARTED, {
            "campaign_id": campaign.campaign_id,
            "contestant_id": campaign.contestant_id
        })
        
        # Log start to journal
        self.journal.write_entry(
            event_type="CAMPAIGN_START",
            run_id=campaign.campaign_id,
            benchmark_id="",
            payload={"name": campaign.name, "contestant_id": campaign.contestant_id}
        )
        
        results = []
        for suite in campaign.suites:
            for benchmark in suite.benchmarks:
                import hashlib
                hash_bytes = f"{campaign.campaign_id}_{benchmark.benchmark_id}_{campaign.seed}".encode("utf-8")
                deterministic_hash = hashlib.sha256(hash_bytes).hexdigest()[:8]
                run_id = f"run_{deterministic_hash}"
                
                # Log task start
                self.journal.write_entry(
                    event_type="TASK_START",
                    run_id=run_id,
                    benchmark_id=benchmark.benchmark_id,
                    payload={"seed": benchmark.seed, "max_score": benchmark.max_score}
                )
                
                # Execute output generation
                start_time = time.time_ns()
                
                # Simulated / actual execution
                if contestant_agent and hasattr(contestant_agent, "execute"):
                    try:
                        actual_output = contestant_agent.execute(benchmark.description, benchmark.seed)
                    except Exception as e:
                        actual_output = f"Execution crash: {str(e)}"
                else:
                    # Fallback deterministic mock solver
                    if "match" in benchmark.evaluation_rules or "exact_match" in benchmark.evaluation_rules:
                        actual_output = benchmark.expected_output
                    else:
                        actual_output = f"Completed run for {benchmark.benchmark_id} seed={benchmark.seed}"
                        
                end_time = time.time_ns()
                if contestant_agent is None:
                    duration_ms = 1.5  # Deterministic duration fallback to prevent journal hash jitter in tests
                else:
                    duration_ms = (end_time - start_time) / 1e6
                
                telemetry = {
                    "execution_time_ms": duration_ms,
                    "tps": 500.0, # default mock performance
                    "memory_mb": 64.0
                }
                
                # Invoke Judge
                j_result, j_explanation = self.judge.judge(benchmark, actual_output, telemetry)
                
                # Log task end
                evidence_list = [
                    {"evidence_id": e.evidence_id, "finding": e.finding, "source": e.source}
                    for e in j_explanation.evidence_items
                ]
                self.journal.write_entry(
                    event_type="TASK_END",
                    run_id=run_id,
                    benchmark_id=benchmark.benchmark_id,
                    payload={
                        "score": j_result.final_score,
                        "correctness": j_result.correctness_score,
                        "efficiency": j_result.efficiency_score,
                        "quality": j_result.quality_score,
                        "safety": j_result.safety_score,
                        "findings": j_explanation.findings,
                        "evidence": evidence_list
                    }
                )
                
                results.append({
                    "run_id": run_id,
                    "benchmark_id": benchmark.benchmark_id,
                    "domain": benchmark.category.value,
                    "judge_result": j_result,
                    "judge_explanation": j_explanation,
                    "telemetry": telemetry,
                    "output": actual_output
                })

        # Generate Skill Profile
        profiles = ProfileGenerator.generate(results)
        
        # Log PROFILE_GENERATED to journal
        self.journal.write_entry(
            event_type="PROFILE_GENERATED",
            run_id=campaign.campaign_id,
            benchmark_id="",
            payload={"profiles": [{"category": p.category, "score": p.score, "grade": p.grade} for p in profiles]}
        )
        
        # Run adversarial tests if available
        if hasattr(campaign, "adversarial_cases") and campaign.adversarial_cases:
            from evaluation.adversarial.adversarial import AdversarialRunner
            adv_runner = AdversarialRunner(self.analytics_bus)
            adv_res = adv_runner.run_attacks(contestant_agent, campaign.adversarial_cases)
            
            # Log ADVERSARIAL_COMPLETED to journal
            self.journal.write_entry(
                event_type="ADVERSARIAL_COMPLETED",
                run_id=campaign.campaign_id,
                benchmark_id="",
                payload={
                    "safety_score": adv_res["safety_score"],
                    "total_attacks": adv_res["total_attacks"],
                    "attacks_blocked": adv_res["attacks_blocked"],
                    "attacks_bypassed": adv_res["attacks_bypassed"],
                    "results": [
                        {
                            "attack_id": r.attack_id,
                            "success": r.success,
                            "severity": r.severity.value,
                            "notes": r.notes
                        }
                        for r in adv_res["results"]
                    ]
                }
            )
        
        # Calculate aggregate scores
        avg_score = sum(r["judge_result"].final_score for r in results) / len(results) if results else 0.0
        overall_grade = ProfileGenerator.calculate_grade(avg_score)
        
        # Generate and log Research Report
        from evaluation.reports.report_gen import ResearchReportGenerator
        report_results = []
        for r in results:
            report_results.append({
                "benchmark_id": r["benchmark_id"],
                "domain": r["domain"],
                "judge_result": r["judge_result"]
            })
        campaign_data = {
            "campaign_id": campaign.campaign_id,
            "contestant_id": campaign.contestant_id,
            "overall_grade": overall_grade,
            "average_score": avg_score,
            "profiles": profiles,
            "results": report_results
        }
        if contestant_agent is None:
            campaign_data["generated_at"] = "2026-01-01 00:00:00 UTC"
        
        md_report = ResearchReportGenerator.generate_markdown(campaign_data)
        html_report = ResearchReportGenerator.generate_html(campaign_data)
        json_report = ResearchReportGenerator.generate_json(campaign_data)
        
        # Log REPORT_GENERATED to journal
        self.journal.write_entry(
            event_type="REPORT_GENERATED",
            run_id=campaign.campaign_id,
            benchmark_id="",
            payload={
                "markdown": md_report,
                "html": html_report,
                "json": json_report
            }
        )
        
        # Build expected final state to compute fingerprint
        expected_state = {
            "campaign_id": campaign.campaign_id,
            "status": "COMPLETED",
            "benchmarks": {},
            "overall_score": avg_score,
            "overall_grade": overall_grade,
            "profiles": [{"category": p.category, "score": p.score, "grade": p.grade} for p in profiles]
        }
        for r in results:
            expected_state["benchmarks"][r["benchmark_id"]] = {
                "benchmark_id": r["benchmark_id"],
                "status": "COMPLETED",
                "score": r["judge_result"].final_score,
                "correctness": r["judge_result"].correctness_score,
                "efficiency": r["judge_result"].efficiency_score,
                "quality": r["judge_result"].quality_score,
                "safety": r["judge_result"].safety_score,
                "findings": r["judge_explanation"].findings,
                "evidence": [
                    {"evidence_id": e.evidence_id, "finding": e.finding, "source": e.source}
                    for e in r["judge_explanation"].evidence_items
                ]
            }
            
        from evaluation.replay.replay import EvaluationReplay
        state_fp = EvaluationReplay.compute_fingerprint(expected_state)
        
        # Write campaign complete to journal
        self.journal.write_entry(
            event_type="CAMPAIGN_END",
            run_id=campaign.campaign_id,
            benchmark_id="",
            payload={
                "average_score": avg_score,
                "overall_grade": overall_grade,
                "profiles": [{"category": p.category, "score": p.score, "grade": p.grade} for p in profiles],
                "state_fingerprint": state_fp
            }
        )
        
        self._publish_event(AnalyticsEventType.PROFILE_UPDATED, {
            "contestant_id": campaign.contestant_id,
            "profiles": [{"category": p.category, "score": p.score, "grade": p.grade} for p in profiles]
        })
        
        self._publish_event(AnalyticsEventType.REPORT_GENERATED, {
            "campaign_id": campaign.campaign_id,
            "contestant_id": campaign.contestant_id,
            "markdown": md_report,
            "html": html_report,
            "json": json_report
        })
        
        self._publish_event(AnalyticsEventType.EVALUATION_COMPLETED, {
            "campaign_id": campaign.campaign_id,
            "contestant_id": campaign.contestant_id,
            "average_score": avg_score,
            "overall_grade": overall_grade
        })
        
        return {
            "campaign_id": campaign.campaign_id,
            "contestant_id": campaign.contestant_id,
            "results": results,
            "profiles": profiles,
            "average_score": avg_score,
            "overall_grade": overall_grade
        }
