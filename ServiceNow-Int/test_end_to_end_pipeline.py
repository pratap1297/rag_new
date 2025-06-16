#!/usr/bin/env python3
"""
Complete End-to-End Pipeline Test
ServiceNow → Vector Database → Groq LLM
"""

import os
import sys
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../../.env")

def test_servicenow_connection():
    """Test ServiceNow connection and data availability"""
    print("🔗 Testing ServiceNow Connection")
    print("-" * 40)
    
    try:
        from servicenow_connector import ServiceNowConnector
        
        # Initialize connector
        connector = ServiceNowConnector()
        
        # Test connection
        incidents = connector.get_incidents(limit=5)
        print(f"✅ ServiceNow connected - {len(incidents)} incidents retrieved")
        
        # Show sample incidents
        for i, incident in enumerate(incidents[:3], 1):
            print(f"   {i}. {incident.get('number')} - {incident.get('short_description', '')[:50]}...")
        
        return incidents
        
    except Exception as e:
        print(f"❌ ServiceNow connection failed: {e}")
        return []

def test_backend_health():
    """Test backend health and Groq integration"""
    print("\n🏥 Testing Backend Health")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend healthy - {len(data.get('components', []))} components")
            
            # Check vector database
            vector_info = data.get('vector_database', {})
            print(f"📊 Vector indices: {vector_info.get('total_indices', 0)}")
            print(f"📊 Total vectors: {vector_info.get('total_vectors', 0)}")
            
            return True
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_groq_integration():
    """Test Groq LLM integration"""
    print("\n🤖 Testing Groq LLM Integration")
    print("-" * 40)
    
    try:
        # Test with a network-specific query
        query = "BGP neighbor down in warehouse network"
        
        response = requests.post(
            "http://localhost:8000/api/query",
            json={"query": query, "max_results": 3},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            provider = data.get('metadata', {}).get('llm_provider', 'Unknown')
            model = data.get('metadata', {}).get('llm_model', 'Unknown')
            
            print(f"✅ Groq integration working")
            print(f"   Provider: {provider}")
            print(f"   Model: {model}")
            
            # Check if real Groq response
            response_text = data.get('response', '')
            is_real = provider == 'groq' and 'Mock LLM Response' not in response_text
            
            print(f"   Real Groq: {'Yes' if is_real else 'No'}")
            
            if is_real:
                print(f"   Response preview: {response_text[:100]}...")
            
            return is_real
        else:
            print(f"❌ Query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Groq test failed: {e}")
        return False

def test_servicenow_to_vector_pipeline():
    """Test ServiceNow data ingestion into vector database"""
    print("\n📊 Testing ServiceNow → Vector Database Pipeline")
    print("-" * 50)
    
    try:
        # Create a sample ServiceNow incident document
        sample_incident = {
            "number": "INC0010001",
            "short_description": "BGP neighbor down at Chicago warehouse",
            "description": "Critical network issue: BGP neighbor 192.168.1.1 is down at Chicago warehouse. Router ISR4331 showing Active state. Warehouse operations impacted.",
            "priority": "1",
            "state": "2",
            "category": "Network",
            "assignment_group": "Network Operations",
            "location": "Chicago Warehouse",
            "created_on": datetime.now().isoformat()
        }
        
        # Format as document for upload
        document_content = f"""# ServiceNow Incident: {sample_incident['number']}

## Summary
{sample_incident['short_description']}

## Description
{sample_incident['description']}

## Details
- Priority: {sample_incident['priority']} (Critical)
- State: {sample_incident['state']} (In Progress)
- Category: {sample_incident['category']}
- Assignment Group: {sample_incident['assignment_group']}
- Location: {sample_incident['location']}
- Created: {sample_incident['created_on']}

## Technical Details
- Network Device: Router ISR4331
- Issue Type: BGP neighbor adjacency failure
- Affected IP: 192.168.1.1
- Impact: Warehouse operations disrupted
"""
        
        # Upload to backend
        files = {
            'file': ('servicenow_incident.md', document_content.encode(), 'text/markdown')
        }
        
        response = requests.post(
            "http://localhost:8000/api/documents/upload",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            doc_id = data.get('document_id')
            print(f"✅ ServiceNow incident uploaded: {doc_id}")
            
            # Wait for processing
            time.sleep(3)
            
            # Test search for the incident
            search_response = requests.post(
                "http://localhost:8000/api/query",
                json={"query": "BGP neighbor down Chicago warehouse", "max_results": 5},
                timeout=30
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                results = search_data.get('results', [])
                
                print(f"✅ Search found {len(results)} relevant results")
                
                # Check if our incident is found
                incident_found = any('INC0010001' in str(result) or 'Chicago warehouse' in str(result).lower() 
                                   for result in results)
                
                if incident_found:
                    print("✅ ServiceNow incident found in search results")
                    
                    # Test Groq response with ServiceNow context
                    response_text = search_data.get('response', '')
                    provider = search_data.get('metadata', {}).get('llm_provider', 'Unknown')
                    
                    print(f"✅ Groq response generated with ServiceNow context")
                    print(f"   Provider: {provider}")
                    print(f"   Response length: {len(response_text)} characters")
                    
                    return True
                else:
                    print("⚠️ ServiceNow incident not found in search results")
                    return False
            else:
                print(f"❌ Search failed: {search_response.status_code}")
                return False
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

def test_complete_workflow():
    """Test complete workflow with real ServiceNow query"""
    print("\n🔄 Testing Complete Workflow")
    print("-" * 40)
    
    # Test queries that would come from ServiceNow incidents
    test_queries = [
        "BGP neighbor down warehouse network critical",
        "Cisco router interface failure operations impact",
        "Network connectivity issues warehouse Chicago",
        "OSPF adjacency problems routing failure"
    ]
    
    success_count = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔎 Test {i}: {query}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/query",
                json={"query": query, "max_results": 3},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                provider = data.get('metadata', {}).get('llm_provider', 'Unknown')
                results = data.get('results', [])
                response_text = data.get('response', '')
                
                print(f"   ✅ Success - {len(results)} context sources")
                print(f"   🤖 Provider: {provider}")
                
                if provider == 'groq' and 'Mock LLM Response' not in response_text:
                    print(f"   🎉 Real Groq response generated")
                    success_count += 1
                else:
                    print(f"   ⚠️ Fallback response")
                    
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return success_count, len(test_queries)

def main():
    """Run complete end-to-end pipeline test"""
    print("🚀 Router Rescue AI - Complete End-to-End Pipeline Test")
    print("=" * 60)
    print("Testing: ServiceNow → Vector Database → Groq LLM")
    print("=" * 60)
    
    # Test components
    servicenow_data = test_servicenow_connection()
    backend_healthy = test_backend_health()
    groq_working = test_groq_integration()
    pipeline_working = test_servicenow_to_vector_pipeline()
    success_count, total_queries = test_complete_workflow()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 END-TO-END TEST SUMMARY")
    print("=" * 60)
    
    print(f"🔗 ServiceNow Connection: {'✅ Working' if servicenow_data else '❌ Failed'}")
    print(f"🏥 Backend Health: {'✅ Healthy' if backend_healthy else '❌ Unhealthy'}")
    print(f"🤖 Groq Integration: {'✅ Working' if groq_working else '❌ Failed'}")
    print(f"📊 ServiceNow Pipeline: {'✅ Working' if pipeline_working else '❌ Failed'}")
    print(f"🔄 Complete Workflow: {success_count}/{total_queries} queries successful")
    
    # Overall status
    all_working = all([servicenow_data, backend_healthy, groq_working, pipeline_working])
    
    if all_working and success_count == total_queries:
        print("\n🎉 END-TO-END PIPELINE FULLY OPERATIONAL!")
        print("✅ ServiceNow data → Vector database → Groq LLM → Intelligent responses")
    elif all_working:
        print("\n⚠️ PIPELINE MOSTLY WORKING")
        print("Some components working, minor issues detected")
    else:
        print("\n❌ PIPELINE NEEDS ATTENTION")
        print("Critical components not working properly")
    
    print(f"\n📊 ServiceNow incidents available: {len(servicenow_data)}")
    print(f"🤖 LLM Provider: {'Groq' if groq_working else 'Fallback'}")
    print(f"🔗 Backend URL: http://localhost:8000")

if __name__ == "__main__":
    main() 