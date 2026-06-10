from typing import List
import statistics
from execution.events import ExecutionEvent
from execution.metrics import ExecutionStatistics

class ExecutionMetricsCalculator:
    """Computes exact statistics percentiles from a list of ExecutionEvents."""
    
    @staticmethod
    def calculate(events: List[ExecutionEvent]) -> ExecutionStatistics:
        if not events:
            return ExecutionStatistics()
            
        stats = ExecutionStatistics()
        stats.total_events = len(events)
        
        latencies = []
        min_start = float('inf')
        max_end = 0
        
        for e in events:
            if e.success:
                stats.successful_events += 1
                lat = (e.completion_timestamp_ns - e.dispatch_timestamp_ns) / 1e6
                if lat >= 0:
                    latencies.append(lat)
            else:
                stats.failed_events += 1
                if e.error:
                    err = e.error.lower()
                    if "timeout" in err:
                        stats.timeout_events += 1
                    elif "overflow" in err:
                        stats.queue_overflow_events += 1
                    else:
                        stats.crashed_events += 1
                        
            if e.dispatch_timestamp_ns > 0 and e.dispatch_timestamp_ns < min_start:
                min_start = e.dispatch_timestamp_ns
            if e.completion_timestamp_ns > 0 and e.completion_timestamp_ns > max_end:
                max_end = e.completion_timestamp_ns
                
        if latencies:
            latencies.sort()
            stats.average_execution_time_ms = statistics.mean(latencies)
            stats.p50_ms = latencies[int(len(latencies) * 0.50)]
            stats.p90_ms = latencies[int(len(latencies) * 0.90)]
            stats.p99_ms = latencies[int(len(latencies) * 0.99)]
            
        duration_s = (max_end - min_start) / 1e9
        if duration_s > 0:
            stats.events_per_second = stats.total_events / duration_s
            
        return stats
