import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from evaluation.journal import EvaluationJournal

@dataclass
class ReplayStep:
    event_type: str
    run_id: str
    benchmark_id: str
    payload: Dict[str, Any]

@dataclass
class EvaluationTimeline:
    campaign_id: str
    steps: List[ReplayStep] = field(default_factory=list)

class EvaluationReplay:
    """Reconstructs evaluation system state at any point in history from transaction journals."""
    
    @staticmethod
    def load_timeline(journal: EvaluationJournal) -> EvaluationTimeline:
        entries = journal.read_all()
        if not entries:
            return EvaluationTimeline(campaign_id="unknown")
            
        campaign_id = "unknown"
        # Find campaign id
        for entry in entries:
            if entry.get("event_type") == "CAMPAIGN_START":
                campaign_id = entry.get("run_id", "unknown")
                break
                
        timeline = EvaluationTimeline(campaign_id=campaign_id)
        for entry in entries:
            timeline.steps.append(ReplayStep(
                event_type=entry["event_type"],
                run_id=entry["run_id"],
                benchmark_id=entry["benchmark_id"],
                payload=entry["payload"]
            ))
        return timeline

    def __init__(self, timeline: EvaluationTimeline):
        self.timeline = timeline
        self.current_index = -1

    def step_forward(self) -> bool:
        if self.current_index < len(self.timeline.steps) - 1:
            self.current_index += 1
            return True
        return False

    def step_backward(self) -> bool:
        if self.current_index > -1:
            self.current_index -= 1
            return True
        return False

    def seek(self, index: int) -> bool:
        if -1 <= index < len(self.timeline.steps):
            self.current_index = index
            return True
        return False

    def reconstruct_state(self) -> Dict[str, Any]:
        """Reconstruct the state up to the current_index."""
        state = {
            "campaign_id": self.timeline.campaign_id,
            "status": "DRAFT",
            "benchmarks": {},
            "overall_score": 0.0,
            "overall_grade": "D",
            "profiles": []
        }
        
        for idx in range(self.current_index + 1):
            step = self.timeline.steps[idx]
            e_type = step.event_type
            payload = step.payload
            
            if e_type == "CAMPAIGN_START":
                state["status"] = "RUNNING"
                
            elif e_type == "TASK_START":
                b_id = step.benchmark_id
                state["benchmarks"][b_id] = {
                    "benchmark_id": b_id,
                    "status": "RUNNING",
                    "score": 0.0,
                    "correctness": 0.0,
                    "efficiency": 0.0,
                    "quality": 0.0,
                    "safety": 0.0,
                    "findings": [],
                    "evidence": []
                }
                
            elif e_type == "TASK_END":
                b_id = step.benchmark_id
                if b_id in state["benchmarks"]:
                    state["benchmarks"][b_id].update({
                        "status": "COMPLETED",
                        "score": payload.get("score", 0.0),
                        "correctness": payload.get("correctness", 0.0),
                        "efficiency": payload.get("efficiency", 0.0),
                        "quality": payload.get("quality", 0.0),
                        "safety": payload.get("safety", 0.0),
                        "findings": payload.get("findings", []),
                        "evidence": payload.get("evidence", [])
                    })
                    
            elif e_type == "CAMPAIGN_END":
                state["status"] = "COMPLETED"
                state["overall_score"] = payload.get("average_score", 0.0)
                state["overall_grade"] = payload.get("overall_grade", "D")
                state["profiles"] = payload.get("profiles", [])
                
                # Verify fingerprint if stored in the campaign end event
                original_fp = payload.get("state_fingerprint")
                if original_fp:
                    computed_fp = self.compute_fingerprint(state)
                    if computed_fp != original_fp:
                        raise ValueError(f"State fingerprint verification failed! Replay state hash mismatch: computed {computed_fp} vs original {original_fp}")
                    state["fingerprint_verified"] = True
                
        return state

    @staticmethod
    def compute_fingerprint(state: Dict[str, Any]) -> str:
        """Computes a deterministic SHA256 hash fingerprint of the given state dictionary."""
        import hashlib
        
        def serialize(obj):
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            elif isinstance(obj, (set, frozenset)):
                return sorted(list(obj))
            return str(obj)
            
        # Filter out fingerprint tracking fields to avoid self-reference
        clean_state = {k: v for k, v in state.items() if k not in ("fingerprint_verified", "state_fingerprint")}
        state_str = json.dumps(clean_state, default=serialize, sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

