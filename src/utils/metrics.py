"""
Performance Monitoring and Metrics Collection

Provides utilities for tracking system performance and collecting metrics.
"""

import time
import functools
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Performance statistics."""
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_time: float = 0.0

    def update(self, duration: float) -> None:
        """Update statistics with new duration."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.count
        self.last_time = duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "total_time": self.total_time,
            "min_time": self.min_time if self.min_time != float('inf') else 0.0,
            "max_time": self.max_time,
            "avg_time": self.avg_time,
            "last_time": self.last_time
        }


class MetricsCollector:
    """Collects and manages system metrics."""

    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.

        Args:
            max_history: Maximum number of historical data points to keep
        """
        self.max_history = max_history
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.performance: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self.logger = logging.getLogger(__name__)

    def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None) -> None:
        """
        Increment a counter.

        Args:
            name: Counter name
            value: Increment value
            tags: Optional tags
        """
        key = self._make_key(name, tags)
        self.counters[key] += value

    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """
        Set a gauge value.

        Args:
            name: Gauge name
            value: Gauge value
            tags: Optional tags
        """
        key = self._make_key(name, tags)
        self.gauges[key] = value

    def record_value(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """
        Record a value in histogram.

        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags
        """
        key = self._make_key(name, tags)
        self.histograms[key].append(MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {}
        ))

    def record_performance(self, name: str, duration: float) -> None:
        """
        Record performance timing.

        Args:
            name: Performance metric name
            duration: Duration in seconds
        """
        self.performance[name].update(duration)

    def get_counter(self, name: str, tags: Dict[str, str] = None) -> int:
        """Get counter value."""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0)

    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> Optional[float]:
        """Get gauge value."""
        key = self._make_key(name, tags)
        return self.gauges.get(key)

    def get_histogram_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """
        Get histogram statistics.

        Args:
            name: Metric name
            tags: Optional tags

        Returns:
            Dictionary with min, max, avg, count
        """
        key = self._make_key(name, tags)
        values = [p.value for p in self.histograms.get(key, [])]

        if not values:
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "count": 0}

        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values)
        }

    def get_performance_stats(self, name: str) -> Dict[str, Any]:
        """Get performance statistics."""
        return self.performance[name].to_dict()

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics.

        Returns:
            Dictionary with all metrics
        """
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self.histograms.keys()
            },
            "performance": {
                name: stats.to_dict()
                for name, stats in self.performance.items()
            },
            "timestamp": datetime.now().isoformat()
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.performance.clear()

    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create metric key from name and tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


def measure_time(metric_name: str = None, collector: MetricsCollector = None):
    """
    Decorator to measure function execution time.

    Args:
        metric_name: Name for the metric (defaults to function name)
        collector: Metrics collector instance

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        name = metric_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if collector:
                    collector.record_performance(name, duration)
                else:
                    global_metrics.record_performance(name, duration)

                # Log slow operations
                if duration > 1.0:  # > 1 second
                    logger = logging.getLogger(func.__module__)
                    logger.warning(f"Slow operation: {name} took {duration:.2f}s")

        return wrapper
    return decorator


class PerformanceMonitor:
    """Context manager for monitoring performance."""

    def __init__(self, name: str, collector: MetricsCollector = None):
        """
        Initialize performance monitor.

        Args:
            name: Metric name
            collector: Metrics collector instance
        """
        self.name = name
        self.collector = collector or global_metrics
        self.start_time = None
        self.duration = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record."""
        self.duration = time.time() - self.start_time
        self.collector.record_performance(self.name, self.duration)
        return False


class RateLimiter:
    """Simple rate limiter for metrics."""

    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: deque = deque(maxlen=max_calls)

    def is_allowed(self) -> bool:
        """
        Check if a call is allowed.

        Returns:
            True if call is allowed, False otherwise
        """
        now = time.time()

        # Remove old calls outside time window
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()

        # Check if we're under the limit
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True

        return False

    def wait_time(self) -> float:
        """
        Get time to wait before next call is allowed.

        Returns:
            Seconds to wait
        """
        if len(self.calls) < self.max_calls:
            return 0.0

        oldest_call = self.calls[0]
        wait_until = oldest_call + self.time_window
        return max(0.0, wait_until - time.time())


class MetricsReporter:
    """Reports metrics periodically."""

    def __init__(self, collector: MetricsCollector, interval: int = 60):
        """
        Initialize metrics reporter.

        Args:
            collector: Metrics collector
            interval: Reporting interval in seconds
        """
        self.collector = collector
        self.interval = interval
        self.logger = logging.getLogger(__name__)
        self.last_report = datetime.now()

    def should_report(self) -> bool:
        """Check if it's time to report."""
        return (datetime.now() - self.last_report).total_seconds() >= self.interval

    def report(self) -> None:
        """Generate and log metrics report."""
        if not self.should_report():
            return

        metrics = self.collector.get_all_metrics()

        # Log summary
        self.logger.info("=== Metrics Report ===")
        self.logger.info(f"Counters: {len(metrics['counters'])}")
        self.logger.info(f"Gauges: {len(metrics['gauges'])}")
        self.logger.info(f"Histograms: {len(metrics['histograms'])}")
        self.logger.info(f"Performance: {len(metrics['performance'])}")

        # Log top performance stats
        if metrics['performance']:
            self.logger.info("Top Performance Metrics:")
            sorted_perf = sorted(
                metrics['performance'].items(),
                key=lambda x: x[1]['total_time'],
                reverse=True
            )
            for name, stats in sorted_perf[:5]:
                self.logger.info(
                    f"  {name}: {stats['count']} calls, "
                    f"avg={stats['avg_time']:.3f}s, "
                    f"max={stats['max_time']:.3f}s"
                )

        self.last_report = datetime.now()


# Global metrics collector
global_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return global_metrics
