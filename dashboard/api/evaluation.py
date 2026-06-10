import os
import time
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from dashboard.dependencies import get_state_cache
from dashboard.services.state_cache import StateCache

# Router setup
router = APIRouter(prefix="/api/public/evaluation", tags=["Evaluation Framework"])

# Pydantic Schemas
class EvaluationCampaignResponse(BaseModel):
    campaign_id: str
    contestant_id: str
    status: str
    average_score: float
    overall_grade: str
    created_at: int
    updated_at: int

class BenchmarkResponse(BaseModel):
    benchmark_id: str
    category: str
    title: str
    description: str
    seed: int
    max_score: float
    expected_output: str
    evaluation_rules: List[str]
    timeout_ms: int
    metadata: Dict[str, Any]

class SkillProfileResponse(BaseModel):
    category: str
    score: float
    grade: str

class ContestantProfileResponse(BaseModel):
    contestant_id: str
    profiles: List[SkillProfileResponse]

class AdversarialLogResponse(BaseModel):
    attack_id: str
    attack_type: str
    severity: str
    success: bool
    notes: str
    timestamp: int

class ReportResponse(BaseModel):
    campaign_id: str
    contestant_id: str
    markdown_report: str
    html_report: str
    json_report: str


# Helper function to ensure default benchmarks exist in the cache
def ensure_default_benchmarks(cache: StateCache):
    if cache.get_benchmarks():
        return
        
    from evaluation.benchmarks.models import Benchmark, EvaluationDomain
    
    defaults = [
        Benchmark(
            benchmark_id="bench_coding_01",
            category=EvaluationDomain.CODING,
            title="Duplicate Keyword Argument Bug",
            description="Fix duplicate engine_class keyword argument in SubmissionMetadata instantiation",
            seed=42,
            max_score=100.0,
            expected_output="engine_class=getattr(manifest, 'engine_class', 'HostedEngine')",
            evaluation_rules=["contains:engine_class", "not_contains:engine_class="],
            timeout_ms=5000,
            metadata={"difficulty": "Medium", "language": "python"}
        ),
        Benchmark(
            benchmark_id="bench_reasoning_01",
            category=EvaluationDomain.REASONING,
            title="Multi-stage Advancement Logic",
            description="Verify correctness and step logic of tournament advancement rules",
            seed=101,
            max_score=100.0,
            expected_output="Advancement check passed",
            evaluation_rules=["contains:Advancement", "contains:passed"],
            timeout_ms=2000,
            metadata={"difficulty": "Hard"}
        ),
        Benchmark(
            benchmark_id="bench_math_01",
            category=EvaluationDomain.MATHEMATICS,
            title="TOP_PERCENT Tie Breaker Boundary Check",
            description="Verify boundary calculations for TOP_PERCENT advancements",
            seed=202,
            max_score=100.0,
            expected_output="ceil calculation matches",
            evaluation_rules=["contains:ceil", "contains:matches"],
            timeout_ms=1000,
            metadata={"difficulty": "Medium"}
        ),
        Benchmark(
            benchmark_id="bench_security_01",
            category=EvaluationDomain.CYBERSECURITY,
            title="Mitigate System Rule Bypass",
            description="Mitigate rule bypass attempts when evaluating external packages",
            seed=303,
            max_score=100.0,
            expected_output="Access Denied. Security restriction active.",
            evaluation_rules=["exact_match"],
            timeout_ms=3000,
            metadata={"difficulty": "Critical"}
        ),
        Benchmark(
            benchmark_id="bench_quantum_01",
            category=EvaluationDomain.QUANTUM,
            title="Qubit State Verification",
            description="Optimize qubit state coherence measurement algorithms",
            seed=404,
            max_score=100.0,
            expected_output="State verified",
            evaluation_rules=["contains:State", "contains:verified"],
            timeout_ms=8000,
            metadata={"difficulty": "Hard"}
        ),
        Benchmark(
            benchmark_id="bench_systems_01",
            category=EvaluationDomain.SYSTEMS,
            title="High Throughput TPS Pipeline",
            description="Achieve high throughput pipeline execution under load",
            seed=505,
            max_score=100.0,
            expected_output="TPS >= 1000",
            evaluation_rules=["contains:TPS"],
            timeout_ms=4000,
            metadata={"difficulty": "Hard"}
        )
    ]
    cache.set_benchmarks(defaults)


