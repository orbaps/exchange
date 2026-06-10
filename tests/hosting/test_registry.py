import unittest
from hosting.runtime import RuntimeType
from hosting.resources import MEDIUM
from hosting.manifest import SubmissionManifest
from hosting.registry import SubmissionRegistry


def _manifest(team: str, version: int, sid: str) -> SubmissionManifest:
    return SubmissionManifest(
        submission_id=sid,
        team_name=team,
        version=version,
        language=RuntimeType.PYTHON,
        entrypoint="main.py",
        build_command="echo ok",
        run_command="python main.py",
        resource_profile=MEDIUM,
    )


class TestSubmissionRegistry(unittest.TestCase):

    def test_register_and_get(self):
        reg = SubmissionRegistry()
        m   = _manifest("TeamA", 1, "sub_A1")
        reg.register(m)
        self.assertIs(reg.get("sub_A1"), m)

    def test_multi_version(self):
        reg = SubmissionRegistry()
        for v in (1, 2, 3):
            reg.register(_manifest("TeamA", v, f"sub_A{v}"))

        versions = reg.get_versions("TeamA")
        self.assertEqual([m.version for m in versions], [1, 2, 3])

        latest = reg.latest("TeamA")
        self.assertEqual(latest.version, 3)
        self.assertEqual(latest.submission_id, "sub_A3")

    def test_latest_returns_none_for_unknown_team(self):
        reg = SubmissionRegistry()
        self.assertIsNone(reg.latest("Ghost"))

    def test_remove(self):
        reg = SubmissionRegistry()
        reg.register(_manifest("TeamB", 1, "sub_B1"))
        reg.register(_manifest("TeamB", 2, "sub_B2"))

        ok = reg.remove("sub_B1")
        self.assertTrue(ok)
        self.assertIsNone(reg.get("sub_B1"))

        # v2 still present
        self.assertIsNotNone(reg.get("sub_B2"))

    def test_update(self):
        reg = SubmissionRegistry()
        reg.register(_manifest("TeamC", 1, "sub_C1"))
        updated = reg.update("sub_C1", notes="patched")
        self.assertEqual(updated.notes, "patched")
        self.assertEqual(reg.get("sub_C1").notes, "patched")

    def test_list_all(self):
        reg = SubmissionRegistry()
        for v in (1, 2):
            reg.register(_manifest("TeamD", v, f"sub_D{v}"))
        self.assertEqual(len(reg.list_all()), 2)


if __name__ == "__main__":
    unittest.main()
