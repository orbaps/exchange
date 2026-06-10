import threading
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class RouteEntry:
    submission_id: str
    endpoint:      str    # e.g. local://submission/sub_abc123/v2
    container_id:  str


class EndpointRouter:
    """Maps logical submission IDs to internal container endpoints.

    Uses opaque local:// URIs — no real HTTP URLs in Phase 4.4.
    The ExecutionSession resolves these to call ContainerInstance.
    """

    def __init__(self):
        self._routes: Dict[str, RouteEntry] = {}   # submission_id → route
        self._lock = threading.Lock()

    def register(self, submission_id: str, endpoint: str, container_id: str) -> RouteEntry:
        entry = RouteEntry(submission_id, endpoint, container_id)
        with self._lock:
            self._routes[submission_id] = entry
        return entry

    def resolve(self, submission_id: str) -> Optional[RouteEntry]:
        with self._lock:
            return self._routes.get(submission_id)

    def remove(self, submission_id: str) -> bool:
        with self._lock:
            return self._routes.pop(submission_id, None) is not None

    def list_routes(self) -> List[RouteEntry]:
        with self._lock:
            return list(self._routes.values())
