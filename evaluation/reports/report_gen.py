import json
import time
from typing import Dict, Any, List

class ResearchReportGenerator:
    """Generates structured evaluation research reports in Markdown, HTML, and JSON formats."""
    
    @staticmethod
    def generate_markdown(campaign_data: Dict[str, Any]) -> str:
        lines = []
        lines.append(f"# IICPC Evaluation Research Report: {campaign_data.get('campaign_id')}")
        gen_time = campaign_data.get("generated_at") or time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        lines.append(f"Generated at: {gen_time}")
        lines.append(f"Contestant ID: **{campaign_data.get('contestant_id')}**")
        lines.append("")
        
        lines.append("## Overview")
        lines.append(f"- **Overall Grade:** `{campaign_data.get('overall_grade')}`")
        lines.append(f"- **Average Benchmark Score:** `{campaign_data.get('average_score', 0.0):.2f}`")
        lines.append("")
        
        lines.append("## Score Breakdown by Category")
        lines.append("| Category | Score | Grade |")
        lines.append("| --- | --- | --- |")
        for profile in campaign_data.get("profiles", []):
            lines.append(f"| {profile.category.upper()} | {profile.score:.1f}% | {profile.grade} |")
        lines.append("")

        lines.append("## Benchmark Summary Details")
        lines.append("| Benchmark ID | Domain | Correctness | Efficiency | Safety | Final Score |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for res in campaign_data.get("results", []):
            j_res = res["judge_result"]
            lines.append(
                f"| {res['benchmark_id']} "
                f"| {res['domain']} "
                f"| {j_res.correctness_score * 100:.1f}% "
                f"| {j_res.efficiency_score * 100:.1f}% "
                f"| {j_res.safety_score * 100:.1f}% "
                f"| {j_res.final_score:.2f} |"
            )
        lines.append("")

        lines.append("## Recommendations")
        lines.append("Based on the evaluation profile, the following optimizations are advised:")
        for profile in campaign_data.get("profiles", []):
            if profile.score < 80.0:
                lines.append(f"- **{profile.category.upper()}**: Implement robust unit tests and verify correctness boundaries to raise grade from `{profile.grade}`.")
            else:
                lines.append(f"- **{profile.category.upper()}**: Strong capability profile (`{profile.grade}`). Maintain existing guardrails.")
                
        return "\n".join(lines)

    @staticmethod
    def generate_html(campaign_data: Dict[str, Any]) -> str:
        md = ResearchReportGenerator.generate_markdown(campaign_data)
        # Convert Markdown list and tables to clean HTML wrapper
        html_body = md.replace("\n", "<br/>")
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>IICPC Evaluation Report</title>
    <style>
        body {{ font-family: sans-serif; padding: 40px; background: #fafafa; color: #333; }}
        .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>"""

    @staticmethod
    def generate_json(campaign_data: Dict[str, Any]) -> str:
        # Format profiles as dictionary list
        profiles_list = []
        for p in campaign_data.get("profiles", []):
            profiles_list.append({
                "category": p.category,
                "score": p.score,
                "grade": p.grade
            })
            
        results_list = []
        for r in campaign_data.get("results", []):
            j_res = r["judge_result"]
            results_list.append({
                "benchmark_id": r["benchmark_id"],
                "domain": r["domain"],
                "score": j_res.final_score,
                "correctness": j_res.correctness_score,
                "efficiency": j_res.efficiency_score,
                "quality": j_res.quality_score,
                "safety": j_res.safety_score
            })
            
        data = {
            "campaign_id": campaign_data.get("campaign_id"),
            "contestant_id": campaign_data.get("contestant_id"),
            "average_score": campaign_data.get("average_score"),
            "overall_grade": campaign_data.get("overall_grade"),
            "profiles": profiles_list,
            "results": results_list
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def generate_pdf_stub(campaign_data: Dict[str, Any]) -> bytes:
        """Simulate a PDF build artifact binary trace."""
        header = b"%PDF-1.4\n"
        content = f"%% IICPC Evaluation Report {campaign_data.get('campaign_id')}\n%% Grade: {campaign_data.get('overall_grade')}\n".encode()
        footer = b"%%EOF\n"
        return header + content + footer
