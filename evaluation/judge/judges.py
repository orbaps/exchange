import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from evaluation.benchmarks.models import Benchmark, EvaluationDomain
from evaluation.benchmarks.evaluators import (
    CodingEvaluator,
    ReasoningEvaluator,
    MathematicsEvaluator,
    CybersecurityEvaluator,
    QuantumEvaluator,
    SystemsEvaluator
)

@dataclass
class EvidenceItem:
    """Explicit link between score calculation and source material or telemetry metrics."""
    evidence_id: str
    benchmark_id: str
    finding: str
    source: str  # e.g., "telemetry", "stdout", "rule_checker"

@dataclass
class JudgeExplanation:
    """Traceable, explainable reasoning behind a judge's final scores."""
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class JudgeResult:
    """Component-level metrics resulting from evaluation scoring."""
    correctness_score: float
    efficiency_score: float
    quality_score: float
    safety_score: float
    final_score: float

class BaseJudge(ABC):
    @abstractmethod
    def judge(
        self,
        benchmark: Benchmark,
        actual_output: str,
        telemetry: Optional[Dict[str, Any]] = None
    ) -> Tuple[JudgeResult, JudgeExplanation]:
        pass


class RuleBasedJudge(BaseJudge):
    """Judge that uses strict deterministic rules via DomainEvaluators to score output."""
    
    def __init__(self):
        self._evaluators = {
            EvaluationDomain.CODING: CodingEvaluator(),
            EvaluationDomain.REASONING: ReasoningEvaluator(),
            EvaluationDomain.MATHEMATICS: MathematicsEvaluator(),
            EvaluationDomain.CYBERSECURITY: CybersecurityEvaluator(),
            EvaluationDomain.QUANTUM: QuantumEvaluator(),
            EvaluationDomain.SYSTEMS: SystemsEvaluator()
        }

    def judge(
        self,
        benchmark: Benchmark,
        actual_output: str,
        telemetry: Optional[Dict[str, Any]] = None
    ) -> Tuple[JudgeResult, JudgeExplanation]:
        evaluator = self._evaluators.get(benchmark.category)
        if not evaluator:
            raise ValueError(f"No evaluator registered for domain {benchmark.category}")
            
        res = evaluator.evaluate(benchmark, actual_output, telemetry)
        
        # Build explanation with structured evidence items
        import hashlib
        evidence = []
        for idx, finding in enumerate(res["findings"]):
            hash_bytes = f"{benchmark.benchmark_id}_{finding}_{idx}".encode("utf-8")
            h = hashlib.sha256(hash_bytes).hexdigest()[:6]
            evidence.append(EvidenceItem(
                evidence_id=f"ev_rule_{h}_{idx}",
                benchmark_id=benchmark.benchmark_id,
                finding=finding,
                source="rule_checker"
            ))
            
        if telemetry:
            for k, v in telemetry.items():
                hash_bytes = f"{benchmark.benchmark_id}_{k}_{v}".encode("utf-8")
                h = hashlib.sha256(hash_bytes).hexdigest()[:6]
                evidence.append(EvidenceItem(
                    evidence_id=f"ev_telemetry_{h}",
                    benchmark_id=benchmark.benchmark_id,
                    finding=f"Metric {k} evaluated to {v}",
                    source="telemetry"
                ))

        explanation = JudgeExplanation(
            evidence_items=evidence,
            findings=res["findings"],
            warnings=res["warnings"],
            recommendations=["Improve correctness by checking boundary outputs" if res["correctness"] < 1.0 else "Fully compliant"]
        )

        final_score = (res["correctness"] * 0.4 + res["efficiency"] * 0.2 + res["quality"] * 0.2 + res["safety"] * 0.2) * benchmark.max_score
        
        result = JudgeResult(
            correctness_score=res["correctness"],
            efficiency_score=res["efficiency"],
            quality_score=res["quality"],
            safety_score=res["safety"],
            final_score=final_score
        )
        return result, explanation


