# 🫀 Comprehensive Heartbeat Monitoring System

## Overview

The RAG System includes a comprehensive heartbeat monitoring system that provides real-time health status, performance metrics, and alerting for all system components. This system is designed to ensure high availability and quick issue detection.

## 🏗️ Architecture

### Core Components

1. **HeartbeatMonitor** - Main monitoring engine
2. **ComponentHealth** - Individual component status tracking
3. **SystemHealth** - Overall system health aggregation
4. **API Endpoints** - RESTful health check interfaces
5. **CLI Tool** - Command-line health checking utility

### Monitored Components

| Component | Description | Health Checks |
|-----------|-------------|---------------|
| **API Server** | FastAPI application | HTTP endpoint availability, response time |
| **Storage Layer** | File system and directories | Directory existence, write permissions, disk usage |
| **Vector Store (FAISS)** | Vector database | Index status, vector count, search performance |
| **Embedding Service** | Cohere API integration | API connectivity, embedding generation, dimension validation |
| **LLM Service** | Groq API integration | API connectivity, response generation, token usage |
| **Dependency Container** | Service injection system | Service registration, creation tests |
| **Ingestion Engine** | Document processing | File ingestion tests, chunking, embedding |
| **Query Engine** | Search and retrieval | Query processing, context retrieval |
| **System Resources** | Hardware metrics | CPU, memory, disk usage |

## 🚀 Quick Start

### 1. Start the System with Monitoring

```bash
# Start the RAG system (includes heartbeat monitoring)
python main.py
```

The heartbeat monitor automatically:
- Initializes with the system
- Starts continuous monitoring (every 30 seconds)
- Provides API endpoints for health checks

### 2. Basic Health Check

```bash
# Using the CLI tool
python health_check_cli.py --mode basic

# Using curl
curl http://localhost:8000/health/summary
```

### 3. Comprehensive Health Check

```bash
# Detailed component analysis
python health_check_cli.py --mode comprehensive

# API endpoint
curl http://localhost:8000/heartbeat
```

## 📡 API Endpoints

### Core Health Endpoints

| Endpoint | Method | Description | Response Time |
|----------|--------|-------------|---------------|
| `/health` | GET | Basic health status | < 100ms |
| `/health/detailed` | GET | Component testing with timeouts | < 15s |
| `/health/summary` | GET | Quick health overview | < 500ms |

### Comprehensive Heartbeat Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/heartbeat` | GET | Full system health check | No |
| `/health/components` | GET | Individual component status | No |
| `/health/history` | GET | Health check history | No |
| `/health/performance` | GET | Performance metrics | No |
| `/health/check` | POST | Trigger manual health check | No |

### Example Responses

#### Basic Health Summary
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-06-07T08:45:43.406309",
  "uptime_hours": 2.5,
  "component_count": 9,
  "healthy_components": 8,
  "warning_components": 1,
  "critical_components": 0,
  "alerts": []
}
```

#### Comprehensive Heartbeat
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-06-07T08:45:43.406309",
  "uptime_seconds": 9000,
  "components": [
    {
      "name": "API Server",
      "status": "healthy",
      "response_time_ms": 45.2,
      "last_check": "2025-06-07T08:45:43.406309",
      "details": {
        "status_code": 200,
        "server_host": "localhost",
        "server_port": 8000
      },
      "error_message": null
    }
  ],
  "performance_metrics": {
    "system_cpu_percent": 15.2,
    "system_memory_percent": 45.8,
    "system_disk_percent": 67.3,
    "total_vectors": 1250,
    "uptime_hours": 2.5,
    "api_key_groq_configured": true,
    "api_key_cohere_configured": true
  },
  "alerts": []
}
```

## 🛠️ CLI Tool Usage

### Installation
```bash
pip install tabulate colorama psutil
```

### Basic Commands

```bash
# Basic health check
python health_check_cli.py --mode basic

# Comprehensive analysis
python health_check_cli.py --mode comprehensive

# Component details
python health_check_cli.py --mode components

# Performance metrics
python health_check_cli.py --mode performance

# Continuous monitoring
python health_check_cli.py --mode monitor --interval 30
```

### Advanced Options

```bash
# Custom server URL
python health_check_cli.py --url http://production-server:8000

# JSON output for automation
python health_check_cli.py --mode basic --json

# With API key authentication
python health_check_cli.py --api-key your-api-key
```

### Example CLI Output

```
🔍 RAG SYSTEM - COMPREHENSIVE HEALTH CHECK
============================================================
Overall Status: HEALTHY
Timestamp: 2025-06-07T08:45:43.406309
Uptime: 2h 30m

📋 COMPONENT HEALTH:
┌─────────────────────────┬─────────┬───────────────┬─────────┐
│ Component               │ Status  │ Response Time │ Error   │
├─────────────────────────┼─────────┼───────────────┼─────────┤
│ API Server              │ HEALTHY │ 45ms          │ None    │
│ Storage Layer           │ HEALTHY │ 1ms           │ None    │
│ Vector Store (FAISS)    │ HEALTHY │ 7ms           │ None    │
│ Embedding Service       │ HEALTHY │ 89ms          │ None    │
│ LLM Service (Groq)      │ HEALTHY │ 1076ms        │ None    │
│ Dependency Container    │ HEALTHY │ 0ms           │ None    │
│ Ingestion Engine        │ HEALTHY │ 129ms         │ None    │
│ Query Engine            │ WARNING │ 8ms           │ Method  │
│ System Resources        │ HEALTHY │ 15ms          │ None    │
└─────────────────────────┴─────────┴───────────────┴─────────┘

📊 PERFORMANCE METRICS:
CPU Usage       15.2%
Memory Usage    45.8%
Disk Usage      67.3%
Total Vectors   1250
Uptime Hours    2.5
Groq API Key    ✅
Cohere API Key  ✅
```

