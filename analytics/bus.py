from typing import Callable, List, Dict
from analytics.events import AnalyticsEvent, AnalyticsEventType

class AnalyticsEventBus:
    """In-memory Pub/Sub for Analytics events."""
    
    def __init__(self):
        self.subscribers: Dict[AnalyticsEventType, List[Callable[[AnalyticsEvent], None]]] = {
            t: [] for t in AnalyticsEventType
        }
        self.all_subscribers: List[Callable[[AnalyticsEvent], None]] = []
        
    def publish(self, event: AnalyticsEvent):
        for sub in self.subscribers.get(event.event_type, []):
            sub(event)
        for sub in self.all_subscribers:
            sub(event)
            
    def subscribe(self, callback: Callable[[AnalyticsEvent], None], event_type: AnalyticsEventType = None):
        if event_type:
            self.subscribers[event_type].append(callback)
        else:
            self.all_subscribers.append(callback)
            
    def unsubscribe(self, callback: Callable[[AnalyticsEvent], None], event_type: AnalyticsEventType = None):
        if event_type:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
        else:
            if callback in self.all_subscribers:
                self.all_subscribers.remove(callback)
                
    def replay(self, events: List[AnalyticsEvent]):
        """Replay historical events through the bus."""
        for event in events:
            self.publish(event)
