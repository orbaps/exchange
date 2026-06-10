import os
import unittest
import hashlib
import json
from hosting.journal import HostingJournal
from hosting.replay import HostingReplay


class TestHostingJournal(unittest.TestCase):

    JOURNAL_PATH = "test_hosting_journal.jsonl"

    def setUp(self):
        if os.path.exists(self.JOURNAL_PATH):
            os.remove(self.JOURNAL_PATH)

    def tearDown(self):
        if os.path.exists(self.JOURNAL_PATH):
            os.remove(self.JOURNAL_PATH)

    def test_append_and_load(self):
        journal = HostingJournal(self.JOURNAL_PATH)
        journal.append("BUILD_STARTED",  {"submission_id": "sub1", "build_id": "b1"})
        journal.append("BUILD_SUCCESS",   {"submission_id": "sub1", "build_id": "b1"})
        journal.append("DEPLOY_STARTED", {"submission_id": "sub1", "container_id": "ctr1"})

        events = HostingReplay.load(self.JOURNAL_PATH)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["event_type"], "BUILD_STARTED")
        self.assertEqual(events[1]["event_type"], "BUILD_SUCCESS")
        self.assertEqual(events[2]["event_type"], "DEPLOY_STARTED")

    def test_sha256_deterministic(self):
        """Same payload must always produce the same hash."""
        journal = HostingJournal(self.JOURNAL_PATH)
        data    = {"submission_id": "sub1", "build_id": "b42"}
        h1      = journal.append("BUILD_STARTED", data)

        # Recompute manually
        record   = {"event_type": "BUILD_STARTED", **data}
        expected = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        self.assertEqual(h1, expected)

    def test_filter_by_type(self):
        journal = HostingJournal(self.JOURNAL_PATH)
        journal.append("BUILD_STARTED",  {"submission_id": "sub1"})
        journal.append("DEPLOY_STARTED", {"submission_id": "sub1"})
        journal.append("BUILD_SUCCESS",  {"submission_id": "sub2"})

        events = HostingReplay.load(self.JOURNAL_PATH)
        builds = HostingReplay.filter_by_type(events, "BUILD_STARTED")
        self.assertEqual(len(builds), 1)

    def test_filter_by_submission(self):
        journal = HostingJournal(self.JOURNAL_PATH)
        journal.append("BUILD_STARTED", {"submission_id": "sub1"})
        journal.append("BUILD_STARTED", {"submission_id": "sub2"})
        journal.append("BUILD_SUCCESS", {"submission_id": "sub1"})

        events = HostingReplay.load(self.JOURNAL_PATH)
        sub1   = HostingReplay.filter_by_submission(events, "sub1")
        self.assertEqual(len(sub1), 2)

    def test_replay_on_empty_file(self):
        events = HostingReplay.load("nonexistent_file.jsonl")
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
