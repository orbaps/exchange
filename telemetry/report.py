from dataclasses import dataclass
from typing import Optional

from telemetry.latency import LatencyStatistics
from telemetry.tps import TPSStatistics
from telemetry.failures import FailureStatistics
from telemetry.execution import ExecutionStatistics

@dataclass
class TelemetryReport:
    """Composite report containing all telemetry metrics for a benchmark execution."""
    
    framework_latency: LatencyStatistics
    framework_tps: TPSStatistics
    
    sandbox_execution: Optional[ExecutionStatistics] = None
    
    # We may not have failures or correctness directly in a single benchmark run if it didn't fail.
    # But we can store them here if we want a unified report.
    failures: Optional[FailureStatistics] = None
    correctness_score: Optional[float] = None
    from telemetry.load import LoadGenerationStatistics
    load_generation: Optional[LoadGenerationStatistics] = None
    
    from execution.metrics import ExecutionStatistics
    execution_stats: Optional[ExecutionStatistics] = None
    
    def to_markdown(self) -> str:
        lines = []
        lines.append("### Telemetry Report")
        
        lines.append("\n**Framework Telemetry (Stream A)**")
        lines.append(f"- **p50 Latency:** {self.framework_latency.p50_ms:.3f} ms")
        lines.append(f"- **p90 Latency:** {self.framework_latency.p90_ms:.3f} ms")
        lines.append(f"- **p99 Latency:** {self.framework_latency.p99_ms:.3f} ms")
        lines.append(f"- **Average Latency:** {self.framework_latency.avg_ms:.3f} ms")
        lines.append(f"- **Framework TPS:** {self.framework_tps.tps:.2f} events/sec")
        
        if self.sandbox_execution:
            lines.append("\n**Sandbox Execution (Stream B)**")
            lines.append(f"- **Execution Time:** {self.sandbox_execution.runtime_ms:.3f} ms")
            lines.append(f"- **Execution TPS:** {self.sandbox_execution.eps:.2f} events/sec")
            lines.append(f"- **Sandbox Overhead:** {self.sandbox_execution.sandbox_overhead_ms:.3f} ms")
            
        if self.failures:
            lines.append("\n**Failure Statistics**")
            lines.append(f"- **Success Rate:** {self.failures.success_rate:.2f}%")
            lines.append(f"- **Failure Rate:** {self.failures.failure_rate:.2f}%")
            lines.append(f"- **Timeouts:** {self.failures.timeout_count}")
            lines.append(f"- **Crashes:** {self.failures.crash_count}")
            
        if self.correctness_score is not None:
            lines.append("\n**Correctness**")
            lines.append(f"- **Score:** {self.correctness_score:.2f}%")
            
        if self.load_generation:
            lines.append("\n**Load Generation Statistics**")
            lines.append(f"- **Total Events:** {self.load_generation.generated_events}")
            lines.append(f"- **Generation Rate:** {self.load_generation.events_per_second:.2f} eps")
            lines.append(f"- **Active Bots:** {self.load_generation.bot_count}")
            lines.append(f"- **Workers:** {self.load_generation.worker_count}")
            lines.append(f"- **Runtime:** {self.load_generation.generation_runtime_ms:.3f} ms")
            
            lines.append("**Event Mix**")
            for k, v in self.load_generation.event_mix.items():
                lines.append(f"- {k}: {v:.2f}%")
                
        if self.execution_stats:
            lines.append("\n**Distributed Execution Statistics**")
            lines.append(f"- **Total Dispatched:** {self.execution_stats.total_events}")
            lines.append(f"- **Successful:** {self.execution_stats.successful_events}")
            lines.append(f"- **Failed:** {self.execution_stats.failed_events}")
            lines.append(f"- **Timeouts:** {self.execution_stats.timeout_events}")
            lines.append(f"- **Crashes:** {self.execution_stats.crashed_events}")
            lines.append(f"- **Overflows:** {self.execution_stats.queue_overflow_events}")
            lines.append(f"- **Throughput:** {self.execution_stats.events_per_second:.2f} eps")
            lines.append(f"- **p50 Latency:** {self.execution_stats.p50_ms:.3f} ms")
            lines.append(f"- **p99 Latency:** {self.execution_stats.p99_ms:.3f} ms")
            
        return "\n".join(lines)
