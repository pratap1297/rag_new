#!/usr/bin/env python3
"""
ServiceNow Incident Scheduler
Fetches incident details from ServiceNow on a regular basis using a configurable scheduler.
Includes caching, change detection, and callback processing for integration with other systems.
"""

import asyncio
import schedule
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading
import os
from dotenv import load_dotenv
import sqlite3
import hashlib
from pathlib import Path

from servicenow_connector import ServiceNowConnector

# Load environment variables
load_dotenv()

# Also try to load from root directory
import sys
from pathlib import Path
root_env_path = Path(__file__).parent.parent.parent / '.env'
if root_env_path.exists():
    load_dotenv(root_env_path)

@dataclass
class IncidentData:
    """Data class for incident information"""
    sys_id: str
    number: str
    short_description: str
    description: str
    priority: str
    priority_label: str
    state: str
    state_label: str
    assigned_to: str
    assigned_to_name: str
    category: str
    subcategory: str
    created_on: str
    updated_on: str
    resolved_on: Optional[str]
    closed_on: Optional[str]
    caller_id: str
    caller_name: str
    location: str
    impact: str
    urgency: str
    business_service: str
    configuration_item: str
    work_notes: str
    close_notes: str
    resolution_code: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def get_hash(self) -> str:
        """Generate hash for change detection"""
        content = f"{self.sys_id}{self.updated_on}{self.state}{self.assigned_to}"
        return hashlib.md5(content.encode()).hexdigest()

