"""
Performance Monitor for Project AEGIS
Real-time performance monitoring, metrics collection, and optimization suggestions
"""

import os
import time
import psutil
import threading
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

import aioredis
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int
    requests_per_second: float
    avg_response_time: float
    error_rate: float
    cache_hit_rate: float
    database_connections: int
    queue_size: int

@dataclass
class AlertThresholds:
    """Alert thresholds for performance metrics"""
    cpu_percent: float = 80.0
    memory_percent: float = 85.0
    disk_usage_percent: float = 90.0
    response_time_p95: float = 1000.0  # ms
    error_rate: float = 5.0  # percentage
    cache_hit_rate: float = 70.0  # percentage
    queue_size: int = 1000

@dataclass
class PerformanceAlert:
    """Performance alert structure"""
    alert_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str  # info, warning, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class MetricsCollector:
    """Collects and manages application metrics"""

    def __init__(self):
        self.registry = CollectorRegistry()

        # Prometheus metrics
        self.request_count = Counter(
            'aegis_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.request_duration = Histogram(
            'aegis_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )

        self.active_connections = Gauge(
            'aegis_active_connections',
            'Number of active connections',
            registry=self.registry
        )

        self.cache_hits = Counter(
            'aegis_cache_hits_total',
            'Total cache hits',
            registry=self.registry
        )

        self.cache_misses = Counter(
            'aegis_cache_misses_total',
            'Total cache misses',
            registry=self.registry
        )

        self.database_connections = Gauge(
            'aegis_database_connections',
            'Number of database connections',
            registry=self.registry
        )

        self.error_count = Counter(
            'aegis_errors_total',
            'Total number of errors',
            ['error_type', 'endpoint'],
            registry=self.registry
        )

        self.system_cpu = Gauge(
            'aegis_system_cpu_percent',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_memory = Gauge(
            'aegis_system_memory_percent',
            'System memory usage percentage',
            registry=self.registry
        )

        self.process_memory = Gauge(
            'aegis_process_memory_bytes',
            'Process memory usage in bytes',
            registry=self.registry
        )

        # Internal metrics
        self._request_times = deque(maxlen=1000)
        self._error_counts = defaultdict(int)
        self._endpoint_counts = defaultdict(int)

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record request metrics"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()

        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        self._request_times.append(duration)
        self._endpoint_counts[f"{method} {endpoint}"] += 1

        if status_code >= 400:
            self._error_counts[f"{method} {endpoint}"] += 1

    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits.inc()

    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses.inc()

    def update_system_metrics(self):
        """Update system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.system_cpu.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        self.system_memory.set(memory.percent)

        # Process memory
        process = psutil.Process()
        self.process_memory.set(process.memory_info().rss)

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics string"""
        return generate_latest(self.registry).decode('utf-8')

    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        if not self._request_times:
            return {
                'count': 0,
                'avg_time': 0,
                'p50': 0,
                'p95': 0,
                'p99': 0
            }

        sorted_times = sorted(self._request_times)
        count = len(sorted_times)

        return {
            'count': count,
            'avg_time': sum(sorted_times) / count,
            'p50': sorted_times[int(count * 0.5)],
            'p95': sorted_times[int(count * 0.95)],
            'p99': sorted_times[int(count * 0.99)]
        }

class PerformanceMonitor:
    """
    Advanced performance monitoring system
    Provides real-time metrics, alerting, and optimization suggestions
    """

    def __init__(self, alert_thresholds: Optional[AlertThresholds] = None):
        self.alert_thresholds = alert_thresholds or AlertThresholds()
        self.metrics_collector = MetricsCollector()

        # Performance history
        self.metrics_history = deque(maxlen=1000)
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)

        # Background monitoring
        self._monitoring_active = False
        self._monitor_thread = None
        self._monitor_interval = 30  # seconds

        # Performance optimization
        self._optimization_suggestions = []
        self._last_optimization_check = datetime.utcnow()

        logger.info("Performance monitor initialized")

    def start_monitoring(self):
        """Start background performance monitoring"""
        if self._monitoring_active:
            logger.warning("Performance monitoring already active")
            return

        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop background performance monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)

        logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring_active:
            try:
                self._collect_metrics()
                self._check_alerts()
                self._generate_optimization_suggestions()

                time.sleep(self._monitor_interval)

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(5)  # Shorter sleep on error

    def _collect_metrics(self):
        """Collect current performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Process metrics
            process = psutil.Process()

            # Application metrics
            request_stats = self.metrics_collector.get_request_stats()

            # Calculate error rate
            total_requests = sum(self.metrics_collector._endpoint_counts.values())
            total_errors = sum(self.metrics_collector._error_counts.values())
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

            # Calculate cache hit rate
            cache_hits = self.metrics_collector.cache_hits._value.get()
            cache_misses = self.metrics_collector.cache_misses._value.get()
            cache_hit_rate = (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0

            metrics = PerformanceMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                disk_usage_percent=(disk.used / disk.total) * 100,
                active_connections=int(self.metrics_collector.active_connections._value.get()),
                requests_per_second=total_requests / 60 if total_requests > 0 else 0,  # Rough estimate
                avg_response_time=request_stats.get('avg_time', 0) * 1000,  # Convert to ms
                error_rate=error_rate,
                cache_hit_rate=cache_hit_rate,
                database_connections=int(self.metrics_collector.database_connections._value.get()),
                queue_size=0  # Would be populated by actual queue monitoring
            )

            self.metrics_history.append(metrics)
            self.metrics_collector.update_system_metrics()

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    def _check_alerts(self):
        """Check performance thresholds and generate alerts"""
        if not self.metrics_history:
            return

        current_metrics = self.metrics_history[-1]

        # CPU usage alert
        if current_metrics.cpu_percent > self.alert_thresholds.cpu_percent:
            self._create_alert(
                "cpu_usage",
                current_metrics.cpu_percent,
                self.alert_thresholds.cpu_percent,
                "warning" if current_metrics.cpu_percent < 95 else "critical",
                f"High CPU usage: {current_metrics.cpu_percent:.1f}%"
            )

        # Memory usage alert
        if current_metrics.memory_percent > self.alert_thresholds.memory_percent:
            self._create_alert(
                "memory_usage",
                current_metrics.memory_percent,
                self.alert_thresholds.memory_percent,
                "warning" if current_metrics.memory_percent < 95 else "critical",
                f"High memory usage: {current_metrics.memory_percent:.1f}%"
            )

        # Disk usage alert
        if current_metrics.disk_usage_percent > self.alert_thresholds.disk_usage_percent:
            self._create_alert(
                "disk_usage",
                current_metrics.disk_usage_percent,
                self.alert_thresholds.disk_usage_percent,
                "critical",
                f"High disk usage: {current_metrics.disk_usage_percent:.1f}%"
            )

        # Response time alert
        if current_metrics.avg_response_time > self.alert_thresholds.response_time_p95:
            self._create_alert(
                "response_time",
                current_metrics.avg_response_time,
                self.alert_thresholds.response_time_p95,
                "warning",
                f"High response time: {current_metrics.avg_response_time:.1f}ms"
            )

        # Error rate alert
        if current_metrics.error_rate > self.alert_thresholds.error_rate:
            self._create_alert(
                "error_rate",
                current_metrics.error_rate,
                self.alert_thresholds.error_rate,
                "critical",
                f"High error rate: {current_metrics.error_rate:.1f}%"
            )

        # Cache hit rate alert
        if current_metrics.cache_hit_rate < self.alert_thresholds.cache_hit_rate:
            self._create_alert(
                "cache_hit_rate",
                current_metrics.cache_hit_rate,
                self.alert_thresholds.cache_hit_rate,
                "warning",
                f"Low cache hit rate: {current_metrics.cache_hit_rate:.1f}%"
            )

        # Queue size alert
        if current_metrics.queue_size > self.alert_thresholds.queue_size:
            self._create_alert(
                "queue_size",
                current_metrics.queue_size,
                self.alert_thresholds.queue_size,
                "warning",
                f"High queue size: {current_metrics.queue_size}"
            )

    def _create_alert(self, metric_name: str, current_value: float, threshold: float,
                      severity: str, message: str):
        """Create or update performance alert"""
        alert_id = f"{metric_name}_{int(time.time())}"

        # Check if similar alert already exists
        existing_alert = None
        for aid, alert in self.active_alerts.items():
            if alert.metric_name == metric_name and not alert.resolved:
                existing_alert = alert
                break

        if existing_alert:
            # Update existing alert
            existing_alert.current_value = current_value
            existing_alert.timestamp = datetime.utcnow()
            existing_alert.message = message
        else:
            # Create new alert
            alert = PerformanceAlert(
                alert_id=alert_id,
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold,
                severity=severity,
                message=message,
                timestamp=datetime.utcnow()
            )

            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            logger.warning(f"Performance alert created: {message}")

    def _generate_optimization_suggestions(self):
        """Generate performance optimization suggestions"""
        if not self.metrics_history:
            return

        # Only generate suggestions every 5 minutes
        if (datetime.utcnow() - self._last_optimization_check) < timedelta(minutes=5):
            return

        self._last_optimization_check = datetime.utcnow()
        suggestions = []

        current_metrics = self.metrics_history[-1]

        # CPU optimization suggestions
        if current_metrics.cpu_percent > 70:
            suggestions.append({
                'category': 'cpu',
                'priority': 'high',
                'suggestion': 'Consider scaling horizontally or optimizing CPU-intensive operations',
                'details': f'Current CPU usage is {current_metrics.cpu_percent:.1f}%'
            })

        # Memory optimization suggestions
        if current_metrics.memory_percent > 75:
            suggestions.append({
                'category': 'memory',
                'priority': 'high',
                'suggestion': 'Review memory usage patterns and consider memory optimization',
                'details': f'Current memory usage is {current_metrics.memory_percent:.1f}%'
            })

        # Cache optimization suggestions
        if current_metrics.cache_hit_rate < 80:
            suggestions.append({
                'category': 'cache',
                'priority': 'medium',
                'suggestion': 'Review caching strategy and consider increasing cache TTL or size',
                'details': f'Current cache hit rate is {current_metrics.cache_hit_rate:.1f}%'
            })

        # Response time optimization suggestions
        if current_metrics.avg_response_time > 500:
            suggestions.append({
                'category': 'response_time',
                'priority': 'high',
                'suggestion': 'Profile slow endpoints and optimize database queries or external API calls',
                'details': f'Current average response time is {current_metrics.avg_response_time:.1f}ms'
            })

        # Error rate optimization suggestions
        if current_metrics.error_rate > 2:
            suggestions.append({
                'category': 'error_rate',
                'priority': 'critical',
                'suggestion': 'Investigate and fix error sources, implement better error handling',
                'details': f'Current error rate is {current_metrics.error_rate:.1f}%'
            })

        self._optimization_suggestions = suggestions

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self, minutes: int = 60) -> List[PerformanceMetrics]:
        """Get metrics history for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get active performance alerts"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]

    def get_alert_history(self, hours: int = 24) -> List[PerformanceAlert]:
        """Get alert history for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve a performance alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.active_alerts[alert_id].resolved_at = datetime.utcnow()
            logger.info(f"Performance alert resolved: {alert_id}")
            return True
        return False

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get performance optimization suggestions"""
        return self._optimization_suggestions

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        current_metrics = self.get_current_metrics()
        active_alerts = self.get_active_alerts()

        if not current_metrics:
            return {
                'status': 'no_data',
                'message': 'No performance data available'
            }

        # Determine overall status
        critical_alerts = [a for a in active_alerts if a.severity == 'critical']
        warning_alerts = [a for a in active_alerts if a.severity == 'warning']

        if critical_alerts:
            status = 'critical'
        elif warning_alerts:
            status = 'warning'
        else:
            status = 'healthy'

        return {
            'status': status,
            'current_metrics': asdict(current_metrics),
            'active_alerts_count': len(active_alerts),
            'critical_alerts_count': len(critical_alerts),
            'warning_alerts_count': len(warning_alerts),
            'optimization_suggestions_count': len(self._optimization_suggestions),
            'last_updated': current_metrics.timestamp.isoformat(),
            'uptime': self._get_uptime()
        }

    def _get_uptime(self) -> str:
        """Get application uptime"""
        if not self.metrics_history:
            return "unknown"

        start_time = self.metrics_history[0].timestamp
        uptime = datetime.utcnow() - start_time

        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        current_metrics = self.get_current_metrics()
        alerts = self.get_active_alerts()
        suggestions = self.get_optimization_suggestions()

        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': asdict(current_metrics) if current_metrics else None,
            'alerts': [asdict(alert) for alert in alerts],
            'suggestions': suggestions,
            'summary': self.get_performance_summary()
        }

        if format == 'json':
            import json
            return json.dumps(data, indent=2, default=str)
        elif format == 'prometheus':
            return self.metrics_collector.get_prometheus_metrics()
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Middleware for FastAPI
class PerformanceMiddleware:
    """FastAPI middleware for performance monitoring"""

    def __init__(self, app, monitor: PerformanceMonitor = None):
        self.app = app
        self.monitor = monitor or performance_monitor

    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        # Create request object for logging
        request = Request(scope, receive)

        # Update active connections
        self.monitor.metrics_collector.active_connections.inc()

        try:
            # Process request
            await self.app(scope, receive, send)

            # Calculate response time
            response_time = time.time() - start_time

            # Record metrics (simplified - in real implementation, you'd get status code from response)
            self.monitor.metrics_collector.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=200,  # Would be actual status code
                duration=response_time
            )

        except Exception as e:
            # Record error
            response_time = time.time() - start_time
            self.monitor.metrics_collector.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=response_time
            )
            self.monitor.metrics_collector.error_count.labels(
                error_type=type(e).__name__,
                endpoint=request.url.path
            ).inc()

        finally:
            # Update active connections
            self.monitor.metrics_collector.active_connections.dec()

# Decorator for function performance monitoring
def monitor_performance(func_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        name = func_name or f"{func.__module__}.{func.__name__}"

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    logger.debug(f"Function {name} executed in {duration:.3f}s")
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    logger.debug(f"Function {name} executed in {duration:.3f}s")
            return sync_wrapper

    return decorator

# Utility functions
def start_performance_monitoring():
    """Start performance monitoring"""
    performance_monitor.start_monitoring()

def stop_performance_monitoring():
    """Stop performance monitoring"""
    performance_monitor.stop_monitoring()

def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics"""
    return performance_monitor.get_performance_summary()

def get_prometheus_metrics() -> str:
    """Get Prometheus metrics"""
    return performance_monitor.metrics_collector.get_prometheus_metrics()

# Export components
__all__ = [
    'PerformanceMonitor',
    'MetricsCollector',
    'PerformanceMetrics',
    'AlertThresholds',
    'PerformanceAlert',
    'PerformanceMiddleware',
    'monitor_performance',
    'performance_monitor',
    'start_performance_monitoring',
    'stop_performance_monitoring',
    'get_performance_metrics',
    'get_prometheus_metrics'
]