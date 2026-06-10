from dataclasses import dataclass
from analytics.timeseries import TimeSeries
from scoring.models import ScoreResult

@dataclass
class CampaignAnalytics:
    active_sessions: int = 0
    completed_sessions: int = 0
    failed_sessions: int = 0
    
    def __init__(self):
        self.score_timeseries = TimeSeries("average_score")
        self.latency_timeseries = TimeSeries("average_latency")
        self.tps_timeseries = TimeSeries("average_tps")
        
    def average_score(self) -> float:
        return self.score_timeseries.latest()
        
    def average_latency(self) -> float:
        return self.latency_timeseries.latest()
        
    def average_tps(self) -> float:
        return self.tps_timeseries.latest()