class ServiceNowScheduler:
    """ServiceNow incident scheduler with advanced features"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the scheduler"""
        self.config = config or self._load_default_config()
        self.connector = ServiceNowConnector()
        self.is_running = False
        self.scheduler_thread = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Setup logging
        self._setup_logging()
        
        # Setup database for caching
        self._setup_database()
        
        # Priority and state mappings
        self.priority_mapping = {
            '1': 'Critical',
            '2': 'High', 
            '3': 'Moderate',
            '4': 'Low',
            '5': 'Planning'
        }
        
        self.state_mapping = {
            '1': 'New',
            '2': 'In Progress',
            '3': 'On Hold',
            '6': 'Resolved',
            '7': 'Closed',
            '8': 'Canceled'
        }
        
        # Callbacks for incident processing
        self.incident_callbacks = []
        
        self.logger.info("ServiceNow Scheduler initialized")
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            'fetch_interval_minutes': int(os.getenv('SERVICENOW_FETCH_INTERVAL', '15')),
            'batch_size': int(os.getenv('SERVICENOW_BATCH_SIZE', '100')),
            'max_incidents_per_fetch': int(os.getenv('SERVICENOW_MAX_INCIDENTS', '1000')),
            'priority_filter': os.getenv('SERVICENOW_PRIORITY_FILTER', '1,2,3').split(','),
            'state_filter': os.getenv('SERVICENOW_STATE_FILTER', '1,2,3').split(','),
            'days_back': int(os.getenv('SERVICENOW_DAYS_BACK', '7')),
            'enable_caching': os.getenv('SERVICENOW_ENABLE_CACHING', 'true').lower() == 'true',
            'cache_ttl_hours': int(os.getenv('SERVICENOW_CACHE_TTL', '1')),
            'enable_change_detection': os.getenv('SERVICENOW_CHANGE_DETECTION', 'true').lower() == 'true',
            'categories_filter': os.getenv('SERVICENOW_CATEGORIES', '').split(',') if os.getenv('SERVICENOW_CATEGORIES') else [],
            'assigned_groups_filter': os.getenv('SERVICENOW_ASSIGNED_GROUPS', '').split(',') if os.getenv('SERVICENOW_ASSIGNED_GROUPS') else []
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('servicenow_scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_database(self):
        """Setup SQLite database for caching"""
        self.db_path = Path('servicenow_cache.db')
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    sys_id TEXT PRIMARY KEY,
                    number TEXT UNIQUE,
                    data TEXT,
                    hash TEXT,
                    fetched_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS fetch_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fetch_time TIMESTAMP,
                    incidents_count INTEGER,
                    new_incidents INTEGER,
                    updated_incidents INTEGER,
                    errors TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_incidents_updated 
                ON incidents(updated_at)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_incidents_number 
                ON incidents(number)
            ''')
    
    def add_incident_callback(self, callback):
        """Add callback function for incident processing"""
        self.incident_callbacks.append(callback)
        self.logger.info(f"Added incident callback: {callback.__name__}")
    
    def _build_query_filters(self) -> Dict[str, Any]:
        """Build query filters based on configuration"""
        filters = {}
        
        # Priority filter
        if self.config['priority_filter']:
            filters['priority'] = self.config['priority_filter']
        
        # State filter
        if self.config['state_filter']:
            filters['state'] = self.config['state_filter']
        
        # Date filter - incidents created/updated in last N days
        if self.config['days_back'] > 0:
            cutoff_date = datetime.now() - timedelta(days=self.config['days_back'])
            filters['sys_updated_on'] = f">={cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Category filter
        if self.config['categories_filter']:
            filters['category'] = self.config['categories_filter']
        
        # Assigned groups filter
        if self.config['assigned_groups_filter']:
            filters['assignment_group'] = self.config['assigned_groups_filter']
        
        return filters
    
    def _parse_incident_data(self, raw_incident: Dict) -> IncidentData:
        """Parse raw incident data into structured format"""
        return IncidentData(
            sys_id=raw_incident.get('sys_id', ''),
            number=raw_incident.get('number', ''),
            short_description=raw_incident.get('short_description', ''),
            description=raw_incident.get('description', ''),
            priority=raw_incident.get('priority', ''),
            priority_label=self.priority_mapping.get(raw_incident.get('priority', ''), 'Unknown'),
            state=raw_incident.get('state', ''),
            state_label=self.state_mapping.get(raw_incident.get('state', ''), 'Unknown'),
            assigned_to=raw_incident.get('assigned_to', {}).get('value', '') if isinstance(raw_incident.get('assigned_to'), dict) else raw_incident.get('assigned_to', ''),
            assigned_to_name=raw_incident.get('assigned_to', {}).get('display_value', '') if isinstance(raw_incident.get('assigned_to'), dict) else '',
            category=raw_incident.get('category', ''),
            subcategory=raw_incident.get('subcategory', ''),
            created_on=raw_incident.get('sys_created_on', ''),
            updated_on=raw_incident.get('sys_updated_on', ''),
            resolved_on=raw_incident.get('resolved_at', ''),
            closed_on=raw_incident.get('closed_at', ''),
            caller_id=raw_incident.get('caller_id', {}).get('value', '') if isinstance(raw_incident.get('caller_id'), dict) else raw_incident.get('caller_id', ''),
            caller_name=raw_incident.get('caller_id', {}).get('display_value', '') if isinstance(raw_incident.get('caller_id'), dict) else '',
            location=raw_incident.get('location', {}).get('display_value', '') if isinstance(raw_incident.get('location'), dict) else raw_incident.get('location', ''),
            impact=raw_incident.get('impact', ''),
            urgency=raw_incident.get('urgency', ''),
            business_service=raw_incident.get('business_service', {}).get('display_value', '') if isinstance(raw_incident.get('business_service'), dict) else raw_incident.get('business_service', ''),
            configuration_item=raw_incident.get('cmdb_ci', {}).get('display_value', '') if isinstance(raw_incident.get('cmdb_ci'), dict) else raw_incident.get('cmdb_ci', ''),
            work_notes=raw_incident.get('work_notes', ''),
            close_notes=raw_incident.get('close_notes', ''),
            resolution_code=raw_incident.get('close_code', '')
        )
    
    def _cache_incident(self, incident: IncidentData):
        """Cache incident data"""
        if not self.config['enable_caching']:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO incidents 
                    (sys_id, number, data, hash, fetched_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    incident.sys_id,
                    incident.number,
                    json.dumps(incident.to_dict()),
                    incident.get_hash(),
                    datetime.now().isoformat(),
                    incident.updated_on
                ))
        except Exception as e:
            self.logger.error(f"Error caching incident {incident.number}: {str(e)}")
    
    def _get_cached_incident(self, sys_id: str) -> Optional[IncidentData]:
        """Get cached incident data"""
        if not self.config['enable_caching']:
            return None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT data FROM incidents WHERE sys_id = ?',
                    (sys_id,)
                )
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    return IncidentData(**data)
        except Exception as e:
            self.logger.error(f"Error retrieving cached incident {sys_id}: {str(e)}")
        
        return None
    
    def _is_incident_changed(self, incident: IncidentData) -> bool:
        """Check if incident has changed since last fetch"""
        if not self.config['enable_change_detection']:
            return True
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT hash FROM incidents WHERE sys_id = ?',
                    (incident.sys_id,)
                )
                row = cursor.fetchone()
                if row:
                    return row[0] != incident.get_hash()
                return True  # New incident
        except Exception as e:
            self.logger.error(f"Error checking incident changes {incident.sys_id}: {str(e)}")
            return True
    
    def _record_fetch_history(self, incidents_count: int, new_count: int, updated_count: int, errors: str = ""):
        """Record fetch history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO fetch_history 
                    (fetch_time, incidents_count, new_incidents, updated_incidents, errors)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    incidents_count,
                    new_count,
                    updated_count,
                    errors
                ))
        except Exception as e:
            self.logger.error(f"Error recording fetch history: {str(e)}")
    
    async def _process_incident_callbacks(self, incidents: List[IncidentData]):
        """Process incident callbacks asynchronously"""
        if not self.incident_callbacks:
            return
        
        for callback in self.incident_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(incidents)
                else:
                    # Run sync callback in executor
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, callback, incidents
                    )
            except Exception as e:
                self.logger.error(f"Error in incident callback {callback.__name__}: {str(e)}")
    
    def fetch_incidents(self) -> List[IncidentData]:
        """Fetch incidents from ServiceNow"""
        self.logger.info("Starting incident fetch...")
        
        try:
            # Test connection first
            if not self.connector.test_connection():
                self.logger.error("ServiceNow connection failed")
                return []
            
            # Build filters
            filters = self._build_query_filters()
            self.logger.info(f"Fetching incidents with filters: {filters}")
            
            # Fetch incidents
            raw_incidents = self.connector.get_all_incidents(
                filters=filters,
                page_size=self.config['batch_size']
            )
            
            if not raw_incidents:
                self.logger.info("No incidents found")
                return []
            
            # Limit incidents if configured
            if self.config['max_incidents_per_fetch'] > 0:
                raw_incidents = raw_incidents[:self.config['max_incidents_per_fetch']]
            
            # Parse incidents
            incidents = []
            new_count = 0
            updated_count = 0
            
            for raw_incident in raw_incidents:
                try:
                    incident = self._parse_incident_data(raw_incident)
                    
                    # Check if incident is new or changed
                    cached_incident = self._get_cached_incident(incident.sys_id)
                    if cached_incident is None:
                        new_count += 1
                    elif self._is_incident_changed(incident):
                        updated_count += 1
                    
                    incidents.append(incident)
                    
                    # Cache the incident
                    self._cache_incident(incident)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing incident: {str(e)}")
                    continue
            
            self.logger.info(f"Fetched {len(incidents)} incidents ({new_count} new, {updated_count} updated)")
            
            # Record fetch history
            self._record_fetch_history(len(incidents), new_count, updated_count)
            
            # Process callbacks asynchronously
            if incidents:
                asyncio.create_task(self._process_incident_callbacks(incidents))
            
            return incidents
            
        except Exception as e:
            error_msg = f"Error fetching incidents: {str(e)}"
            self.logger.error(error_msg)
            self._record_fetch_history(0, 0, 0, error_msg)
            return []
    
    def get_incident_by_number(self, incident_number: str) -> Optional[IncidentData]:
        """Get specific incident by number"""
        try:
            raw_incident = self.connector.get_incident_by_number(incident_number)
            if raw_incident:
                return self._parse_incident_data(raw_incident)
        except Exception as e:
            self.logger.error(f"Error fetching incident {incident_number}: {str(e)}")
        return None
    
    def get_cached_incidents(self, limit: int = 100) -> List[IncidentData]:
        """Get cached incidents"""
        incidents = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT data FROM incidents 
                    ORDER BY updated_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                for row in cursor.fetchall():
                    data = json.loads(row[0])
                    incidents.append(IncidentData(**data))
                    
        except Exception as e:
            self.logger.error(f"Error retrieving cached incidents: {str(e)}")
        
        return incidents
    
    def get_fetch_statistics(self) -> Dict[str, Any]:
        """Get fetch statistics"""
        stats = {
            'total_cached_incidents': 0,
            'last_fetch_time': None,
            'total_fetches': 0,
            'average_incidents_per_fetch': 0,
            'error_rate': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total cached incidents
                cursor = conn.execute('SELECT COUNT(*) FROM incidents')
                stats['total_cached_incidents'] = cursor.fetchone()[0]
                
                # Fetch history stats
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_fetches,
                        MAX(fetch_time) as last_fetch,
                        AVG(incidents_count) as avg_incidents,
                        SUM(CASE WHEN errors != '' THEN 1 ELSE 0 END) as error_count
                    FROM fetch_history
                ''')
                
                row = cursor.fetchone()
                if row:
                    stats['total_fetches'] = row[0]
                    stats['last_fetch_time'] = row[1]
                    stats['average_incidents_per_fetch'] = round(row[2] or 0, 2)
                    stats['error_rate'] = round((row[3] / max(row[0], 1)) * 100, 2)
                    
        except Exception as e:
            self.logger.error(f"Error getting statistics: {str(e)}")
        
        return stats
    
    def start_scheduler(self):
        """Start the incident fetching scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.logger.info(f"Starting scheduler with {self.config['fetch_interval_minutes']} minute intervals")
        
        # Schedule the job
        schedule.every(self.config['fetch_interval_minutes']).minutes.do(self.fetch_incidents)
        
        # Run initial fetch
        self.fetch_incidents()
        
        # Start scheduler in separate thread
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started successfully")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.is_running:
            self.logger.warning("Scheduler is not running")
            return
        
        self.logger.info("Stopping scheduler...")
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.executor.shutdown(wait=True)
        
        self.logger.info("Scheduler stopped")
    
    def cleanup_old_cache(self, days_to_keep: int = 30):
        """Clean up old cached incidents"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM incidents 
                    WHERE fetched_at < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                
                cursor = conn.execute('''
                    DELETE FROM fetch_history 
                    WHERE fetch_time < ?
                ''', (cutoff_date.isoformat(),))
                
                self.logger.info(f"Cleaned up {deleted_count} old cached incidents")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {str(e)}")

