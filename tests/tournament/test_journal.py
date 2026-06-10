import os
import shutil
import unittest

from tournament.journal import TournamentJournal
from tournament.replay import TournamentReplay

class TestJournalDeterminism(unittest.TestCase):
    def setUp(self):
        self.journal_path = "test_journal_artifacts/journal.jsonl"
        os.makedirs(os.path.dirname(self.journal_path), exist_ok=True)
        if os.path.exists(self.journal_path):
            os.remove(self.journal_path)

    def tearDown(self):
        if os.path.exists("test_journal_artifacts"):
            shutil.rmtree("test_journal_artifacts")

    def test_replay_determinism(self):
        journal = TournamentJournal(self.journal_path)
        
        # Write some events
        journal.record_tournament_start("t1", ["team1", "team2"])
        journal.record_stage_start("t1", "stage1", ["team1", "team2"])
        journal.record_advancement("t1", "stage1", ["team1"])
        journal.record_elimination("t1", "stage1", ["team2"])
        journal.record_stage_end("t1", "stage1", ["team1", "team2"])
        journal.record_winner_declaration("t1", "team1")

        # Load timeline
        timeline = TournamentReplay.load_timeline(journal)
        
        self.assertEqual(timeline.tournament_id, "t1")
        self.assertEqual(len(timeline.events), 6)
        
        # Verify event sequence
        self.assertEqual(timeline.events[0].event_type, "TOURNAMENT_START")
        self.assertEqual(timeline.events[1].event_type, "STAGE_START")
        self.assertEqual(timeline.events[2].event_type, "ADVANCEMENT")
        self.assertEqual(timeline.events[3].event_type, "ELIMINATION")
        self.assertEqual(timeline.events[4].event_type, "STAGE_END")
        self.assertEqual(timeline.events[5].event_type, "WINNER_DECLARATION")
        
        # Corrupt the journal and ensure it fails hash verification
        with open(self.journal_path, "r") as f:
            lines = f.readlines()
            
        import json
        corrupted = json.loads(lines[0])
        corrupted["entry"]["payload"]["locked_contestants"] = ["hacked_team"]
        lines[0] = json.dumps(corrupted) + "\n"
        
        with open(self.journal_path, "w") as f:
            f.writelines(lines)
            
        with self.assertRaises(ValueError) as context:
            TournamentReplay.load_timeline(TournamentJournal(self.journal_path))
            
        self.assertIn("Journal corruption detected", str(context.exception))

if __name__ == "__main__":
    unittest.main()
