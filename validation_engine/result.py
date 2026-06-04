from dataclasses import dataclass, field
from typing import List, Any
from enum import Enum

class MismatchType(Enum):
    ORDER_STATE = "ORDER_STATE"
    TRADE_STATE = "TRADE_STATE"
    BOOK_STATE = "BOOK_STATE"

@dataclass
class Mismatch:
    """Represents a discrepancy between the reference engine and a contestant engine."""
    mismatch_type: MismatchType
    expected: Any
    actual: Any
    details: str

@dataclass
class ValidationResult:
    """Aggregates the total correctness of a state comparison."""
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    mismatches: List[Mismatch] = field(default_factory=list)
    
    @property
    def correctness_score(self) -> float:
        """Returns the correctness score as a percentage [0.0, 100.0]."""
        if self.total_checks == 0:
            return 100.0
        return (self.passed_checks / self.total_checks) * 100.0

    def add_pass(self) -> None:
        self.total_checks += 1
        self.passed_checks += 1
        
    def add_fail(self, mismatch: Mismatch) -> None:
        self.total_checks += 1
        self.failed_checks += 1
        self.mismatches.append(mismatch)