# Example callback functions
async def process_network_incidents(incidents: List[IncidentData]):
    """Example callback for processing network-related incidents"""
    network_keywords = ['network', 'router', 'switch', 'firewall', 'vpn', 'bgp', 'ospf', 'vlan']
    
    network_incidents = []
    for incident in incidents:
        description_lower = incident.description.lower() + incident.short_description.lower()
        if any(keyword in description_lower for keyword in network_keywords):
            network_incidents.append(incident)
    
    if network_incidents:
        print(f"Found {len(network_incidents)} network-related incidents")
        # Process network incidents (e.g., send to vector database, create alerts, etc.)

def process_critical_incidents(incidents: List[IncidentData]):
    """Example callback for processing critical incidents"""
    critical_incidents = [inc for inc in incidents if inc.priority == '1']
    
    if critical_incidents:
        print(f"Found {len(critical_incidents)} critical incidents")
        # Process critical incidents (e.g., send alerts, escalate, etc.)

# Main execution
if __name__ == "__main__":
    # Create scheduler instance
    scheduler = ServiceNowScheduler()
    
    # Add callbacks
    scheduler.add_incident_callback(process_network_incidents)
    scheduler.add_incident_callback(process_critical_incidents)
    
    try:
        # Start the scheduler
        scheduler.start_scheduler()
        
        # Keep the main thread alive
        while True:
            time.sleep(10)
            
            # Print statistics every 10 minutes
            if int(time.time()) % 600 == 0:
                stats = scheduler.get_fetch_statistics()
                print(f"Scheduler Statistics: {stats}")
                
    except KeyboardInterrupt:
        print("Shutting down scheduler...")
        scheduler.stop_scheduler()
        print("Scheduler stopped") 