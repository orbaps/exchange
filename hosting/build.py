import subprocess
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from hosting.artifacts import ArtifactStore
from hosting.manifest import SubmissionManifest


class BuildStatus(Enum):
    PENDING  = "PENDING"
    BUILDING = "BUILDING"
    SUCCESS  = "SUCCESS"
    FAILED   = "FAILED"


@dataclass
class BuildResult:
    build_id:      str
    submission_id: str
    status:        BuildStatus
    duration_ms:   float
    logs:          List[str] = field(default_factory=list)
    artifact_path: str = ""
    error:         Optional[str] = None


class BuildExecutor:
    """Runs the actual build process and captures stdout/stderr.

    Separated from BuildManager so tracking/logging concerns are decoupled
    from subprocess execution. Replace the subprocess body with compiler
    invocations per RuntimeType in future phases.
    """

    def __init__(self, store: ArtifactStore):
        self.store = store

    def execute(self, manifest: SubmissionManifest) -> BuildResult:
        build_id  = f"build_{uuid.uuid4().hex[:8]}"
        logs: List[str] = []
        t0 = time.time()

        try:
            # For Phase 4.4: simulate a successful build via subprocess echo.
            # Real compilers per RuntimeType are plugged in Phase 5+.
            cmd = manifest.build_command or f"echo build:{manifest.language.value}"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=manifest.source_path or ".",
                timeout=manifest.resource_profile.execution_timeout_sec,
            )
            logs.extend(result.stdout.splitlines())
            if result.stderr:
                logs.extend(result.stderr.splitlines())

            if result.returncode != 0:
                raise RuntimeError(f"Build exited with code {result.returncode}")

            # Persist build log under versioned path: root/{sid}/v{version}/build.log
            log_text = "\n".join(logs)
            artifact = self.store.write_text(
                manifest.submission_id, manifest.version, f"{build_id}.log", log_text, "log"
            )
            duration_ms = (time.time() - t0) * 1000

            return BuildResult(
                build_id=build_id,
                submission_id=manifest.submission_id,
                status=BuildStatus.SUCCESS,
                duration_ms=duration_ms,
                logs=logs,
                artifact_path=artifact.path,
            )

        except Exception as exc:
            duration_ms = (time.time() - t0) * 1000
            logs.append(str(exc))
            return BuildResult(
                build_id=build_id,
                submission_id=manifest.submission_id,
                status=BuildStatus.FAILED,
                duration_ms=duration_ms,
                logs=logs,
                error=str(exc),
            )


class BuildManager:
    """Tracks build state and coordinates with BuildExecutor.

    BuildManager owns:  status tracking, history, logging
    BuildExecutor owns: running commands, capturing output
    """

    def __init__(self, store: ArtifactStore):
        self._store    = store
        self._executor = BuildExecutor(store)
        self._history: dict[str, BuildResult] = {}   # build_id → result

    def build(self, manifest: SubmissionManifest) -> BuildResult:
        result = self._executor.execute(manifest)
        self._history[result.build_id] = result
        return result

    def get_result(self, build_id: str) -> Optional[BuildResult]:
        return self._history.get(build_id)

    def all_results(self) -> List[BuildResult]:
        return list(self._history.values())
