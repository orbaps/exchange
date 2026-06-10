from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SkillProfile:
    """Skill capability profile computed for a contestant."""
    category: str
    score: float
    grade: str

class ProfileGenerator:
    """Generates ability profiles from benchmark results and historical statistics."""
    
    @staticmethod
    def calculate_grade(score: float) -> str:
        """Deterministic boundary mapping of scores to letters."""
        if score >= 95.0:
            return "S+"
        elif score >= 90.0:
            return "S"
        elif score >= 80.0:
            return "A"
        elif score >= 70.0:
            return "B"
        elif score >= 60.0:
            return "C"
        else:
            return "D"

    @classmethod
    def generate(
        cls,
        benchmark_results: List[Dict[str, Any]],
        historical_scores: Optional[List[float]] = None
    ) -> List[SkillProfile]:
        # Supported categories: correctness, latency, reliability, reasoning, optimization, safety
        categories = ["correctness", "latency", "reliability", "reasoning", "optimization", "safety"]
        
        # Accumulate metrics
        cat_scores: Dict[str, List[float]] = {cat: [] for cat in categories}
        
        for res in benchmark_results:
            # We map benchmark run output components to categories
            judge_res = res.get("judge_result")
            if not judge_res:
                continue
                
            # If the result object is an instance or a dict
            c_val = getattr(judge_res, "correctness_score", 0.0) if hasattr(judge_res, "correctness_score") else judge_res.get("correctness_score", 0.0)
            e_val = getattr(judge_res, "efficiency_score", 0.0) if hasattr(judge_res, "efficiency_score") else judge_res.get("efficiency_score", 0.0)
            q_val = getattr(judge_res, "quality_score", 0.0) if hasattr(judge_res, "quality_score") else judge_res.get("quality_score", 0.0)
            s_val = getattr(judge_res, "safety_score", 0.0) if hasattr(judge_res, "safety_score") else judge_res.get("safety_score", 0.0)

            cat_scores["correctness"].append(c_val * 100.0)
            cat_scores["optimization"].append(e_val * 100.0)
            cat_scores["reliability"].append(q_val * 100.0)
            cat_scores["safety"].append(s_val * 100.0)
            
            # Category reasoning maps directly to reasoning/math category correctness
            domain = res.get("domain")
            if domain in ("REASONING", "MATHEMATICS"):
                cat_scores["reasoning"].append(c_val * 100.0)

            # Map execution time latency
            telemetry = res.get("telemetry", {})
            exec_time = telemetry.get("execution_time_ms", 100.0)
            latency_score = max(0.0, min(100.0, 100.0 - (exec_time / 50.0))) # scale
            cat_scores["latency"].append(latency_score)
            
        # Add historical metrics if available
        if historical_scores:
            cat_scores["correctness"].extend(historical_scores)

        profiles = []
        for cat in categories:
            scores = cat_scores[cat]
            avg_score = sum(scores) / len(scores) if scores else 50.0
            # Clamp between 0 and 100
            avg_score = max(0.0, min(100.0, avg_score))
            profiles.append(SkillProfile(
                category=cat,
                score=avg_score,
                grade=cls.calculate_grade(avg_score)
            ))
            
        return profiles
