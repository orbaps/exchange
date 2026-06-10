from typing import List, Optional
from analytics.events import AnalyticsEvent
from analytics.bus import AnalyticsEventBus

class AnalyticsStream:
    """Maintains an ordered history of analytics events."""
    
    def __init__(self, bus: AnalyticsEventBus):
        self.history: List[AnalyticsEvent] = []
        self.bus = bus
        self.bus.subscribe(self.append)
        
    def append(self, event: AnalyticsEvent):
        # Insert while maintaining order by timestamp
        self.history.append(event)
        
    def latest(self, count: int = 1) -> List[AnalyticsEvent]:
        return self.history[-count:] if self.history else []
        
    def replay(self) -> List[AnalyticsEvent]:
        return list(self.history)
