from dataclasses import dataclass, field
from typing import List
import statistics


@dataclass
class HostingStatistics:
    """Operational metrics snapshot for the hosting layer."""
    active_containers:       int   = 0
    failed_containers:       int   = 0
    total_deployments:       int   = 0
    successful_deployments:  int   = 0
    total_builds:            int   = 0
    successful_builds:       int   = 0

    # Raw timing samples collected during operation
    startup_times_ms:  List[float] = field(default_factory=list)
    restart_counts:    List[int]   = field(default_factory=list)

    @property
    def average_startup_time(self) -> float:
        if not self.startup_times_ms:
            return 0.0
        return statistics.mean(self.startup_times_ms)

    @property
    def deployment_success_rate(self) -> float:
        if self.total_deployments == 0:
            return 0.0
        return self.successful_deployments / self.total_deployments

    @property
    def build_success_rate(self) -> float:
        if self.total_builds == 0:
            return 0.0
        return self.successful_builds / self.total_builds

    @property
    def average_restart_count(self) -> float:
        if not self.restart_counts:
            return 0.0
        return statistics.mean(self.restart_counts)

    def record_deployment(self, success: bool, startup_ms: float = 0.0) -> None:
        self.total_deployments += 1
        if success:
            self.successful_deployments += 1
        if startup_ms > 0:
            self.startup_times_ms.append(startup_ms)

    def record_build(self, success: bool) -> None:
        self.total_builds += 1
        if success:
            self.successful_builds += 1

    def record_restart(self, count: int) -> None:
        self.restart_counts.append(count)

    def summary(self) -> str:
        return (
            f"HostingStatistics:\n"
            f"  active_containers:       {self.active_containers}\n"
            f"  failed_containers:       {self.failed_containers}\n"
            f"  deployment_success_rate: {self.deployment_success_rate:.1%}\n"
            f"  build_success_rate:      {self.build_success_rate:.1%}\n"
            f"  average_startup_time:    {self.average_startup_time:.1f} ms\n"
            f"  average_restart_count:   {self.average_restart_count:.2f}\n"
        )
