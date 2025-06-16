"""
ServiceNow Connector for RAG System
Enhanced connector with RAG system integration capabilities
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from urllib.parse import quote_plus
import re
import time

try:
    from ...core.error_handling import IntegrationError, AuthenticationError, APIError
except ImportError:
    # Fallback for when running from different contexts
    try:
        from core.error_handling import IntegrationError, AuthenticationError, APIError
    except ImportError:
        # Define minimal error classes if import fails
        class IntegrationError(Exception):
            pass
        class AuthenticationError(Exception):
            pass
        class APIError(Exception):
            pass

class ServiceNowConnector:
    """ServiceNow API connector optimized for RAG system integration"""
    
    def __init__(self, config_manager=None):
        """Initialize ServiceNow connector with RAG system configuration"""
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
        # Get ServiceNow credentials from environment (matching your .env format)
        self.instance = os.getenv('SERVICENOW_INSTANCE')
        self.username = os.getenv('SERVICENOW_USERNAME') 
        self.password = os.getenv('SERVICENOW_PASSWORD')
        self.table = os.getenv('SERVICENOW_TABLE', 'incident')
        
        # Validate required credentials
        if not all([self.instance, self.username, self.password]):
            missing = []
            if not self.instance: missing.append('SERVICENOW_INSTANCE')
            if not self.username: missing.append('SERVICENOW_USERNAME')
            if not self.password: missing.append('SERVICENOW_PASSWORD')
            
            raise ValueError(f"Missing ServiceNow credentials: {', '.join(missing)}")
        
        # Build base URL - your instance format: dev319029.service-now.com
        if not self.instance.startswith('https://'):
            self.base_url = f"https://{self.instance}"
        else:
            self.base_url = self.instance
        
        # API endpoints
        self.incident_endpoint = f"{self.base_url}/api/now/table/{self.table}"
        
        # Session setup with enhanced configuration
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'RAG-System-ServiceNow-Integration/1.0'
        })
        
        # Connection timeout settings
        self.timeout = 30
        
        # Authentication state
        self._auth_token = None
        self._token_expiry = None
        
        # Rate limiting
        self._last_request_time = None
        self._min_request_interval = 0.1  # 100ms between requests
        
        # Input validation patterns
        self._sys_id_pattern = re.compile(r'^[a-zA-Z0-9]{32}$')
        self._number_pattern = re.compile(r'^[A-Z]{2,3}[0-9]{8}$')
        
        self.logger.info(f"ServiceNow connector initialized for instance: {self.instance}")
    
    def _validate_sys_id(self, sys_id: str) -> bool:
        """Validate ServiceNow sys_id format"""
        return bool(self._sys_id_pattern.match(sys_id))
    
    def _validate_number(self, number: str) -> bool:
        """Validate ServiceNow incident number format"""
        return bool(self._number_pattern.match(number))
    
    def _validate_filters(self, filters: Dict[str, Any]) -> None:
        """Validate query filters"""
        if not isinstance(filters, dict):
            raise ValueError("Filters must be a dictionary")
        
        for key, value in filters.items():
            if not isinstance(key, str):
                raise ValueError(f"Filter key must be string, got {type(key)}")
            
            # Validate sys_id format if present
            if key == 'sys_id' and not self._validate_sys_id(str(value)):
                raise ValueError(f"Invalid sys_id format: {value}")
            
            # Validate number format if present
            if key == 'number' and not self._validate_number(str(value)):
                raise ValueError(f"Invalid incident number format: {value}")
            
            # Validate date formats
            if key.endswith('_date') and value:
                try:
                    datetime.fromisoformat(str(value))
                except ValueError:
                    raise ValueError(f"Invalid date format for {key}: {value}")
    
    def test_connection(self) -> bool:
        """Test connection to ServiceNow instance with enhanced error reporting"""
        try:
            self.logger.info("Testing ServiceNow connection...")
            
            response = self.session.get(
                self.incident_endpoint,
                params={'sysparm_limit': 1},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully connected to ServiceNow: {self.base_url}")
                return True
            else:
                self.logger.error(f"Connection failed. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error("Connection timeout - ServiceNow instance may be slow or unreachable")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error - Check network connectivity and ServiceNow instance URL")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected connection error: {str(e)}")
            return False
    
    def get_incidents(self, filters: Optional[Dict[str, Any]] = None, 
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get incidents from ServiceNow with proper parameterization"""
        try:
            # Validate input parameters
            if limit < 1 or limit > 1000:
                raise ValueError("Limit must be between 1 and 1000")
            
            if filters:
                self._validate_filters(filters)
            
            # Ensure authentication
            self._ensure_authenticated()
            
            # Build query parameters safely
            query_params = {
                'sysparm_limit': str(limit),
                'sysparm_display_value': 'true',
                'sysparm_exclude_reference_link': 'true'
            }
            
            # Add filters using proper parameterization
            if filters:
                encoded_filters = []
                for key, value in filters.items():
                    # URL encode the key and value
                    encoded_key = quote_plus(key)
                    encoded_value = quote_plus(str(value))
                    encoded_filters.append(f"{encoded_key}={encoded_value}")
                
                query_params['sysparm_query'] = '^'.join(encoded_filters)
            
            # Make API request with rate limiting
            self._enforce_rate_limit()
            response = self.session.get(
                self.incident_endpoint,
                params=query_params,
                timeout=self.timeout
            )
            
            # Handle response
            if response.status_code == 200:
                data = response.json()
                return data.get('result', [])
            else:
                self._handle_error_response(response)
                
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to fetch incidents: {str(e)}")
        except Exception as e:
            raise IntegrationError(f"Error in get_incidents: {str(e)}")
    
    def get_incident(self, sys_id: str) -> Dict[str, Any]:
        """Get single incident by sys_id with validation"""
        try:
            # Validate sys_id
            if not self._validate_sys_id(sys_id):
                raise ValueError(f"Invalid sys_id format: {sys_id}")
            
            # Ensure authentication
            self._ensure_authenticated()
            
            # Make API request with rate limiting
            self._enforce_rate_limit()
            response = self.session.get(
                f"{self.base_url}/api/now/table/{self.table}/{sys_id}",
                params={
                    'sysparm_display_value': 'true',
                    'sysparm_exclude_reference_link': 'true'
                },
                timeout=self.timeout
            )
            
            # Handle response
            if response.status_code == 200:
                data = response.json()
                return data.get('result', {})
            else:
                self._handle_error_response(response)
                
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to fetch incident {sys_id}: {str(e)}")
        except Exception as e:
            raise IntegrationError(f"Error in get_incident: {str(e)}")
    
    def get_incident_by_number(self, incident_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific incident by its number"""
        try:
            params = {
                'sysparm_query': f'number={incident_number}',
                'sysparm_limit': 1
            }
            
            response = self.session.get(
                self.incident_endpoint,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                incidents = response.json()['result']
                return incidents[0] if incidents else None
            else:
                self.logger.error(f"Failed to get incident {incident_number}. Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting incident {incident_number}: {str(e)}")
            return None
    
    def get_recent_incidents(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get incidents created or updated in the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        filters = {
            'updated_after': cutoff_str
        }
        
        return self.get_incidents(filters=filters, limit=1000)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for diagnostics"""
        return {
            'instance': self.instance,
            'base_url': self.base_url,
            'username': self.username,
            'table': self.table,
            'connected': self.test_connection()
        }
    
    def _ensure_authenticated(self) -> None:
        """Ensure authentication is valid"""
        if not self._auth_token or datetime.now() >= self._token_expiry:
            self.logger.info("Authenticating with ServiceNow...")
            response = self.session.post(
                f"{self.base_url}/api/now/table/sys_user_hashed_credentials",
                json={
                    'user': self.username,
                    'password': self.password
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self._auth_token = auth_data['result']['sys_id']
                self._token_expiry = datetime.now() + timedelta(hours=1)
                self.logger.info("Authentication successful")
            else:
                self.logger.error(f"Authentication failed. Status: {response.status_code}, Response: {response.text}")
                raise AuthenticationError("Authentication failed")
    
    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle API error responses"""
        try:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            error_detail = error_data.get('error', {}).get('detail', '')
            
            if response.status_code == 401:
                raise AuthenticationError(f"Authentication failed: {error_message}")
            elif response.status_code == 403:
                raise AuthenticationError(f"Access denied: {error_message}")
            elif response.status_code == 404:
                raise APIError(f"Resource not found: {error_message}")
            elif response.status_code == 429:
                raise APIError(f"Rate limit exceeded: {error_message}")
            else:
                raise APIError(f"API error ({response.status_code}): {error_message} - {error_detail}")
                
        except json.JSONDecodeError:
            raise APIError(f"Invalid response from ServiceNow: {response.text}")
    
    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests"""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self._min_request_interval:
                time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = datetime.now() 