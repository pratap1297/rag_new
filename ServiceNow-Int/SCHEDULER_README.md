# ServiceNow Scheduler Integration

This module provides a comprehensive ServiceNow incident scheduler that automatically fetches incident details on a regular basis and integrates them with the Router Rescue AI backend system.

## Features

### 🔄 **Automated Scheduling**
- Configurable fetch intervals (default: 15 minutes)
- Background processing with thread-safe operations
- Automatic retry mechanisms with exponential backoff
- Graceful error handling and recovery

### 📊 **Advanced Filtering**
- Priority-based filtering (Critical, High, Moderate, Low, Planning)
- State-based filtering (New, In Progress, On Hold, Resolved, Closed)
- Date range filtering (configurable days back)
- Category and assignment group filtering
- Network-related incident detection

### 💾 **Intelligent Caching**
- SQLite-based local caching
- Change detection to avoid duplicate processing
- Configurable cache TTL
- Fetch history tracking and analytics

### 🔗 **Backend Integration**
- Automatic document upload to Router Rescue AI backend
- Network incident prioritization
- Metadata enrichment for enhanced search
- Real-time processing with callback system

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ServiceNow    │    │    Scheduler     │    │  Router Rescue  │
│    Instance     │◄──►│   Integration    │◄──►│   AI Backend    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ SQLite Cache │
                       │   Database   │
                       └──────────────┘
```

## Components

### 1. ServiceNow Scheduler (`servicenow_scheduler.py`)

**Core Features:**
- **IncidentData Class**: Structured data representation with 25+ fields
- **Configurable Filtering**: Advanced query building with multiple filter types
- **Caching System**: SQLite-based caching with change detection
- **Callback System**: Extensible processing pipeline
- **Statistics Tracking**: Comprehensive fetch analytics

**Key Methods:**
```python
# Start the scheduler
scheduler.start_scheduler()

# Add custom processing callbacks
scheduler.add_incident_callback(your_callback_function)

# Fetch incidents manually
incidents = scheduler.fetch_incidents()

# Get statistics
stats = scheduler.get_fetch_statistics()
```

### 2. Backend Integration (`backend_integration.py`)

**Integration Features:**
- **Network Detection**: Intelligent filtering for network-related incidents
- **Document Formatting**: Structured document creation for backend processing
- **Async Processing**: Non-blocking incident processing
- **Error Handling**: Robust error management with logging

**Key Methods:**
```python
# Start integration
integration.start_integration(config)

# Process incidents manually
await integration.process_incidents_batch(incidents)

# Check if incident is network-related
is_network = integration.is_network_related(incident)
```

## Configuration

### Environment Variables

Copy `env_scheduler_template.txt` to `.env` and configure:

```bash
# ServiceNow Connection
SERVICENOW_INSTANCE=your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

# Scheduler Settings
SERVICENOW_FETCH_INTERVAL=15          # Minutes between fetches
SERVICENOW_BATCH_SIZE=100             # Incidents per API call
SERVICENOW_MAX_INCIDENTS=1000         # Max incidents per fetch
SERVICENOW_DAYS_BACK=7                # Days to look back

# Filtering
SERVICENOW_PRIORITY_FILTER=1,2,3      # Priority levels to fetch
SERVICENOW_STATE_FILTER=1,2,3         # States to fetch
SERVICENOW_CATEGORIES=Network,Infrastructure  # Categories to include

# Backend Integration
BACKEND_URL=http://localhost:8000      # Router Rescue AI backend URL
```

### Priority Levels
- `1` = Critical
- `2` = High
- `3` = Moderate
- `4` = Low
- `5` = Planning

### State Values
- `1` = New
- `2` = In Progress
- `3` = On Hold
- `6` = Resolved
- `7` = Closed
- `8` = Canceled

## Installation

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure Environment:**
```bash
cp env_scheduler_template.txt .env
# Edit .env with your ServiceNow credentials
```

3. **Test Connection:**
```bash
python test_connection.py
```

## Usage

### Basic Usage

```python
from servicenow_scheduler import ServiceNowScheduler
from backend_integration import BackendIntegration

# Create and start integration
integration = BackendIntegration()
integration.start_integration()

# Keep running
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    integration.stop_integration()
```

### Advanced Usage with Custom Callbacks

```python
from servicenow_scheduler import ServiceNowScheduler, IncidentData
from typing import List

def custom_incident_processor(incidents: List[IncidentData]):
    """Custom callback for processing incidents"""
    for incident in incidents:
        if incident.priority == '1':  # Critical incidents
            print(f"CRITICAL: {incident.number} - {incident.short_description}")
            # Send alert, create ticket, etc.

# Create scheduler with custom config
config = {
    'fetch_interval_minutes': 10,
    'priority_filter': ['1', '2'],  # Only critical and high
    'categories_filter': ['Network', 'Infrastructure']
}

