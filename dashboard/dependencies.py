from dashboard.services.state_cache import StateCache
from dashboard.services.channel_manager import ChannelManager
from dashboard.services.event_bridge import EventBridge
from dashboard.services.aggregator import DashboardAggregator

# Global instances
state_cache = StateCache()
channel_manager = ChannelManager()
event_bridge = EventBridge(state_cache, channel_manager)
aggregator = DashboardAggregator(state_cache)

def get_state_cache() -> StateCache:
    return state_cache

def get_channel_manager() -> ChannelManager:
    return channel_manager

def get_event_bridge() -> EventBridge:
    return event_bridge

def get_aggregator() -> DashboardAggregator:
    return aggregator