# Helper function to search for journal files and reconstruct evaluation state
def rebuild_evaluation_state_from_journals(cache: StateCache):
    paths = []
    # Check default directory dashboard_run_artifacts
    if os.path.exists("dashboard_run_artifacts"):
        for f in os.listdir("dashboard_run_artifacts"):
            if f.endswith(".jsonl") and ("eval" in f or "campaign" in f):
                paths.append(os.path.join("dashboard_run_artifacts", f))
                
    # Also check current directory
    for f in os.listdir("."):
        if f.endswith(".jsonl") and ("eval" in f or "campaign" in f):
            paths.append(f)
            
    paths = list(set(paths))
    
    for path in paths:
        try:
            from evaluation.journal import EvaluationJournal
            from evaluation.replay.replay import EvaluationReplay
            
            journal = EvaluationJournal(path)
            timeline = EvaluationReplay.load_timeline(journal)
            if not timeline.steps:
                continue
                
            replay = EvaluationReplay(timeline)
            replay.seek(len(timeline.steps) - 1)
            state = replay.reconstruct_state()
            
            campaign_id = state.get("campaign_id")
            if not campaign_id:
                continue
                
            contestant_id = "unknown"
            for step in timeline.steps:
                if step.event_type == "CAMPAIGN_START":
                    contestant_id = step.payload.get("contestant_id", "unknown")
                    break
                    
            cache.add_evaluation({
                "campaign_id": campaign_id,
                "contestant_id": contestant_id,
                "status": state.get("status", "COMPLETED"),
                "average_score": state.get("overall_score", 0.0),
                "overall_grade": state.get("overall_grade", "D"),
                "created_at": int(os.path.getctime(path) * 1e9),
                "updated_at": int(os.path.getmtime(path) * 1e9)
            })
            
            if state.get("profiles"):
                profiles = []
                for p in state["profiles"]:
                    profiles.append({
                        "category": p.get("category"),
                        "score": p.get("score"),
                        "grade": p.get("grade")
                    })
                cache.set_profile(contestant_id, profiles)
                
            from evaluation.reports.report_gen import ResearchReportGenerator
            results = []
            for b_id, b_details in state.get("benchmarks", {}).items():
                from evaluation.judge.judges import JudgeResult
                jr = JudgeResult(
                    correctness_score=b_details.get("correctness", 0.0),
                    efficiency_score=b_details.get("efficiency", 0.0),
                    quality_score=b_details.get("quality", 0.0),
                    safety_score=b_details.get("safety", 0.0),
                    final_score=b_details.get("score", 0.0)
                )
                
                domain_val = "CODING"
                if "reason" in b_id or "logic" in b_id:
                    domain_val = "REASONING"
                elif "math" in b_id:
                    domain_val = "MATHEMATICS"
                elif "security" in b_id or "bypass" in b_id:
                    domain_val = "CYBERSECURITY"
                elif "quantum" in b_id:
                    domain_val = "QUANTUM"
                elif "system" in b_id or "tps" in b_id:
                    domain_val = "SYSTEMS"
                
                results.append({
                    "benchmark_id": b_id,
                    "domain": domain_val,
                    "judge_result": jr
                })
                
            from evaluation.profiles.generator import SkillProfile
            profile_objs = []
            for p in state.get("profiles", []):
                profile_objs.append(SkillProfile(
                    category=p.get("category"),
                    score=p.get("score"),
                    grade=p.get("grade")
                ))
                
            campaign_data = {
                "campaign_id": campaign_id,
                "contestant_id": contestant_id,
                "overall_grade": state.get("overall_grade", "D"),
                "average_score": state.get("overall_score", 0.0),
                "profiles": profile_objs,
                "results": results
            }
            
            cache.set_report(campaign_id, {
                "campaign_id": campaign_id,
                "contestant_id": contestant_id,
                "markdown_report": ResearchReportGenerator.generate_markdown(campaign_data),
                "html_report": ResearchReportGenerator.generate_html(campaign_data),
                "json_report": ResearchReportGenerator.generate_json(campaign_data)
            })
            
            for step in timeline.steps:
                if step.event_type == "ADVERSARIAL_TEST_COMPLETED":
                    cache.add_adversarial_log({
                        "attack_id": step.payload.get("attack_id"),
                        "attack_type": step.payload.get("attack_type"),
                        "severity": step.payload.get("severity"),
                        "success": step.payload.get("success"),
                        "notes": step.payload.get("notes", "Restored from journal"),
                        "timestamp": int(os.path.getctime(path) * 1e9)
                    })
        except Exception:
            pass


# ── REST Endpoints ────────────────────────────────────────────────────────────

