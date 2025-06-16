# ServiceNow Integration for RAG System

## Overview

The ServiceNow integration allows your RAG system to automatically fetch, process, and ingest ServiceNow incidents as searchable documents. This enables users to query historical incidents, troubleshooting information, and network-related issues directly through the RAG system.

## Architecture

```
ServiceNow API → Connector → Scheduler → Processor → RAG Ingestion Engine → FAISS Vector Store
                                ↓
                            Cache Database (SQLite)
```

## Features

- **Automated Ticket Fetching**: Scheduled retrieval of ServiceNow incidents
- **Smart Filtering**: Priority, state, category, and network-related filtering
- **Change Detection**: Only processes updated or new incidents
- **Caching**: SQLite-based caching to avoid duplicate processing
- **Network Classification**: Automatically identifies network-related incidents
- **Technical Detail Extraction**: Extracts IP addresses, hostnames, error codes
- **RESTful API**: Complete API for managing the integration
- **Real-time Monitoring**: Status tracking and performance metrics

## Installation & Setup

### 1. Environment Configuration

Create or update your `.env` file with ServiceNow credentials:

```bash
# ServiceNow Configuration
SERVICENOW_INSTANCE=your_instance_name
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

# Optional: Integration Settings
SERVICENOW_FETCH_INTERVAL=15
SERVICENOW_BATCH_SIZE=100
SERVICENOW_MAX_INCIDENTS=1000
SERVICENOW_PRIORITY_FILTER=1,2,3
SERVICENOW_STATE_FILTER=1,2,3
SERVICENOW_DAYS_BACK=7
```

### 2. System Configuration

Update `rag-system/data/config/system_config.json`:

```json
{
  "servicenow": {
    "enabled": true,
    "fetch_interval_minutes": 15,
    "batch_size": 100,
    "max_incidents_per_fetch": 1000,
    "priority_filter": ["1", "2", "3"],
    "state_filter": ["1", "2", "3"],
    "days_back": 7,
    "network_only": false,
    "auto_ingest": true,
    "cache_enabled": true,
    "cache_ttl_hours": 1
  }
}
```

### 3. Start the RAG System

The ServiceNow integration will be automatically initialized when you start the RAG system:

```bash
cd rag-system
python main.py
```

## API Endpoints

### Status & Management

- `GET /api/servicenow/status` - Get integration status
- `POST /api/servicenow/initialize` - Initialize integration
- `POST /api/servicenow/start` - Start automated sync
- `POST /api/servicenow/stop` - Stop automated sync

### Synchronization

- `POST /api/servicenow/sync` - Manual sync with filters
- `POST /api/servicenow/sync/incident/{number}` - Sync specific incident

### Configuration

- `GET /api/servicenow/config` - Get current configuration
- `PUT /api/servicenow/config` - Update configuration

### Monitoring

- `GET /api/servicenow/tickets/recent` - Get recent tickets
- `GET /api/servicenow/history` - Get sync history
- `POST /api/servicenow/test` - Test integration

## Usage Examples

### 1. Initialize and Start Integration

```python
import requests

# Initialize
response = requests.post("http://localhost:8000/api/servicenow/initialize")
print(response.json())

# Start automated sync
response = requests.post("http://localhost:8000/api/servicenow/start")
print(response.json())
```

### 2. Manual Sync with Filters

```python
import requests

filters = {
    "priority_filter": ["1", "2"],  # Critical and High only
    "network_only": True,           # Network-related incidents only
    "days_back": 3,                 # Last 3 days
    "limit": 50                     # Max 50 incidents
}

response = requests.post(
    "http://localhost:8000/api/servicenow/sync",
    json=filters
)
print(response.json())
```

### 3. Query ServiceNow Data

Once incidents are ingested, you can query them through the regular RAG API:

```python
import requests

query = {
    "query": "network outage router configuration",
    "max_results": 5
}

response = requests.post("http://localhost:8000/query", json=query)
print(response.json())
```

### 4. Get Integration Status

```python
import requests

response = requests.get("http://localhost:8000/api/servicenow/status")
status = response.json()

print(f"Initialized: {status['initialized']}")
print(f"Connection Healthy: {status['connection_healthy']}")
print(f"Scheduler Running: {status['scheduler_running']}")
print(f"Total Fetched: {status['statistics']['total_fetched']}")
```

## Configuration Options

### Priority Filters
- `1` - Critical
- `2` - High  
- `3` - Moderate
- `4` - Low
- `5` - Planning

### State Filters
- `1` - New
- `2` - In Progress
- `3` - On Hold
- `6` - Resolved
- `7` - Closed
- `8` - Canceled

### Network Classification

The system automatically identifies network-related incidents using keywords:
- Network equipment: router, switch, firewall, vpn
- Protocols: bgp, ospf, tcp, dhcp, dns
- Connectivity: ethernet, wifi, lan, wan
- Vendors: cisco, juniper, arista, fortinet

## Monitoring & Troubleshooting

### Check Integration Health

```bash
curl http://localhost:8000/api/servicenow/test
```

### View Recent Activity

```bash
curl http://localhost:8000/api/servicenow/history?limit=10
```

### Monitor Sync Performance

```bash
curl http://localhost:8000/api/servicenow/status
```

### Common Issues

1. **Connection Failed**
   - Verify ServiceNow credentials in `.env`
   - Check network connectivity to ServiceNow instance
   - Ensure ServiceNow instance URL is correct

2. **No Incidents Fetched**
   - Check priority and state filters
   - Verify date range (`days_back` setting)
   - Check ServiceNow permissions for the user

3. **Processing Errors**
   - Check logs for detailed error messages
   - Verify RAG system components are healthy
   - Ensure sufficient disk space for caching

## Data Flow

1. **Fetch**: Scheduler retrieves incidents from ServiceNow API
2. **Filter**: Apply priority, state, and category filters
3. **Process**: Convert incidents to structured documents
4. **Cache**: Store in SQLite for change detection
5. **Ingest**: Add to RAG system via ingestion engine
6. **Index**: Create vector embeddings and store in FAISS

## Security Considerations

- Store ServiceNow credentials securely in environment variables
- Use dedicated ServiceNow user with minimal required permissions
- Enable HTTPS for ServiceNow API communication
- Regularly rotate ServiceNow credentials
- Monitor access logs for unusual activity

## Performance Tuning

### Batch Size
- Increase `batch_size` for faster processing of large datasets
- Decrease for lower memory usage

### Fetch Interval
- Increase `fetch_interval_minutes` to reduce API load
- Decrease for more real-time synchronization

### Caching
- Enable `cache_enabled` to avoid reprocessing unchanged incidents
- Adjust `cache_ttl_hours` based on update frequency

### Filtering
- Use `network_only: true` to focus on relevant incidents
- Adjust priority and state filters to reduce noise
- Set appropriate `days_back` to limit historical data

## Integration with Existing Workflow

The ServiceNow integration is designed to work seamlessly with your existing RAG system:

1. **Non-Disruptive**: Runs independently without affecting existing functionality
2. **Configurable**: Can be enabled/disabled without system restart
3. **Isolated**: Uses separate database and processing pipeline
4. **Compatible**: Works with existing document ingestion and querying

## Support & Maintenance

- Monitor integration status through API endpoints
- Review sync history for performance trends
- Clean up old cache data periodically
- Update configuration as ServiceNow schema changes
- Test integration after ServiceNow system updates 