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
                total_mismatches=total_mismatches,
                successful_runs=len(successful_scenario_runs),
                failed_runs=contestant_result.failed_runs
            )
            
        return ReportData(
            campaign_id=result.campaign_id,
            total_runs=result.total_runs,
            overall_success_rate=overall_success_rate,
            contestants=contestants_data
        )

    @staticmethod
    def generate_markdown(result: CampaignResult) -> str:
        data = CampaignReport.generate_data(result)
        
        lines = [
            f"# Campaign Report: {data.campaign_id}",
            "",
            f"**Total Runs**: {data.total_runs}",
            f"**Overall Success Rate**: {data.overall_success_rate:.2f}%",
            "",
            "## Contestant Results",
            ""
        ]
        
        for contestant_id, c_data in data.contestants.items():
            lines.append(f"### Contestant: {contestant_id}")
            lines.append(f"- **Correctness**: {c_data.average_correctness:.2f}%")
            lines.append(f"- **Total Mismatches**: {c_data.total_mismatches}")
            lines.append(f"- **Successful Runs**: {c_data.successful_runs}")
            lines.append(f"- **Failed Runs**: {c_data.failed_runs}")
            lines.append("")
            
        return "\n".join(lines)
