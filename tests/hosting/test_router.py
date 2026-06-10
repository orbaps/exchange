import unittest
from hosting.router import EndpointRouter


class TestEndpointRouter(unittest.TestCase):

    def test_register_and_resolve(self):
        router = EndpointRouter()
        entry  = router.register("sub_001", "local://submission/sub_001/v1", "ctr_aaa")
        self.assertEqual(entry.endpoint, "local://submission/sub_001/v1")

        resolved = router.resolve("sub_001")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.container_id, "ctr_aaa")

    def test_resolve_unknown_returns_none(self):
        router = EndpointRouter()
        self.assertIsNone(router.resolve("ghost_sub"))

    def test_remove(self):
        router = EndpointRouter()
        router.register("sub_002", "local://submission/sub_002/v1", "ctr_bbb")
        ok = router.remove("sub_002")
        self.assertTrue(ok)
        self.assertIsNone(router.resolve("sub_002"))

    def test_unique_endpoints_per_submission(self):
        router = EndpointRouter()
        router.register("sub_A", "local://submission/sub_A/v1", "ctr_1")
        router.register("sub_B", "local://submission/sub_B/v1", "ctr_2")
        routes = router.list_routes()
        endpoints = [r.endpoint for r in routes]
        self.assertEqual(len(endpoints), len(set(endpoints)))  # all unique

    def test_overwrite_registration(self):
        """Re-registering the same submission_id updates the route."""
        router = EndpointRouter()
        router.register("sub_X", "local://submission/sub_X/v1", "ctr_old")
        router.register("sub_X", "local://submission/sub_X/v2", "ctr_new")
        r = router.resolve("sub_X")
        self.assertEqual(r.container_id, "ctr_new")
        self.assertEqual(r.endpoint, "local://submission/sub_X/v2")


if __name__ == "__main__":
    unittest.main()
