from typing import List, Dict
from analytics.campaign import CampaignAnalytics
from analytics.leaderboard import LiveLeaderboard
from analytics.health import SessionHealthHistory, SessionHealthStatus

class AnalyticsReport:
    """Provides human-readable markdown abstractions summarizing the Live Analytics streams."""
    
    @staticmethod
    def generate(campaign: CampaignAnalytics, leaderboard: LiveLeaderboard, health_history: SessionHealthHistory) -> str:
        lines = []
        lines.append("### Live Analytics Report")
        
        # Campaign 
        lines.append("\n**Campaign Status**")
        lines.append(f"- Active Sessions: {campaign.active_sessions}")
        lines.append(f"- Completed Sessions: {campaign.completed_sessions}")
        lines.append(f"- Failed Sessions: {campaign.failed_sessions}")
        lines.append(f"- Average Score (Trailing): {campaign.average_score():.2f}")
        lines.append(f"- Average Latency (Trailing): {campaign.average_latency():.2f} ms")
        lines.append(f"- Average TPS (Trailing): {campaign.average_tps():.2f} eps")
        
        # Leaderboard
        lines.append("\n**Current Leaderboard State**")
        sorted_ranks = sorted(leaderboard.current_rankings.items(), key=lambda x: x[1])
        for idx, (contestant_id, rank) in enumerate(sorted_ranks):
            if idx >= 5: # Top 5 only
                break
            lines.append(f"{rank}. {contestant_id}")
            
        # Health
        lines.append("\n**System Health Overview**")
        crashed = 0
        timed_out = 0
        for sid, health in health_history.health_map.items():
            if health.status == SessionHealthStatus.CRASHED:
                crashed += 1
            elif health.status == SessionHealthStatus.TIMED_OUT:
                timed_out += 1
                
        lines.append(f"- Total Crashed Submissions: {crashed}")
        lines.append(f"- Total Timed Out Submissions: {timed_out}")
        
        return "\n".join(lines)
