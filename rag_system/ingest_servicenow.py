#!/usr/bin/env python3
"""
Ingest ServiceNow incidents into RAG system
"""

import sys
import os
sys.path.append('src')

from src.core.dependency_container import DependencyContainer
from src.core.config_manager import ConfigManager

def main():
    print("🎫 ServiceNow Incidents Ingestion")
    print("=" * 50)
    
    try:
        # Initialize the system
        container = DependencyContainer()
        
        # Register core services
        from src.core.dependency_container import register_core_services
        register_core_services(container)
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        if not ingestion_engine:
            print("❌ Ingestion engine not available")
            return
        
        print("✅ Ingestion engine initialized")
        
        # Ingest the ServiceNow incidents file
        file_path = "data/uploads/ServiceNow_Incidents_Last30Days.json"
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        print(f"📁 Ingesting file: {file_path}")
        
        result = ingestion_engine.ingest_file(file_path)
        
        print(f"🔍 Ingestion result: {result}")
        
        if result.get('status') == 'success':
            print(f"✅ Successfully ingested ServiceNow incidents!")
            print(f"📊 Chunks created: {result.get('chunks_created', 0)}")
            print(f"📋 File: {result.get('file_name', 'N/A')}")
        else:
            print(f"❌ Ingestion failed: {result.get('error', 'Unknown error')}")
            if 'details' in result:
                print(f"📋 Details: {result['details']}")
            if 'traceback' in result:
                print(f"🔍 Traceback: {result['traceback']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 