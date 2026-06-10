import json
import os
import shutil
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Artifact:
    artifact_id:   str
    submission_id: str
    version:       int
    artifact_type: str        # "build_output" | "log" | "manifest"
    path:          str
    size_bytes:    int = 0


class ArtifactStore:
    """Centralised store for build outputs, logs, and metadata.

    Directory layout (version-safe):
        root/
        └── {submission_id}/
             └── v{version}/
                  ├── build.log
                  └── manifest.json

    This prevents TeamA v1 from overwriting TeamA v3 artifacts.
    """

    def __init__(self, root: str = "artifacts"):
        self.root = root
        os.makedirs(root, exist_ok=True)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _dir(self, submission_id: str, version: int) -> str:
        d = os.path.join(self.root, submission_id, f"v{version}")
        os.makedirs(d, exist_ok=True)
        return d

    def _path(self, submission_id: str, version: int, filename: str) -> str:
        return os.path.join(self._dir(submission_id, version), filename)

    def _artifact_id(self, submission_id: str, version: int, filename: str) -> str:
        return f"{submission_id}/v{version}/{filename}"

    # ── Write ─────────────────────────────────────────────────────────────────

    def write_text(self, submission_id: str, version: int, filename: str,
                   content: str, artifact_type: str = "log") -> Artifact:
        path = self._path(submission_id, version, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        size = os.path.getsize(path)
        return Artifact(self._artifact_id(submission_id, version, filename),
                        submission_id, version, artifact_type, path, size)

    def write_json(self, submission_id: str, version: int, filename: str,
                   data: dict, artifact_type: str = "manifest") -> Artifact:
        return self.write_text(
            submission_id, version, filename,
            json.dumps(data, indent=2, sort_keys=True),
            artifact_type,
        )

    def copy_file(self, submission_id: str, version: int, src_path: str,
                  artifact_type: str = "build_output") -> Artifact:
        filename = os.path.basename(src_path)
        dest = self._path(submission_id, version, filename)
        shutil.copy2(src_path, dest)
        size = os.path.getsize(dest)
        return Artifact(self._artifact_id(submission_id, version, filename),
                        submission_id, version, artifact_type, dest, size)

    # ── Read ──────────────────────────────────────────────────────────────────

    def read_text(self, submission_id: str, version: int, filename: str) -> Optional[str]:
        path = self._path(submission_id, version, filename)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            return f.read()

    def list_versions(self, submission_id: str) -> List[int]:
        """Returns sorted list of stored version numbers for a submission."""
        sub_dir = os.path.join(self.root, submission_id)
        if not os.path.isdir(sub_dir):
            return []
        versions = []
        for name in os.listdir(sub_dir):
            if name.startswith("v") and name[1:].isdigit():
                versions.append(int(name[1:]))
        return sorted(versions)

    def list_artifacts(self, submission_id: str, version: int) -> List[Artifact]:
        d = self._dir(submission_id, version)
        results = []
        for fn in os.listdir(d):
            p = os.path.join(d, fn)
            results.append(Artifact(self._artifact_id(submission_id, version, fn),
                                    submission_id, version, "unknown", p, os.path.getsize(p)))
        return results

    # ── Remove ────────────────────────────────────────────────────────────────

    def purge_version(self, submission_id: str, version: int) -> bool:
        d = os.path.join(self.root, submission_id, f"v{version}")
        if os.path.isdir(d):
            shutil.rmtree(d)
            return True
        return False

    def purge(self, submission_id: str) -> bool:
        d = os.path.join(self.root, submission_id)
        if os.path.isdir(d):
            shutil.rmtree(d)
            return True
        return False
