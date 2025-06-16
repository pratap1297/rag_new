I'll help you create a complete solution for connecting to ServiceNow, ingesting tickets, and retrieving them based on key values. Here's a comprehensive guide:I've created a comprehensive guide for ServiceNow integration that covers all the essential aspects you requested. Here's what the solution includes:

## Key Features:

**Connection Setup:**
- Secure credential management using environment variables
- Connection testing functionality
- Proper authentication handling

**Ticket Ingestion:**
- Single incident creation
- Bulk incident creation
- Input validation and error handling

**Ticket Retrieval:**
- Flexible filtering system
- Query by priority, state, assigned user, or custom criteria
- Pagination support for large datasets
- Specific incident lookup by number

**Advanced Features:**
- Retry logic with exponential backoff
- Comprehensive error handling
- Logging for debugging
- Security best practices

## Quick Start:

1. Install dependencies: `pip install requests python-dotenv`
2. Create `.env` file with your ServiceNow credentials
3. Use the ServiceNowConnector class to interact with your instance

The code is production-ready and includes proper error handling, logging, and security considerations. You can easily extend it to work with other ServiceNow tables (like Change Requests, Problems, etc.) by modifying the table endpoints.

# ServiceNow Integration Guide

## Prerequisites

1. **ServiceNow Instance**: Access to a ServiceNow instance (e.g., `https://your-instance.service-now.com`)
2. **Authentication**: Username/password or OAuth credentials
3. **API Access**: Ensure REST API access is enabled
4. **Python Libraries**: Install required packages

```bash
pip install requests python-dotenv
```

## Step 1: Setup Environment Variables

Create a `.env` file to store your credentials securely:

```env
SERVICENOW_INSTANCE=your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
```

## Step 2: Basic ServiceNow Connection Class

```python
import requests
import json
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class ServiceNowConnector:
    def __init__(self):
        self.instance = os.getenv('SERVICENOW_INSTANCE')
        self.username = os.getenv('SERVICENOW_USERNAME')
        self.password = os.getenv('SERVICENOW_PASSWORD')
        self.base_url = f"https://{self.instance}/api/now/table"
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self):
        """Test the connection to ServiceNow"""
        try:
            url = f"{self.base_url}/incident"
            response = requests.get(
                url, 
                auth=self.auth, 
                headers=self.headers,
                params={'sysparm_limit': 1}
            )
            
            if response.status_code == 200:
                self.logger.info("Connection to ServiceNow successful!")
                return True
            else:
                self.logger.error(f"Connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection error: {str(e)}")
            return False
```

## Step 3: Create/Ingest Tickets

```python
def create_incident(self, incident_data):
    """Create a new incident in ServiceNow"""
    try:
        url = f"{self.base_url}/incident"
        
        # Validate required fields
        required_fields = ['short_description', 'description']
        for field in required_fields:
            if field not in incident_data:
                raise ValueError(f"Missing required field: {field}")
        
        response = requests.post(
            url,
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(incident_data)
        )
        
        if response.status_code == 201:
            result = response.json()
            self.logger.info(f"Incident created successfully: {result['result']['number']}")
            return result['result']
        else:
            self.logger.error(f"Failed to create incident: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        self.logger.error(f"Error creating incident: {str(e)}")
        return None

def bulk_create_incidents(self, incidents_list):
    """Create multiple incidents"""
    created_incidents = []
    
    for incident_data in incidents_list:
        result = self.create_incident(incident_data)
        if result:
            created_incidents.append(result)
    
    return created_incidents
```

## Step 4: Retrieve Tickets

```python
def get_incidents(self, filters=None, limit=100):
    """Retrieve incidents based on filters"""
    try:
        url = f"{self.base_url}/incident"
        
        params = {
            'sysparm_limit': limit,
            'sysparm_offset': 0
        }
        
        # Add filters if provided
        if filters:
            query_parts = []
            for key, value in filters.items():
                if isinstance(value, list):
                    # Handle multiple values (OR condition)
                    or_conditions = [f"{key}={v}" for v in value]
                    query_parts.append(f"({'^OR'.join(or_conditions)})")
                else:
                    query_parts.append(f"{key}={value}")
            
            if query_parts:
                params['sysparm_query'] = '^'.join(query_parts)
        
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            params=params
        )
        
        if response.status_code == 200:
            result = response.json()
            self.logger.info(f"Retrieved {len(result['result'])} incidents")
            return result['result']
        else:
            self.logger.error(f"Failed to retrieve incidents: {response.status_code}")
            return []
            
    except Exception as e:
        self.logger.error(f"Error retrieving incidents: {str(e)}")
        return []

def get_incident_by_number(self, incident_number):
    """Get a specific incident by number"""
    filters = {'number': incident_number}
    incidents = self.get_incidents(filters=filters, limit=1)
    return incidents[0] if incidents else None

def get_incidents_by_priority(self, priority):
    """Get incidents by priority (1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning)"""
    filters = {'priority': priority}
    return self.get_incidents(filters=filters)

def get_incidents_by_state(self, state):
    """Get incidents by state"""
    filters = {'state': state}
    return self.get_incidents(filters=filters)

def get_incidents_by_assigned_to(self, user_id):
    """Get incidents assigned to a specific user"""
    filters = {'assigned_to': user_id}
    return self.get_incidents(filters=filters)
```

