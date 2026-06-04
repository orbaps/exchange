from __future__ import annotations

# ---
# SeededPrng is a helper class providing deterministic pseudo-random number generation
# ---


class SeededPrng:
    """Deterministic Seeded Pseudo-Random Number Generator.

    Ensures cross-platform identical sequences given the same seed.
    """

    def __init__(self) -> None:
        """Initialize the seeded PRNG state."""
        raise NotImplementedError

    def init(self, seed: int) -> None:
        """Initialize the generator with a specific 64-bit seed.

        Args:
            seed: A 64-bit integer seed value.
        """
        raise NotImplementedError

    def nextUint64(self) -> int:
        """Generate the next random 64-bit unsigned integer.

        Returns:
            A random 64-bit integer.
        """
        raise NotImplementedError

    def nextFloat(self) -> float:
        """Generate the next random float in range [0.0, 1.0).

        Returns:
            A float value.
        """
        raise NotImplementedError

    def nextGaussian(self) -> float:
        """Generate the next random float following a standard normal distribution.

        Returns:
            A Gaussian-distributed float.
        """
        raise NotImplementedError
