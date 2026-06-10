from botfleet.config import FleetConfig
from botfleet.orderflow import MarketRegime

class TrafficProfiles:
    """Pre-defined standard fleet configurations for load testing."""
    
    @staticmethod
    def get_conservative_profile(seed: int) -> FleetConfig:
        return FleetConfig(
            num_bots=100,
            duration_seconds=10.0,
            events_per_second=1000.0,
            seed=seed,
            regime=MarketRegime.CALM
        )
        
    @staticmethod
    def get_normal_profile(seed: int) -> FleetConfig:
        return FleetConfig(
            num_bots=1000,
            duration_seconds=30.0,
            events_per_second=10000.0,
            seed=seed,
            regime=MarketRegime.TRENDING_UP
        )
        
    @staticmethod
    def get_stress_profile(seed: int) -> FleetConfig:
        return FleetConfig(
            num_bots=5000,
            duration_seconds=60.0,
            events_per_second=50000.0,
            seed=seed,
            regime=MarketRegime.VOLATILE
        )
        
    @staticmethod
    def get_extreme_profile(seed: int) -> FleetConfig:
        return FleetConfig(
            num_bots=10000,
            duration_seconds=60.0,
            events_per_second=100000.0,
            seed=seed,
            regime=MarketRegime.FLASH_CRASH
        )