## Step 5: Usage Examples

```python
def main():
    # Initialize connector
    sn = ServiceNowConnector()
    
    # Test connection
    if not sn.test_connection():
        print("Failed to connect to ServiceNow")
        return
    
    # Example 1: Create sample incidents
    sample_incidents = [
        {
            'short_description': 'Server outage in production',
            'description': 'Production server is down, affecting all users',
            'priority': '1',  # Critical
            'category': 'Hardware',
            'subcategory': 'Server',
            'urgency': '1'
        },
        {
            'short_description': 'Email service slow',
            'description': 'Users reporting slow email response times',
            'priority': '3',  # Moderate
            'category': 'Software',
            'subcategory': 'Email',
            'urgency': '2'
        },
        {
            'short_description': 'Password reset request',
            'description': 'User unable to access system after password expiry',
            'priority': '4',  # Low
            'category': 'Access',
            'subcategory': 'Password',
            'urgency': '3'
        }
    ]
    
    # Create incidents
    print("Creating incidents...")
    created_incidents = sn.bulk_create_incidents(sample_incidents)
    print(f"Created {len(created_incidents)} incidents")
    
    # Example 2: Retrieve incidents by priority
    print("\nRetrieving critical incidents...")
    critical_incidents = sn.get_incidents_by_priority('1')
    for incident in critical_incidents:
        print(f"- {incident['number']}: {incident['short_description']}")
    
    # Example 3: Retrieve incidents by state
    print("\nRetrieving new incidents...")
    new_incidents = sn.get_incidents_by_state('1')  # New state
    for incident in new_incidents:
        print(f"- {incident['number']}: {incident['short_description']}")
    
    # Example 4: Custom filters
    print("\nRetrieving incidents with custom filters...")
    custom_filters = {
        'category': 'Hardware',
        'priority': ['1', '2']  # Critical or High priority
    }
    filtered_incidents = sn.get_incidents(filters=custom_filters)
    for incident in filtered_incidents:
        print(f"- {incident['number']}: {incident['short_description']} (Priority: {incident['priority']})")

if __name__ == "__main__":
    main()
```

## Step 6: Advanced Features

### Error Handling and Retry Logic

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

# Apply to methods
@retry_on_failure(max_retries=3)
def create_incident_with_retry(self, incident_data):
    return self.create_incident(incident_data)
```

### Pagination for Large Result Sets

```python
def get_all_incidents(self, filters=None, page_size=100):
    """Retrieve all incidents with pagination"""
    all_incidents = []
    offset = 0
    
    while True:
        url = f"{self.base_url}/incident"
        params = {
            'sysparm_limit': page_size,
            'sysparm_offset': offset
        }
        
        if filters:
            query_parts = []
            for key, value in filters.items():
                query_parts.append(f"{key}={value}")
            params['sysparm_query'] = '^'.join(query_parts)
        
        response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
        
        if response.status_code == 200:
            result = response.json()
            incidents = result['result']
            
            if not incidents:  # No more records
                break
                
            all_incidents.extend(incidents)
            offset += page_size
            
            self.logger.info(f"Retrieved {len(all_incidents)} incidents so far...")
        else:
            break
    
    return all_incidents
```

## Common ServiceNow Field References

### Incident Priority Values
- 1 = Critical
- 2 = High
- 3 = Moderate
- 4 = Low
- 5 = Planning

### Incident State Values
- 1 = New
- 2 = In Progress
- 3 = On Hold
- 6 = Resolved
- 7 = Closed

### Common Query Operators
- `=` : Equals
- `!=` : Not equals
- `>` : Greater than
- `<` : Less than
- `CONTAINS` : Contains text
- `STARTSWITH` : Starts with text
- `ISEMPTY` : Field is empty
- `ISNOTEMPTY` : Field is not empty

## Security Best Practices

1. **Never hardcode credentials** - Use environment variables or secure vaults
2. **Use HTTPS** - Always use secure connections
3. **Implement rate limiting** - Respect ServiceNow API limits
4. **Log responsibly** - Don't log sensitive information
5. **Use service accounts** - Create dedicated API users with minimal permissions
6. **Implement token refresh** - For OAuth authentication