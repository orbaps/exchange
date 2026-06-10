from campaign.result import CampaignResult, RunStatus
from campaign.metrics import CampaignMetrics
from campaign.report_data import ReportData, ContestantReportData

class CampaignReport:
    """Generates human-readable Markdown reports from CampaignResults."""
    
    @staticmethod
    def generate_data(result: CampaignResult) -> ReportData:
        overall_success_rate = 0.0
        if result.total_runs > 0:
            overall_success_rate = (result.successful_runs / result.total_runs) * 100.0
            
        contestants_data = {}
        for contestant_id, contestant_result in result.results.items():
            metrics = CampaignMetrics.calculate(contestant_result.scenario_results)
            
            successful_scenario_runs = [r for r in contestant_result.scenario_results if r.status == RunStatus.SUCCESS]
            total_mismatches = 0
            for run in successful_scenario_runs:
                if run.benchmark_result:
                    total_mismatches += len(run.benchmark_result.validation_result.mismatches)
                    
            contestants_data[contestant_id] = ContestantReportData(
                contestant_id=contestant_id,
                average_correctness=metrics["average_correctness"],
                average_execution_time=metrics["average_execution_time"],
                total_mismatches=total_mismatches,
                successful_runs=len(successful_scenario_runs),
                failed_runs=contestant_result.failed_runs,
                average_latency_ms=contestant_result.average_latency_ms,
                best_latency_ms=contestant_result.best_latency_ms,
                worst_latency_ms=contestant_result.worst_latency_ms,
                average_tps=contestant_result.average_tps,
                best_tps=contestant_result.best_tps,
                worst_tps=contestant_result.worst_tps,
                success_rate=contestant_result.success_rate,
                average_score=contestant_result.average_score,
                best_score=contestant_result.best_score,
                worst_score=contestant_result.worst_score,
                score_stddev=contestant_result.score_stddev
            )
            
        return ReportData(
            campaign_id=result.campaign_id,
            total_runs=result.total_runs,
            overall_success_rate=overall_success_rate,
            contestants=contestants_data
        )

    @staticmethod
    def generate_markdown(result: CampaignResult, snapshot=None) -> str:
        data = CampaignReport.generate_data(result)
        
        lines = []
        if snapshot:
            from leaderboard.report import LeaderboardReport
            lines.append(LeaderboardReport.generate_markdown(snapshot))
            lines.append("")
            lines.append("---")
            lines.append("")
        
        lines.extend([
            f"# Campaign Report: {data.campaign_id}",
            "",
            f"**Total Runs**: {data.total_runs}",
            f"**Overall Success Rate**: {data.overall_success_rate:.2f}%",
            "",
            "## Contestant Results",
            ""
        ])
        
        for contestant_id, c_data in data.contestants.items():
            lines.append(f"### Contestant: {contestant_id}")
            lines.append(f"- **Correctness**: {c_data.average_correctness:.2f}%")
            lines.append(f"- **Avg Execution Time**: {c_data.average_execution_time:.3f} ms")
            lines.append(f"- **Total Mismatches**: {c_data.total_mismatches}")
            lines.append(f"- **Successful Runs**: {c_data.successful_runs}")
            lines.append(f"- **Failed Runs**: {c_data.failed_runs}")
            lines.append(f"- **Success Rate**: {c_data.success_rate:.2f}%")
            lines.append(f"- **Avg Latency**: {c_data.average_latency_ms:.3f} ms")
            lines.append(f"- **Best Latency**: {c_data.best_latency_ms:.3f} ms")
            lines.append(f"- **Worst Latency**: {c_data.worst_latency_ms:.3f} ms")
            lines.append(f"- **Avg TPS**: {c_data.average_tps:.2f} eps")
            lines.append(f"- **Best TPS**: {c_data.best_tps:.2f} eps")
            lines.append(f"- **Worst TPS**: {c_data.worst_tps:.2f} eps")
            lines.append(f"- **Final Score (Avg)**: {c_data.average_score:.2f}")
            lines.append(f"- **Best Score**: {c_data.best_score:.2f}")
            lines.append(f"- **Worst Score**: {c_data.worst_score:.2f}")
            lines.append(f"- **Score StdDev**: {c_data.score_stddev:.2f}")
            lines.append("")
            
        return "\n".join(lines)