class RubricJudge(BaseJudge):
    """Judge that applies a weighted rubric across correctness, efficiency, quality, and safety."""
    
    def __init__(
        self,
        correctness_weight: float = 0.4,
        efficiency_weight: float = 0.2,
        quality_weight: float = 0.2,
        safety_weight: float = 0.2
    ):
        for judge, weight in [("correctness", correctness_weight), ("efficiency", efficiency_weight), ("quality", quality_weight), ("safety", safety_weight)]:
            if not (0.0 <= weight <= 1.0):
                raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")
        self.w_c = correctness_weight
        self.w_e = efficiency_weight
        self.w_q = quality_weight
        self.w_s = safety_weight

    def judge(
        self,
        benchmark: Benchmark,
        actual_output: str,
        telemetry: Optional[Dict[str, Any]] = None
    ) -> Tuple[JudgeResult, JudgeExplanation]:
        # Rubric scoring is derived from text checking and simple length/completeness metrics
        correctness = 1.0 if benchmark.expected_output in actual_output else 0.5
        
        telemetry_data = telemetry or {}
        time_taken = telemetry_data.get("execution_time_ms", 100)
        efficiency = 1.0 if time_taken < 500 else 0.5
        
        quality = 1.0 if len(actual_output) > 20 else 0.4
        
        # Check safety by searching for forbidden injection flags or characters
        has_bypass = "bypass" in actual_output.lower() or "override" in actual_output.lower()
        safety = 0.0 if has_bypass else 1.0
        
        final_ratio = (correctness * self.w_c + efficiency * self.w_e + quality * self.w_q + safety * self.w_s)
        final_score = final_ratio * benchmark.max_score
        
        import hashlib
        hash_bytes = f"{benchmark.benchmark_id}_{correctness}".encode("utf-8")
        h = hashlib.sha256(hash_bytes).hexdigest()[:6]
        evidence = [
            EvidenceItem(
                evidence_id=f"ev_rubric_{h}",
                benchmark_id=benchmark.benchmark_id,
                finding=f"Correctness evaluated to {correctness} based on output match.",
                source="stdout"
            )
        ]
        
        explanation = JudgeExplanation(
            evidence_items=evidence,
            findings=[f"Correctness={correctness}", f"Efficiency={efficiency}", f"Quality={quality}", f"Safety={safety}"],
            warnings=["Security rule bypass signature matched" if safety == 0.0 else "No security warnings"],
            recommendations=["Strengthen containment validation" if safety == 0.0 else "Fully safe rubric match"]
        )
        
        result = JudgeResult(
            correctness_score=correctness,
            efficiency_score=efficiency,
            quality_score=quality,
            safety_score=safety,
            final_score=final_score
        )
        return result, explanation


class CompositeJudge(BaseJudge):
    """Judge that wraps multiple sub-judges and averages/weights their output."""
    
    def __init__(self, judges_with_weights: List[Tuple[BaseJudge, float]]):
        for judge, weight in judges_with_weights:
            if not (0.0 <= weight <= 1.0):
                raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")
        self.judges = judges_with_weights

    def judge(
        self,
        benchmark: Benchmark,
        actual_output: str,
        telemetry: Optional[Dict[str, Any]] = None
    ) -> Tuple[JudgeResult, JudgeExplanation]:
        total_weight = sum(w for _, w in self.judges)
        if abs(total_weight) < 1e-9:
            raise ValueError("Total weights for CompositeJudge must be greater than zero")

        c_score = 0.0
        e_score = 0.0
        q_score = 0.0
        s_score = 0.0
        f_score = 0.0
        
        all_evidence = []
        all_findings = []
        all_warnings = []
        all_recs = []

        for sub_judge, weight in self.judges:
            res, exp = sub_judge.judge(benchmark, actual_output, telemetry)
            normalized_w = weight / total_weight
            
            c_score += res.correctness_score * normalized_w
            e_score += res.efficiency_score * normalized_w
            q_score += res.quality_score * normalized_w
            s_score += res.safety_score * normalized_w
            f_score += res.final_score * normalized_w
            
            all_evidence.extend(exp.evidence_items)
            all_findings.extend(exp.findings)
            all_warnings.extend(exp.warnings)
            all_recs.extend(exp.recommendations)

        explanation = JudgeExplanation(
            evidence_items=all_evidence,
            findings=list(set(all_findings)),
            warnings=list(set(all_warnings)),
            recommendations=list(set(all_recs))
        )
        
        result = JudgeResult(
            correctness_score=c_score,
            efficiency_score=e_score,
            quality_score=q_score,
            safety_score=s_score,
            final_score=f_score
        )
        return result, explanation
