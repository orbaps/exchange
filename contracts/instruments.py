from __future__ import annotations

from dataclasses import dataclass

from contracts.domain import MatchingAlgorithm, SmpMode

# ---
# Instrument configurations driving exchange matching rules
# ---

@dataclass
class InstrumentDefinition:
    """Defines product parameters, matching engine settings, and validation bands."""
    symbol: str
    tick_size: int
    lot_size: int
    max_order_qty: int
    price_band_lower: int
    price_band_upper: int
    matching_algorithm: MatchingAlgorithm
    smp_mode: SmpMode
    prorata_threshold: int

    def __post_init__(self) -> None:
        """Validates the fields of the instrument definition."""
        if not self.symbol or not isinstance(self.symbol, str):
            raise TypeError("symbol must be a non-empty string")
        if self.tick_size <= 0 or not isinstance(self.tick_size, int):
            raise ValueError("tick_size must be a positive integer")
        if self.lot_size <= 0 or not isinstance(self.lot_size, int):
            raise ValueError("lot_size must be a positive integer")
        if self.max_order_qty <= 0 or not isinstance(self.max_order_qty, int):
            raise ValueError("max_order_qty must be a positive integer")
        if self.price_band_lower < 0 or not isinstance(self.price_band_lower, int):
            raise ValueError("price_band_lower must be a non-negative integer")
        if self.price_band_upper < self.price_band_lower or not isinstance(self.price_band_upper, int):
            raise ValueError("price_band_upper must be greater than or equal to price_band_lower")
        if not isinstance(self.matching_algorithm, MatchingAlgorithm):
            raise TypeError("matching_algorithm must be a valid MatchingAlgorithm")
        if not isinstance(self.smp_mode, SmpMode):
            raise TypeError("smp_mode must be a valid SmpMode")
        if self.prorata_threshold < 0 or not isinstance(self.prorata_threshold, int):
            raise ValueError("prorata_threshold must be a non-negative integer")

    def isTickAligned(self, price: int) -> bool:
        """Checks if price is aligned with the minimum tick increment."""
        if price <= 0 or not isinstance(price, int):
            return False
        return price % self.tick_size == 0

    def isLotAligned(self, qty: int) -> bool:
        """Checks if quantity is aligned with the minimum lot increment."""
        if qty <= 0 or not isinstance(qty, int):
            return False
        return qty % self.lot_size == 0

    def isWithinBands(self, price: int) -> bool:
        """Checks if price is within the circuit breaker boundaries."""
        if not isinstance(price, int):
            return False
        return self.price_band_lower <= price <= self.price_band_upper

