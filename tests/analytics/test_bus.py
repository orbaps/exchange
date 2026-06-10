import unittest
from analytics.bus import AnalyticsEventBus
from analytics.events import AnalyticsEvent, AnalyticsEventType

class TestAnalyticsBus(unittest.TestCase):
    def test_publish_subscribe(self):
        bus = AnalyticsEventBus()
        received = []
        
        def callback(event):
            received.append(event)
            
        bus.subscribe(callback, AnalyticsEventType.EXECUTION_UPDATE)
        
        # Publish matching event
        e1 = AnalyticsEvent("1", 0, AnalyticsEventType.EXECUTION_UPDATE, "src", {})
        bus.publish(e1)
        self.assertEqual(len(received), 1)
        
        # Publish non-matching event
        e2 = AnalyticsEvent("2", 0, AnalyticsEventType.SCORE_UPDATE, "src", {})
        bus.publish(e2)
        self.assertEqual(len(received), 1)
        
        # Unsubscribe
        bus.unsubscribe(callback, AnalyticsEventType.EXECUTION_UPDATE)
        bus.publish(e1)
        self.assertEqual(len(received), 1)

if __name__ == '__main__':
    unittest.main()
