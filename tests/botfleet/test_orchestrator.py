import unittest
import hashlib
import json
from botfleet.config import FleetConfig
from botfleet.orderflow import MarketRegime
from botfleet.orchestrator import BotOrchestrator

class TestOrchestrator(unittest.TestCase):
    
    def test_determinism_100k(self):
        """Generates 100k events twice and ensures identical hashes."""
        config = FleetConfig(
            num_bots=100,
            duration_seconds=10.0,
            events_per_second=10000.0, # 100k total expected
            seed=12345,
            regime=MarketRegime.TRENDING_UP
        )
        
        orch1 = BotOrchestrator(config, num_workers=4)
        events1, _ = orch1.generate_fleet_events()
        
        orch2 = BotOrchestrator(config, num_workers=4)
        events2, _ = orch2.generate_fleet_events()
        
        self.assertEqual(len(events1), len(events2))
        
        # Verify deterministic exact match using canonical JSON
        str1 = json.dumps([vars(e) for e in events1], default=str, sort_keys=True)
        str2 = json.dumps([vars(e) for e in events2], default=str, sort_keys=True)
        hash1 = hashlib.sha256(str1.encode()).hexdigest()
        hash2 = hashlib.sha256(str2.encode()).hexdigest()
        
        self.assertEqual(hash1, hash2)

if __name__ == '__main__':
    unittest.main()
