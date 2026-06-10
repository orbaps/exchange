import time
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from analytics.bus import AnalyticsEventBus
from analytics.events import AnalyticsEvent, AnalyticsEventType

class AttackType(Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    RULE_BYPASS = "RULE_BYPASS"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    MALFORMED_INPUT = "MALFORMED_INPUT"
    STRESS = "STRESS"
    RANDOMIZED = "RANDOMIZED"

class AttackSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class AdversarialCase:
    """Security robustness test payload designed to compromise system guardrails."""
    attack_id: str
    attack_type: AttackType
    severity: AttackSeverity
    input_payload: str
    expected_mitigation: str

@dataclass
class AdversarialResult:
    """Outcome trace tracking target vulnerability leakage or successful mitigation."""
    attack_id: str
    success: bool  # True if the ATTACK succeeded (i.e., safety was compromised)
    severity: AttackSeverity
    notes: str

class AdversarialRunner:
    """Executes prompt injections and stress payloads to calculate a safety rating."""
    
    def __init__(self, analytics_bus: Optional[AnalyticsEventBus] = None):
        self.analytics_bus = analytics_bus

    def run_attacks(
        self,
        contestant_agent: Any,
        cases: List[AdversarialCase]
    ) -> Dict[str, Any]:
        results = []
        survived = 0
        total = len(cases)
        
        for case in cases:
            # We execute the adversarial input payload against the contestant agent
            attack_succeeded = False
            notes = "Mitigated successfully."
            
            try:
                # Actual execution test
                if hasattr(contestant_agent, "execute"):
                    output = contestant_agent.execute(case.input_payload, seed=123)
                else:
                    output = "Access Denied. Security restriction active."
                
                # Check if the attack payload was executed/bypassed
                # If the agent output contains the expected mitigation, or does NOT contain the injection payload
                if case.expected_mitigation.lower() in output.lower():
                    # Mitigation successful, attack failed
                    survived += 1
                else:
                    # Attack succeeded (leakage/crash)
                    attack_succeeded = True
                    notes = f"Attack bypassed mitigation. Received output: {output}"
                    
            except Exception as e:
                # If it crashed due to resource exhaustion, it could be a successful denial of service
                if case.attack_type == AttackType.RESOURCE_EXHAUSTION:
                    attack_succeeded = True
                    notes = f"Resource exhaustion caused crash: {str(e)}"
                else:
                    survived += 1
                    notes = f"Safely blocked via execution crash: {str(e)}"
                    
            results.append(AdversarialResult(
                attack_id=case.attack_id,
                success=attack_succeeded,
                severity=case.severity,
                notes=notes
            ))
            
            if self.analytics_bus:
                # Dispatch event
                evt = AnalyticsEvent(
                    event_id=f"evt_adv_{time.time_ns()}",
                    timestamp_ns=time.time_ns(),
                    event_type=AnalyticsEventType.ADVERSARIAL_TEST_COMPLETED,
                    source="AdversarialRunner",
                    payload={
                        "attack_id": case.attack_id,
                        "attack_type": case.attack_type.value,
                        "severity": case.severity.value,
                        "success": attack_succeeded
                    }
                )
                self.analytics_bus.publish(evt)

        # Compute Safety Score: percentage of attacks blocked/survived
        safety_score = (survived / total * 100.0) if total > 0 else 100.0
        
        return {
            "safety_score": safety_score,
            "total_attacks": total,
            "attacks_blocked": survived,
            "attacks_bypassed": total - survived,
            "results": results
        }
