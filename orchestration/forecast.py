from typing import List, Dict, Tuple, Optional
from orchestration.models import CapacityForecast, NodeOrchestrationMetrics

class CapacityForecaster:
    """Predicts future CPU/memory utilization and node failure risk using deterministic linear trend extrapolation."""
    
    def fit_linear(self, data: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        Fit a line y = mx + c to the data points.
        Returns: (m, c)
        """
        n = len(data)
        if n < 2:
            return 0.0, data[0][1] if n == 1 else 0.0

        sum_x = sum(d[0] for d in data)
        sum_y = sum(d[1] for d in data)
        sum_xx = sum(d[0] * d[0] for d in data)
        sum_xy = sum(d[0] * d[1] for d in data)

        denom = n * sum_xx - sum_x * sum_x
        if abs(denom) < 1e-9:
            return 0.0, sum_y / n

        m = (n * sum_xy - sum_x * sum_y) / denom
        c = (sum_y - m * sum_x) / n
        return m, c

    def forecast_capacity(self, node_id: str, history: List[NodeOrchestrationMetrics], now: float) -> CapacityForecast:
        """
        Fits linear models on historical metrics and extrapolates value at T+60 and T+300.
        Calculates bottleneck times and predicted failure risk.
        """
        if not history:
            return CapacityForecast(
                node_id=node_id,
                timestamp=now,
                predicted_cpu=0.0,
                predicted_memory=0.0,
                predicted_failure_risk=0.0
            )

        latest = history[-1]
        
        # CPU points
        cpu_pts = [(m.timestamp, m.cpu_usage) for m in history]
        cpu_m, cpu_c = self.fit_linear(cpu_pts)

        # Memory points
        mem_pts = [(m.timestamp, m.memory_usage) for m in history]
        mem_m, mem_c = self.fit_linear(mem_pts)

        # Forecast T+60 and T+300
        cpu_60 = max(0.0, min(100.0, cpu_m * (now + 60.0) + cpu_c))
        cpu_300 = max(0.0, min(100.0, cpu_m * (now + 300.0) + cpu_c))

        mem_60 = max(0.0, min(100.0, mem_m * (now + 60.0) + mem_c))
        mem_300 = max(0.0, min(100.0, mem_m * (now + 300.0) + mem_c))

        # Find bottleneck (crossing 100%)
        bottleneck_time = None
        times = []
        if cpu_m > 0.001:
            t_cpu = (100.0 - cpu_c) / cpu_m
            if t_cpu > now:
                times.append(t_cpu)
        if mem_m > 0.001:
            t_mem = (100.0 - mem_c) / mem_m
            if t_mem > now:
                times.append(t_mem)

        if times:
            bottleneck_time = min(times)

        # Failure Risk Calculation
        failure_risk = 0.0
        if latest.cpu_usage > 90.0 or latest.memory_usage > 90.0:
            failure_risk = 1.0
        elif bottleneck_time is not None:
            time_to_fail = bottleneck_time - now
            if time_to_fail <= 60.0:
                failure_risk = 0.9
            elif time_to_fail <= 300.0:
                # scale linearly from 0.9 to 0.2
                failure_risk = 0.2 + (0.7 * (300.0 - time_to_fail) / 240.0)
            else:
                failure_risk = 0.1
        else:
            # Check if current pressure is elevated
            avg_pressure = (latest.cpu_usage + latest.memory_usage) / 2.0
            failure_risk = max(0.0, min(1.0, (avg_pressure - 50.0) / 50.0 * 0.2))

        return CapacityForecast(
            node_id=node_id,
            timestamp=now,
            predicted_cpu=cpu_300,
            predicted_memory=mem_300,
            predicted_failure_risk=round(failure_risk, 3),
            bottleneck_time=bottleneck_time
        )
