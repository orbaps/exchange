import unittest
import os
import hashlib
import json
from botfleet.profiles import TrafficProfiles
from botfleet.orchestrator import BotOrchestrator
from botfleet.replay import ReplayExporter

class TestReplay(unittest.TestCase):
    
    def test_replay_determinism(self):
        """campaign -> save -> load -> same hash"""
        config = TrafficProfiles.get_conservative_profile(seed=777)
        # Reduce scale for fast test
        config.num_bots = 10
        config.events_per_second = 100
        config.duration_seconds = 1.0
        
        orch = BotOrchestrator(config, num_workers=2)
        events, _ = orch.generate_fleet_events()
        
        filepath = "test_events.jsonl"
        ReplayExporter.save_events(events, filepath)
        
        loaded_events = ReplayExporter.load_events(filepath)
        
        # Verify deterministic exact match using canonical JSON
        str1 = json.dumps([vars(e) for e in events], default=str, sort_keys=True)
        str2 = json.dumps([vars(e) for e in loaded_events], default=str, sort_keys=True)
        hash1 = hashlib.sha256(str1.encode()).hexdigest()
        hash2 = hashlib.sha256(str2.encode()).hexdigest()
        
        self.assertEqual(hash1, hash2)
        
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    unittest.main()
