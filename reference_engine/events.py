from typing import Callable, Any, Dict, List

class EventBus:
    """A synchronous event bus for publishing and subscribing to engine events."""
    
    def __init__(self) -> None:
        self._subscribers: Dict[type, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        """Subscribes a handler function to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        """Publishes an event to all registered subscribers of its type."""
        event_type = type(event)
        # Call specific type subscribers
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                handler(event)
        
        # Also call generic subscribers (those subscribed to `object` or `Any` if supported)
        if object in self._subscribers and event_type is not object:
            for handler in self._subscribers[object]:
                handler(event)

class ReplayLog:
    """An append-only log of events that can be replayed to reconstruct state."""
    
    def __init__(self) -> None:
        self._events: List[Any] = []
        
    def append(self, event: Any) -> None:
        """Appends an event to the log. Should be wired to subscribe to input events."""
        self._events.append(event)
        
    def replay(self, target_engine: Any) -> List[Any]:
        """
        Replays all logged events sequentially into the target_engine.
        Returns a list of all execution reports or outputs generated during replay.
        """
        outputs = []
        for event in self._events:
            result = target_engine.on_message(event)
            if result:
                outputs.extend(result)
        return outputs

    @property
    def events(self) -> List[Any]:
        """Returns the chronological sequence of logged events."""
        return list(self._events)
