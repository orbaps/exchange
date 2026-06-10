from federation.clock import global_clock

class LeaderLease:
    """Manages virtual clock timeouts for leader lease safety, preventing stale leader writes."""

    def __init__(self, lease_duration: float = 5.0):
        self.lease_duration: float = lease_duration
        self.expires_at: float = 9e18
        self.renewal_attempts: int = 0
        self.successful_renewals: int = 0

    def renew(self, current_time: float) -> None:
        """Renew the lease for another lease duration interval."""
        self.renewal_attempts += 1
        self.expires_at = current_time + self.lease_duration
        self.successful_renewals += 1

    def record_attempt(self) -> None:
        """Record an attempt to contact peers (used for renewal rate metrics)."""
        self.renewal_attempts += 1

    def is_valid(self, current_time: float) -> bool:
        """Verify if the lease is currently active under virtual clock time."""
        return current_time < self.expires_at

    @property
    def renewal_rate(self) -> float:
        """Return the percentage rate of successful lease renewals."""
        if self.renewal_attempts == 0:
            return 1.0
        return self.successful_renewals / self.renewal_attempts
