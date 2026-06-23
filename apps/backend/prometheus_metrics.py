"""
Prometheus Metrics Configuration
Task 3.4: Expose metrics endpoint for Grafana monitoring

Metrics exposed:
1. agent_latency_seconds — Time from invoke to response (histogram)
2. agent_errors_total — Count of errors by agent (counter)
3. websocket_connections_active — Current active WebSocket connections (gauge)
4. cache_hit_rate — Percentage of cache hits (gauge 0.0-1.0)
5. request_duration_seconds — HTTP request latency (histogram)
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
)
import time
from functools import wraps
from typing import Optional

# Create registry for metrics
registry = CollectorRegistry()

# === Metrics ===

# 1. Agent Latency (histogram with buckets: 0.1s, 0.5s, 1s, 2s, 5s)
agent_latency_seconds = Histogram(
    'agent_latency_seconds',
    'Time from agent invoke to response',
    ['agent'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
    registry=registry,
)

# 2. Agent Errors (counter)
agent_errors_total = Counter(
    'agent_errors_total',
    'Total count of agent errors',
    ['agent', 'error_type'],  # error_type: timeout, 500, validation, network
    registry=registry,
)

# 3. WebSocket Connections (gauge)
websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections',
    registry=registry,
)

# 4. Cache Hit Rate (gauge)
cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0.0 - 1.0)',
    registry=registry,
)

# 5. Request Duration (histogram)
request_duration_seconds = Histogram(
    'request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'status_code'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=registry,
)


# === Helper Functions ===

def track_agent_latency(agent_name: str):
    """Decorator to track agent latency"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                agent_latency_seconds.labels(agent=agent_name).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start
                agent_latency_seconds.labels(agent=agent_name).observe(duration)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                agent_latency_seconds.labels(agent=agent_name).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start
                agent_latency_seconds.labels(agent=agent_name).observe(duration)
                raise

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def record_agent_error(agent_name: str, error_type: str):
    """Record an agent error"""
    agent_errors_total.labels(agent=agent_name, error_type=error_type).inc()


def track_websocket_connection(increment: bool = True):
    """Track WebSocket connection count"""
    if increment:
        websocket_connections_active.inc()
    else:
        websocket_connections_active.dec()


def update_cache_hit_rate(hits: int, total: int):
    """Update cache hit rate (0.0 - 1.0)"""
    if total > 0:
        rate = hits / total
        cache_hit_rate.set(rate)


def track_request_duration(method: str, endpoint: str, status_code: int):
    """Decorator to track request duration"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                ).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start
                request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=500,
                ).observe(duration)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                ).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start
                request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=500,
                ).observe(duration)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def get_metrics() -> bytes:
    """Return Prometheus metrics in text format"""
    return generate_latest(registry)


# === Integration with FastAPI ===

def add_prometheus_middleware(app):
    """Add Prometheus middleware to FastAPI app"""
    import asyncio
    from fastapi import Request
    from time import time

    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        start_time = time()
        response = await call_next(request)
        process_time = time() - start_time

        # Track request duration
        request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).observe(process_time)

        return response


import asyncio
