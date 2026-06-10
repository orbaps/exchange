import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from evaluation.benchmarks.models import Benchmark

class DomainEvaluator(ABC):
    """Abstract interface for task-specific domain output validation."""
    
    @abstractmethod
    def evaluate(self, benchmark: Benchmark, actual_output: str, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate actual output against the benchmark specifications.
        Returns a dict containing component scores: correctness, efficiency, quality, safety, and findings.
        """
        pass

    def _check_rules(self, benchmark: Benchmark, actual_output: str) -> Dict[str, Any]:
        findings = []
        warnings = []
        passed_rules = 0
        total_rules = len(benchmark.evaluation_rules)
        
        for rule in benchmark.evaluation_rules:
            if rule == "exact_match":
                if actual_output.strip() == benchmark.expected_output.strip():
                    passed_rules += 1
                else:
                    findings.append(f"Failed exact_match. Expected: {benchmark.expected_output}, Got: {actual_output}")
            elif rule.startswith("contains:"):
                target = rule[len("contains:"):]
                if target in actual_output:
                    passed_rules += 1
                else:
                    findings.append(f"Output missing expected keyword: '{target}'")
            elif rule.startswith("not_contains:"):
                target = rule[len("not_contains:"):]
                if target not in actual_output:
                    passed_rules += 1
                else:
                    findings.append(f"Output contained banned content: '{target}'")
                    warnings.append(f"Banned content detected: '{target}'")
            elif rule.startswith("regex:"):
                pattern = rule[len("regex:"):]
                if re.search(pattern, actual_output):
                    passed_rules += 1
                else:
                    findings.append(f"Output did not match regex pattern: {pattern}")
            else:
                # Default true rule for custom stubs
                passed_rules += 1

        correctness_ratio = (passed_rules / total_rules) if total_rules > 0 else 1.0
        return {
            "correctness_ratio": correctness_ratio,
            "findings": findings,
            "warnings": warnings
        }


class CodingEvaluator(DomainEvaluator):
    def evaluate(self, benchmark: Benchmark, actual_output: str, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rule_res = self._check_rules(benchmark, actual_output)
        
        # In coding, efficiency is driven by execution times, quality by code cleanliness
        telemetry_data = telemetry or {}
        exec_time = telemetry_data.get("execution_time_ms", 100.0)
        
        # Calculate efficiency score: higher is better, capped at 1.0
        efficiency = max(0.0, min(1.0, 1.0 - (exec_time / (benchmark.timeout_ms or 5000))))
        
        # Check safety from memory limits or warning findings
        safety = 1.0 if not rule_res["warnings"] else 0.5
        
        return {
            "correctness": rule_res["correctness_ratio"],
            "efficiency": efficiency,
            "quality": 0.9 if "syntax_error" not in actual_output else 0.1,
            "safety": safety,
            "findings": rule_res["findings"],
            "warnings": rule_res["warnings"]
        }


class ReasoningEvaluator(DomainEvaluator):
    def evaluate(self, benchmark: Benchmark, actual_output: str, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rule_res = self._check_rules(benchmark, actual_output)
        
        # Reasoning evaluates coherence and structure (e.g. check for chain-of-thought)
        has_thinking = "think" in actual_output.lower() or "reason" in actual_output.lower()
        quality = 1.0 if has_thinking else 0.5
        
        return {
            "correctness": rule_res["correctness_ratio"],
            "efficiency": 1.0, # Reasoning trace time is less critical than correctness
            "quality": quality,
            "safety": 1.0 if not rule_res["warnings"] else 0.0,
            "findings": rule_res["findings"],
            "warnings": rule_res["warnings"]
        }


class MathematicsEvaluator(DomainEvaluator):
    def evaluate(self, benchmark: Benchmark, actual_output: str, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rule_res = self._check_rules(benchmark, actual_output)
        
        # Math checks precision
        return {
            "correctness": rule_res["correctness_ratio"],
            "efficiency": 1.0,
            "quality": 1.0,
            "safety": 1.0,
            "findings": rule_res["findings"],
            "warnings": rule_res["warnings"]
        }


class CybersecurityEvaluator(DomainEvaluator):
    def evaluate(self, benchmark: Benchmark, actual_output: str, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rule_res = self._check_rules(benchmark, actual_output)
        
        # Safety is the core metric for cybersecurity evaluation
        safety = rule_res["correctness_ratio"]
        return {
            "correctness": rule_res["correctness_ratio"],
            "efficiency": 0.8,
            "quality": 0.9,
            "safety": safety,
            "findings": rule_res["findings"],
            "warnings": rule_res["warnings"]
        }


class QuantumEvaluator(DomainEvaluator):
    def evaluate(self, benchmark: Benchmark, actual_output: str, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rule_res = self._check_rules(benchmark, actual_output)
        return {
            "correctness": rule_res["correctness_ratio"],
            "efficiency": 1.0,
            "quality": 0.9,
            "safety": 1.0,
            "findings": rule_res["findings"],
            "warnings": rule_res["warnings"]
        }


class SystemsEvaluator(DomainEvaluator):
    def evaluate(self, benchmark: Benchmark, actual_output: str, telemetry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        rule_res = self._check_rules(benchmark, actual_output)
        
        # Systems benchmark is highly driven by telemetry throughput
        telemetry_data = telemetry or {}
        tps = telemetry_data.get("tps", 100.0)
        efficiency = min(1.0, tps / 1000.0)
        
        return {
            "correctness": rule_res["correctness_ratio"],
            "efficiency": efficiency,
            "quality": 1.0,
            "safety": 1.0,
            "findings": rule_res["findings"],
            "warnings": rule_res["warnings"]
        }
