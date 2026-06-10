from leaderboard.models import LeaderboardSnapshot

class LeaderboardReport:
    """Generates Markdown representations of a leaderboard snapshot."""
    
    @staticmethod
    def generate_markdown(snapshot: LeaderboardSnapshot) -> str:
        lines = []
        lines.append(f"# Leaderboard (Campaign: {snapshot.campaign_id})")
        lines.append(f"Generated at: {snapshot.generated_at}")
        lines.append("")
        lines.append("| Rank | Contestant | Score | Grade | Correctness | Latency | TPS | Success |")
        lines.append("|---|---|---|---|---|---|---|---|")
        
        for entry in snapshot.entries:
            lines.append(
                f"| {entry.rank} "
                f"| {entry.contestant_id} "
                f"| {entry.score:.2f} "
                f"| {entry.rating_grade.value} "
                f"| {entry.average_correctness:.2f}% "
                f"| {entry.average_latency:.2f} ms "
                f"| {entry.average_tps:.2f} eps "
                f"| {entry.success_rate:.2f}% |"
            )
            
        return "\n".join(lines)