scheduler = ServiceNowScheduler(config)
scheduler.add_incident_callback(custom_incident_processor)
scheduler.start_scheduler()
```

### Manual Incident Fetching

```python
from servicenow_scheduler import ServiceNowScheduler

scheduler = ServiceNowScheduler()

# Fetch incidents manually
incidents = scheduler.fetch_incidents()

# Process specific incident
incident = scheduler.get_incident_by_number('INC0012345')
if incident:
    print(f"Found incident: {incident.short_description}")

# Get cached incidents
cached = scheduler.get_cached_incidents(limit=50)
print(f"Found {len(cached)} cached incidents")
```

## Monitoring and Analytics

### Fetch Statistics

```python
stats = scheduler.get_fetch_statistics()
print(f"""
Total Cached Incidents: {stats['total_cached_incidents']}
Last Fetch: {stats['last_fetch_time']}
Total Fetches: {stats['total_fetches']}
Average Incidents per Fetch: {stats['average_incidents_per_fetch']}
Error Rate: {stats['error_rate']}%
""")
```

### Database Schema

The scheduler creates two main tables:

**incidents table:**
- `sys_id` (PRIMARY KEY)
- `number` (UNIQUE)
- `data` (JSON)
- `hash` (for change detection)
- `fetched_at`
- `updated_at`

**fetch_history table:**
- `id` (AUTO INCREMENT)
- `fetch_time`
- `incidents_count`
- `new_incidents`
- `updated_incidents`
- `errors`

## Network Incident Detection

The system automatically identifies network-related incidents using keyword matching:

**Network Keywords:**
- Infrastructure: `network`, `router`, `switch`, `firewall`, `vpn`
- Protocols: `bgp`, `ospf`, `vlan`, `tcp`, `ip`, `dns`, `dhcp`
- Connectivity: `ethernet`, `wifi`, `wireless`, `lan`, `wan`
- Performance: `bandwidth`, `latency`, `packet`, `ping`, `traceroute`
- Vendors: `cisco`, `juniper`, `arista`, `fortinet`

## Error Handling

### Connection Errors
- Automatic retry with exponential backoff
- Connection health checks before fetching
- Graceful degradation on ServiceNow unavailability

### Processing Errors
- Individual incident error isolation
- Comprehensive error logging
- Fetch history tracking with error details

### Backend Integration Errors
- Timeout handling for backend requests
- Retry mechanisms for failed uploads
- Fallback processing for backend unavailability

## Performance Optimization

### Batch Processing
- Configurable batch sizes for API efficiency
- Concurrent processing of multiple incidents
- Memory-efficient handling of large datasets

### Caching Strategy
- Local SQLite caching for offline capability
- Change detection to minimize redundant processing
- Configurable cache TTL for data freshness

### Resource Management
- Thread pool for concurrent operations
- Proper cleanup on shutdown
- Memory usage monitoring

## Troubleshooting

### Common Issues

1. **Connection Failures:**
```bash
# Test ServiceNow connection
python test_connection.py
```

2. **Authentication Errors:**
- Verify credentials in `.env`
- Check ServiceNow user permissions
- Ensure API access is enabled

3. **No Incidents Found:**
- Check filter configurations
- Verify date range settings
- Review ServiceNow data availability

4. **Backend Integration Issues:**
- Verify backend URL and availability
- Check network connectivity
- Review backend logs for errors

### Logging

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python servicenow_scheduler.py
```

Log files:
- `servicenow_scheduler.log` - Scheduler operations
- `backend_integration.log` - Backend integration events

## Security Considerations

### Credentials Management
- Store credentials in `.env` file (not in code)
- Use environment variables in production
- Consider using ServiceNow OAuth for enhanced security

### Data Protection
- Local cache encryption (future enhancement)
- Secure transmission to backend
- Audit logging for compliance

### Access Control
- Principle of least privilege for ServiceNow user
- Network segmentation for backend communication
- Regular credential rotation

## Future Enhancements

### Planned Features
1. **Real-time Webhooks**: ServiceNow webhook integration for instant updates
2. **Advanced Analytics**: Machine learning for incident pattern detection
3. **Multi-tenant Support**: Support for multiple ServiceNow instances
4. **Enhanced Security**: OAuth authentication and encryption
5. **Performance Monitoring**: Detailed performance metrics and alerting

### Integration Opportunities
1. **Slack/Teams Integration**: Real-time notifications for critical incidents
2. **ITSM Tools**: Integration with other ITSM platforms
3. **Monitoring Systems**: Integration with Prometheus/Grafana
4. **Automation Platforms**: Integration with Ansible/Terraform

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Verify configuration settings
4. Test individual components separately

## License

This module is part of the Router Rescue AI project and follows the same licensing terms. 