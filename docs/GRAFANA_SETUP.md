# Grafana Dashboard Setup
## Task 3.5: Create monitoring visualizations

### Prerequisites
1. Grafana instance running (default: http://localhost:3000)
2. Prometheus instance scraping backend metrics
3. Backend exposing /api/v1/monitoring/metrics endpoint

### Setup Steps

#### 1. Add Data Source (Prometheus)
1. Go to: Grafana > Configuration > Data Sources
2. Click "Add data source"
3. Select "Prometheus"
4. URL: `http://prometheus:9090` (or your Prometheus instance)
5. Click "Save & test"

#### 2. Create Dashboard
1. Go to: Dashboards > New > New dashboard
2. Click "Add new panel"
3. Create the following panels:

### Dashboard Panels

#### Panel 1: Agent Latency (p50, p95, p99)
```
Type: Graph / Time series
Metric: histogram_quantile(0.5, agent_latency_seconds) (for p50)
        histogram_quantile(0.95, agent_latency_seconds) (for p95)
        histogram_quantile(0.99, agent_latency_seconds) (for p99)
Group by: agent
Title: Agent Response Time Percentiles
Axes: 
  - Y-axis: Latency (seconds)
  - X-axis: Time
```

#### Panel 2: Error Rate by Agent
```
Type: Graph / Time series
Metric: rate(agent_errors_total[5m])
Group by: agent, error_type
Title: Error Rate by Agent
Axes:
  - Y-axis: Errors per second
  - X-axis: Time
Legend: {{agent}} - {{error_type}}
```

#### Panel 3: Cache Hit Rate
```
Type: Gauge
Metric: cache_hit_rate
Title: Current Cache Hit Rate
Unit: Percent (0-100)
Thresholds:
  - 0-50: Red
  - 50-80: Yellow
  - 80-100: Green
```

#### Panel 4: WebSocket Connections
```
Type: Stat / Number
Metric: websocket_connections_active
Title: Active WebSocket Connections
Unit: short
Decimals: 0
Sparkline: On
```

#### Panel 5: Request Duration Distribution
```
Type: Heatmap / Time series
Metric: increase(request_duration_seconds_bucket[5m])
Group by: le (bucket)
Title: Request Duration Heatmap
Axes:
  - Y-axis: Bucket (seconds)
  - X-axis: Time
```

#### Panel 6: API Success Rate
```
Type: Gauge
Metric: 1 - (rate(request_duration_seconds_count{status_code=~"5.."}[5m]) / rate(request_duration_seconds_count[5m]))
Title: API Success Rate
Unit: Percent (0-100)
Thresholds:
  - 0-95: Red
  - 95-99: Yellow
  - 99-100: Green
```

### PromQL Queries Reference

**Agent latency percentiles:**
```promql
histogram_quantile(0.5, rate(agent_latency_seconds_bucket[5m]))
histogram_quantile(0.95, rate(agent_latency_seconds_bucket[5m]))
histogram_quantile(0.99, rate(agent_latency_seconds_bucket[5m]))
```

**Error count over time:**
```promql
rate(agent_errors_total[5m]) by (agent, error_type)
```

**Cache effectiveness:**
```promql
cache_hit_rate
```

**Active connections:**
```promql
websocket_connections_active
```

**Request latency by endpoint:**
```promql
histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) by (endpoint)
```

**API error rate:**
```promql
rate(request_duration_seconds_count{status_code=~"5.."}[5m])
```

### Alerts Configuration

Create Prometheus alert rules for critical issues:

**Alert: High Error Rate**
```yaml
- alert: AgentHighErrorRate
  expr: rate(agent_errors_total[5m]) > 0.1
  for: 5m
  annotations:
    summary: "High error rate on {{ $labels.agent }}"
    description: "Error rate is {{ $value }} errors/sec"
```

**Alert: High Latency**
```yaml
- alert: AgentHighLatency
  expr: histogram_quantile(0.95, rate(agent_latency_seconds_bucket[5m])) > 2
  for: 10m
  annotations:
    summary: "High latency on {{ $labels.agent }}"
    description: "P95 latency is {{ $value }}s"
```

**Alert: Cache Hit Rate Low**
```yaml
- alert: LowCacheHitRate
  expr: cache_hit_rate < 0.5
  for: 15m
  annotations:
    summary: "Cache hit rate is low"
    description: "Cache hit rate is {{ $value | humanizePercentage }}"
```

### Dashboard JSON Export
After creating your dashboard, export and save as:
`openspec/changes/phase6-enhancement/reports/grafana-dashboard.json`

### Integration with Sentry
Link Sentry errors to Grafana metrics:
1. In Sentry, go to Integrations > Grafana
2. Configure Grafana instance URL
3. Enable "Create or link issues"
4. Now errors will show related Grafana panels

### Production Deployment

**Environment Setup:**
```bash
# In Railway or your container:
GRAFANA_ADMIN_PASSWORD=your-secure-password
PROMETHEUS_URL=http://prometheus:9090
SENTRY_DSN=https://key@sentry.io/project
```

**Verification:**
```bash
# Check metrics endpoint
curl http://backend:8080/api/v1/monitoring/metrics

# Verify Prometheus scrape
curl http://prometheus:9090/api/v1/targets

# Test Grafana datasource
curl http://grafana:3000/api/datasources
```

### Troubleshooting

**No data showing:**
1. Verify Prometheus is scraping the backend
2. Check backend metrics endpoint is accessible
3. Verify PromQL query syntax

**Metrics not updating:**
1. Check backend logs for errors
2. Verify Prometheus scrape interval (default: 15s)
3. Check network connectivity between Prometheus and backend

**High latency shown:**
1. Check agent implementation performance
2. Review database query performance
3. Check API response sizes

### Further Reading
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Queries](https://grafana.com/docs/grafana/latest/dashboards/manage-dashboards/)
- [Histograms and Quantiles](https://prometheus.io/docs/practices/histograms/)
