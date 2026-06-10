from enum import Enum

class RatingGrade(Enum):
    S_PLUS = "S+"
    S = "S"
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class RatingCalculator:
    """Calculates letter grades based on numeric scores."""
    
    @staticmethod
    def calculate(score: float) -> RatingGrade:
        """
        95-100  S+
        90-95   S
        85-90   A+
        80-85   A
        70-80   B
        60-70   C
        <60     D
        """
        if score >= 95.0:
            return RatingGrade.S_PLUS
        elif score >= 90.0:
            return RatingGrade.S
        elif score >= 85.0:
            return RatingGrade.A_PLUS
        elif score >= 80.0:
            return RatingGrade.A
        elif score >= 70.0:
            return RatingGrade.B
        elif score >= 60.0:
            return RatingGrade.C
        else:
            return RatingGrade.D