@router.get("/evaluations", response_model=List[EvaluationCampaignResponse])
async def get_evaluations(cache: StateCache = Depends(get_state_cache)):
    rebuild_evaluation_state_from_journals(cache)
    evals = cache.get_evaluations()
    # If cache is still empty, return an empty list gracefully
    return [
        EvaluationCampaignResponse(
            campaign_id=e["campaign_id"],
            contestant_id=e["contestant_id"],
            status=e["status"],
            average_score=e["average_score"],
            overall_grade=e["overall_grade"],
            created_at=e["created_at"],
            updated_at=e["updated_at"]
        ) for e in evals
    ]

@router.get("/evaluations/{id}", response_model=EvaluationCampaignResponse)
async def get_evaluation(id: str, cache: StateCache = Depends(get_state_cache)):
    rebuild_evaluation_state_from_journals(cache)
    e = cache.get_evaluation(id)
    if not e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation campaign with ID {id} not found."
        )
    return EvaluationCampaignResponse(
        campaign_id=e["campaign_id"],
        contestant_id=e["contestant_id"],
        status=e["status"],
        average_score=e["average_score"],
        overall_grade=e["overall_grade"],
        created_at=e["created_at"],
        updated_at=e["updated_at"]
    )

@router.get("/benchmarks", response_model=List[BenchmarkResponse])
async def get_benchmarks(cache: StateCache = Depends(get_state_cache)):
    ensure_default_benchmarks(cache)
    benchmarks = cache.get_benchmarks()
    res = []
    for b in benchmarks:
        # Check if benchmark is dict or object
        b_id = getattr(b, "benchmark_id", None) or b.get("benchmark_id")
        category = getattr(b, "category", None)
        category_str = category.value if hasattr(category, "value") else str(category)
        title = getattr(b, "title", None) or b.get("title", "")
        desc = getattr(b, "description", None) or b.get("description", "")
        seed = getattr(b, "seed", None) or b.get("seed", 0)
        max_score = getattr(b, "max_score", None) or b.get("max_score", 100.0)
        expected = getattr(b, "expected_output", None) or b.get("expected_output", "")
        rules = getattr(b, "evaluation_rules", None) or b.get("evaluation_rules", [])
        timeout = getattr(b, "timeout_ms", None) or b.get("timeout_ms", 5000)
        meta = getattr(b, "metadata", None) or b.get("metadata", {})
        
        res.append(BenchmarkResponse(
            benchmark_id=b_id,
            category=category_str,
            title=title,
            description=desc,
            seed=seed,
            max_score=max_score,
            expected_output=expected,
            evaluation_rules=rules,
            timeout_ms=timeout,
            metadata=meta
        ))
    return res

@router.get("/profiles", response_model=List[ContestantProfileResponse])
async def get_profiles(cache: StateCache = Depends(get_state_cache)):
    rebuild_evaluation_state_from_journals(cache)
    profiles_dict = cache.get_profiles()
    res = []
    for contestant_id, p_list in profiles_dict.items():
        sub_list = []
        for p in p_list:
            cat = getattr(p, "category", None) or p.get("category")
            score = getattr(p, "score", None) or p.get("score", 0.0)
            grade = getattr(p, "grade", None) or p.get("grade", "D")
            sub_list.append(SkillProfileResponse(
                category=cat,
                score=score,
                grade=grade
            ))
        res.append(ContestantProfileResponse(
            contestant_id=contestant_id,
            profiles=sub_list
        ))
    return res

@router.get("/adversarial", response_model=List[AdversarialLogResponse])
async def get_adversarial(cache: StateCache = Depends(get_state_cache)):
    rebuild_evaluation_state_from_journals(cache)
    logs = cache.get_adversarial_logs()
    res = []
    for l in logs:
        res.append(AdversarialLogResponse(
            attack_id=l["attack_id"],
            attack_type=l["attack_type"],
            severity=l["severity"],
            success=l["success"],
            notes=l.get("notes", ""),
            timestamp=l["timestamp"]
        ))
    return res

@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(campaign_id: Optional[str] = None, cache: StateCache = Depends(get_state_cache)):
    rebuild_evaluation_state_from_journals(cache)
    reports = cache.get_reports()
    
    res = []
    for camp_id, r in reports.items():
        if campaign_id and camp_id != campaign_id:
            continue
        res.append(ReportResponse(
            campaign_id=camp_id,
            contestant_id=r["contestant_id"],
            markdown_report=r["markdown_report"],
            html_report=r["html_report"],
            json_report=r["json_report"]
        ))
    return res