## 🔧 Configuration

### Thresholds

The system uses configurable thresholds for performance monitoring:

```python
thresholds = {
    'api_response_time_ms': 5000,      # 5 seconds
    'memory_usage_percent': 85,        # 85%
    'cpu_usage_percent': 80,           # 80%
    'disk_usage_percent': 90,          # 90%
    'vector_search_time_ms': 1000,     # 1 second
    'embedding_time_ms': 3000,         # 3 seconds
    'llm_response_time_ms': 10000,     # 10 seconds
    'query_response_time_ms': 5000     # 5 seconds
}
```

### Monitoring Interval

```python
# Default: 30 seconds
heartbeat_monitor.check_interval = 30

# Start continuous monitoring
heartbeat_monitor.start_monitoring()
```

## 📊 Health Status Levels

| Status | Description | Action Required |
|--------|-------------|-----------------|
| **HEALTHY** | All systems operational | None |
| **WARNING** | Minor issues detected | Monitor closely |
| **CRITICAL** | Major issues affecting functionality | Immediate attention |
| **UNKNOWN** | Unable to determine status | Investigate |

## 🚨 Alerting

### Alert Types

1. **Component Failures** - When individual components fail health checks
2. **Performance Thresholds** - When metrics exceed configured limits
3. **API Connectivity** - When external APIs are unreachable
4. **Resource Exhaustion** - When system resources are critically low

### Alert Examples

```json
{
  "alerts": [
    "Critical issues detected in: API Server",
    "Performance threshold exceeded: memory_usage_percent = 92 > 85",
    "High CPU usage: 95.2%",
    "LLM API connectivity issues detected"
  ]
}
```

## 📈 Performance Metrics

### System Metrics
- **CPU Usage** - Current processor utilization
- **Memory Usage** - RAM consumption percentage
- **Disk Usage** - Storage space utilization
- **Uptime** - System operational time

### RAG-Specific Metrics
- **Vector Count** - Total vectors in FAISS store
- **API Key Status** - External API configuration
- **Component Response Times** - Individual service performance
- **Query Performance** - Search and retrieval metrics

### Vector Store Metrics
- **Index Health** - FAISS index status
- **Search Performance** - Vector similarity search times
- **Storage Efficiency** - Index size and optimization

## 🔍 Troubleshooting

### Common Issues

#### API Server Critical
```bash
# Check if server is running
curl http://localhost:8000/health

# Restart the server
python main.py
```

#### High Resource Usage
```bash
# Check system resources
python health_check_cli.py --mode performance

# Monitor continuously
python health_check_cli.py --mode monitor
```

#### Component Warnings
```bash
# Get detailed component status
python health_check_cli.py --mode components

# Check specific component logs
tail -f data/logs/health_history.json
```

### Health Check Failures

1. **Connection Refused** - Server not running
2. **Timeout Errors** - Component overloaded
3. **API Key Issues** - External service authentication
4. **Resource Exhaustion** - System capacity limits

## 🔄 Integration

### Monitoring Tools

The heartbeat system integrates with:

- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards
- **PagerDuty** - Alert management
- **Slack** - Notification channels

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Health Check
  run: |
    python health_check_cli.py --mode basic --json > health.json
    if [ $? -ne 0 ]; then
      echo "Health check failed"
      exit 1
    fi
```

### Docker Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python health_check_cli.py --mode basic || exit 1
```

## 📝 Logging

### Health History

Health checks are automatically logged to:
- **File**: `data/logs/health_history.json`
- **Memory**: Last 100 health checks
- **API**: `/health/history` endpoint

### Log Format

```json
{
  "history": [
    {
      "overall_status": "healthy",
      "timestamp": "2025-06-07T08:45:43.406309",
      "uptime_seconds": 9000,
      "components": [...],
      "performance_metrics": {...},
      "alerts": []
    }
  ],
  "last_updated": "2025-06-07T08:45:43.406309"
}
```

## 🚀 Advanced Features

### Custom Health Checks

```python
# Add custom component check
async def check_custom_component(self) -> ComponentHealth:
    # Your custom health check logic
    return ComponentHealth(
        name="Custom Component",
        status=HealthStatus.HEALTHY,
        response_time_ms=response_time,
        last_check=datetime.now().isoformat(),
        details={"custom_metric": value}
    )
```

### Webhook Notifications

```python
# Configure webhook alerts
heartbeat_monitor.webhook_url = "https://your-webhook-endpoint.com"
heartbeat_monitor.enable_webhooks = True
```

### Performance Baselines

```python
# Set custom thresholds
heartbeat_monitor.thresholds.update({
    'custom_metric_threshold': 100,
    'api_response_time_ms': 2000
})
```

## 📚 Best Practices

### 1. Regular Monitoring
- Run health checks every 30 seconds in production
- Monitor trends over time
- Set up automated alerts

### 2. Threshold Tuning
- Adjust thresholds based on your environment
- Monitor false positive rates
- Update thresholds as system scales

### 3. Response Procedures
- Document response procedures for each alert type
- Test alert channels regularly
- Maintain escalation procedures

### 4. Capacity Planning
- Monitor resource trends
- Plan for growth
- Set up predictive alerts

## 🔗 Related Documentation

- [API Documentation](./API.md)
- [Configuration Guide](./CONFIG.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

## 📞 Support

For issues with the heartbeat monitoring system:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review health check logs in `data/logs/health_history.json`
3. Run diagnostic tests with `python test_heartbeat.py`
4. Contact the development team with health check output

**Remember**: The heartbeat system is designed to be your first line of defense for system health. Regular monitoring and prompt response to alerts will ensure optimal system performance! 🚀 