from tournament.models import TournamentResult

class TournamentReportGenerator:
    
    @staticmethod
    def generate(result: TournamentResult) -> str:
        lines = []
        lines.append(f"# Tournament Results: {result.tournament_id}")
        lines.append("")
        
        if result.winner:
            lines.append(f"Winner:\n{result.winner}\n")
            
        if len(result.final_rankings) > 1:
            lines.append(f"Runner Up:\n{result.final_rankings[1]}\n")
            
        if len(result.final_rankings) > 2:
            lines.append(f"Third:\n{result.final_rankings[2]}\n")
            
        for stage in result.stage_results:
            n_start = len(stage.contestants_started)
            n_adv = len(stage.contestants_advanced)
            if n_adv == 0 and stage.winner:
                n_adv = 1 # The winner is the advanced one
            lines.append(f"{stage.stage_type}:")
            lines.append(f"{n_start} -> {n_adv}")
            lines.append("")
            
        lines.append("# Final Rankings\n")
        for i, team in enumerate(result.final_rankings):
            lines.append(f"{i + 1}. {team}")
            
        return "\n".join(lines)
