import os
import shutil
import unittest
from hosting.manifest import SubmissionManifest
from hosting.runtime import RuntimeType
from hosting.resources import SMALL
from hosting.artifacts import ArtifactStore

from tournament.submission_lock import SubmissionLock
from tournament.version_freeze import VersionFreeze

class TestVersionFreeze(unittest.TestCase):
    def tearDown(self):
        if os.path.exists("test_freeze_artifacts"):
            shutil.rmtree("test_freeze_artifacts")

    def test_submission_freeze(self):
        lock = SubmissionLock()
        store = ArtifactStore("test_freeze_artifacts")
        freezer = VersionFreeze(lock, store)
        
        # Initial manifest for v7
        manifest = SubmissionManifest(
            submission_id="sub1",
            team_name="Team A",
            version=7,
            language=RuntimeType.PYTHON,
            entrypoint="main.py",
            build_command="build",
            run_command="run",
            resource_profile=SMALL
        )
        
        # Freeze at tournament start
        freezer.freeze("tourney1", [manifest])
        
        # Team updates to v8 in the broader system (simulated by mutating original object)
        manifest.version = 8
        
        # Retrieve frozen manifest for the tournament
        frozen_manifests = freezer.get_frozen_manifests("tourney1", ["sub1"])
        frozen = frozen_manifests[0]
        
        # Verify it's still v7
        self.assertEqual(frozen.version, 7)
        self.assertEqual(manifest.version, 8) # Just to prove mutation happened

if __name__ == "__main__":
    unittest.main()
