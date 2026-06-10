from typing import Any, Dict, Optional
from execution.session import ExecutionSession


class ExecutionManager:
    """Manages the lifecycle of ExecutionSessions.

    Phase 4.4: accepts an optional EndpointRouter + ContainerManager so every
    session it creates is automatically wired into the hosting layer.

    Ownership:
        ExecutionManager  — creates and holds all sessions
        WorkerPool        — receives session references; does NOT own them
    """

    def __init__(self, router=None, container_manager=None):
        """
        Args:
            router:            hosting.router.EndpointRouter or None
            container_manager: hosting.manager.ContainerManager or None
        """
        self.sessions:          Dict[str, ExecutionSession] = {}
        self._router            = router
        self._container_manager = container_manager

    def create_session(
        self,
        session_id:     str,
        submission_id:  str,
        engine:         Any,
        sandbox_config: Dict,
    ) -> ExecutionSession:
        session = ExecutionSession(
            session_id=session_id,
            submission_id=submission_id,
            engine=engine,
            sandbox_config=sandbox_config,
            router=self._router,
            container_manager=self._container_manager,
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ExecutionSession]:
        return self.sessions.get(session_id)

    def start_all(self) -> None:
        for s in self.sessions.values():
            s.start()

    def stop_all(self) -> None:
        for s in self.sessions.values():
            s.stop()
