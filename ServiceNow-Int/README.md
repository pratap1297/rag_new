# ServiceNow Integration

This project provides a complete solution for connecting to ServiceNow, creating tickets, and retrieving them based on various criteria.

## 📁 Files Overview

- `servicenow_connector.py` - Main ServiceNow connector class with all functionality
- `push_pull_tickets.py` - Simple script demonstrating core push/pull operations
- `servicenow_example.py` - Comprehensive example with advanced features
- `requirements.txt` - Python dependencies
- `env_template.txt` - Environment variables template
- `Servicenow-guide.md` - Detailed integration guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables

1. Copy `env_template.txt` to `.env`
2. Fill in your ServiceNow credentials:

```env
SERVICENOW_INSTANCE=your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
```

### 3. Run the Examples

**Simple Push/Pull Demo:**
```bash
python push_pull_tickets.py
```

**Comprehensive Demo:**
```bash
python servicenow_example.py
```

## 🔧 Core Functionality

### ServiceNowConnector Class

The main class provides these key methods:

#### Connection
- `test_connection()` - Test ServiceNow connectivity
- `__init__()` - Initialize with credentials from environment

#### Creating Tickets
- `create_incident(incident_data)` - Create a single incident
- `bulk_create_incidents(incidents_list)` - Create multiple incidents

#### Retrieving Tickets
- `get_incidents(filters=None, limit=100)` - Get incidents with optional filters
- `get_incident_by_number(incident_number)` - Get specific incident by number
- `get_incidents_by_priority(priority)` - Filter by priority (1-5)
- `get_incidents_by_state(state)` - Filter by state (1=New, 2=In Progress, etc.)
- `get_incidents_by_assigned_to(user_id)` - Filter by assigned user
- `get_all_incidents(filters=None)` - Get all incidents with pagination

#### Updating Tickets
- `update_incident(incident_sys_id, update_data)` - Update existing incident

## 📝 Usage Examples

### Basic Connection Test

```python
from servicenow_connector import ServiceNowConnector

# Initialize connector
sn = ServiceNowConnector()

# Test connection
if sn.test_connection():
    print("✅ Connected to ServiceNow!")
else:
    print("❌ Connection failed")
```

### Creating Tickets

```python
# Single ticket
ticket_data = {
    'short_description': 'Server Down',
    'description': 'Production server is not responding',
    'priority': '1',  # Critical
    'category': 'Hardware'
}

created_ticket = sn.create_incident(ticket_data)
print(f"Created ticket: {created_ticket['number']}")

# Multiple tickets
tickets = [
    {
        'short_description': 'Email Issues',
        'description': 'Users cannot send emails',
        'priority': '2'
    },
    {
        'short_description': 'Printer Offline',
        'description': 'Office printer not working',
        'priority': '3'
    }
]

created_tickets = sn.bulk_create_incidents(tickets)
print(f"Created {len(created_tickets)} tickets")
```

### Retrieving Tickets

```python
# Get all critical tickets
critical_tickets = sn.get_incidents_by_priority('1')

# Get new tickets
new_tickets = sn.get_incidents_by_state('1')

# Get tickets with custom filters
filters = {
    'category': 'Hardware',
    'priority': ['1', '2']  # Critical or High
}
filtered_tickets = sn.get_incidents(filters=filters)

# Get specific ticket by number
ticket = sn.get_incident_by_number('INC0000123')
```

### Advanced Filtering

```python
# Multiple criteria
complex_filters = {
    'priority': ['1', '2'],      # Critical or High priority
    'state': ['1', '2'],         # New or In Progress
    'category': 'Software'       # Software category
}

tickets = sn.get_incidents(filters=complex_filters, limit=50)
```

## 🔍 ServiceNow Field Reference

### Priority Values
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

### Common Fields
- `short_description` - Brief title (required)
- `description` - Detailed description (required)
- `priority` - Priority level (1-5)
- `urgency` - Urgency level (1-4)
- `impact` - Impact level (1-4)
- `category` - Category (Hardware, Software, Network, etc.)
- `subcategory` - Subcategory
- `caller_id` - Person who reported the incident
- `assigned_to` - Person assigned to resolve
- `assignment_group` - Group assigned to resolve

## 🛡️ Security Best Practices

1. **Never hardcode credentials** - Always use environment variables
2. **Use HTTPS** - All connections are secure by default
3. **Limit permissions** - Use service accounts with minimal required permissions
4. **Rotate credentials** - Regularly update passwords
5. **Monitor API usage** - Keep track of API calls and limits

## 🔧 Error Handling

The connector includes comprehensive error handling:

- **Connection errors** - Network and authentication issues
- **API errors** - ServiceNow API response errors
- **Validation errors** - Missing required fields
- **Retry logic** - Automatic retry with exponential backoff

## 📊 Logging

All operations are logged with appropriate levels:

- `INFO` - Successful operations
- `ERROR` - Failed operations with details
- `DEBUG` - Detailed debugging information

## 🚨 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check instance URL (without https://)
   - Verify username/password
   - Ensure API access is enabled

2. **Authentication Error**
   - Verify credentials in `.env` file
   - Check if account is locked
   - Confirm user has incident table access

3. **Missing Required Fields**
   - Ensure `short_description` and `description` are provided
   - Check field names match ServiceNow schema

4. **API Limits**
   - ServiceNow has rate limits
   - Use pagination for large datasets
   - Implement delays between bulk operations

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Tips

1. **Use filters** - Always filter queries to reduce data transfer
2. **Pagination** - Use `get_all_incidents()` for large datasets
3. **Bulk operations** - Use `bulk_create_incidents()` for multiple tickets
4. **Connection reuse** - Reuse the same connector instance
5. **Caching** - Cache frequently accessed data

## 🔄 Integration Patterns

### Scheduled Ticket Creation
```python
import schedule
import time

def create_daily_report():
    sn = ServiceNowConnector()
    # Create daily report ticket
    
schedule.every().day.at("09:00").do(create_daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Monitoring Integration
```python
def check_critical_tickets():
    sn = ServiceNowConnector()
    critical = sn.get_incidents_by_priority('1')
    
    if len(critical) > 10:
        # Send alert
        pass
```

## 📚 Additional Resources

- [ServiceNow REST API Documentation](https://docs.servicenow.com/bundle/tokyo-application-development/page/integrate/inbound-rest/concept/c_RESTAPI.html)
- [ServiceNow Table API](https://docs.servicenow.com/bundle/tokyo-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html)
- [ServiceNow Query Operators](https://docs.servicenow.com/bundle/tokyo-platform-user-interface/page/use/common-ui-elements/reference/r_OpAvailableFiltersQueries.html)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 