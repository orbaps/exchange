from scoring.models import ScoreResult

class ScoreReport:
    """Generates markdown reports for individual scoring results."""
    
    @staticmethod
    def generate_markdown(result: ScoreResult) -> str:
        lines = [
            f"### Score Report: {result.contestant_id} (Scenario: {result.scenario_id})",
            "",
            f"**Scoring Version**: {result.breakdown.scoring_version}",
            "",
            "#### Final Score",
            f"**{result.breakdown.final_score:.2f}** / 100.0",
            "",
            "#### Score Breakdown",
            f"- **Correctness (70%)**: {result.breakdown.correctness_score:.2f}",
            f"- **Latency (15%)**: {result.breakdown.latency_score:.2f}",
            f"- **Throughput (10%)**: {result.breakdown.throughput_score:.2f}",
            f"- **Reliability (5%)**: {result.breakdown.reliability_score:.2f}",
            "",
            "#### Raw Metrics",
            f"- **Correctness**: {result.breakdown.raw_correctness:.2f}%",
            f"- **p99 Latency**: {result.breakdown.raw_p99_latency_ms:.3f} ms",
            f"- **Throughput**: {result.breakdown.raw_eps:.2f} EPS",
            f"- **Success Rate**: {result.breakdown.raw_success_rate:.2f}%"
        ]
        
        return "\n".join(lines)
