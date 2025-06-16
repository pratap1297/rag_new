#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Processors + UI Integration Test
Tests the complete workflow: Processors -> API -> UI -> Folder Monitoring
"""

import os
import sys
import time
import json
import requests
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'=' * 80}")
    print(f"{title.center(80)}")
    print(f"{'=' * 80}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-' * 60}")
    print(f"{title}")
    print(f"{'-' * 60}")

def check_api_server(api_url="http://localhost:8000", max_retries=3):
    """Check if API server is running"""
    print_section("API SERVER STATUS CHECK")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Server is running")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Components: {len(data.get('components', {}))}")
                print(f"   URL: {api_url}")
                return True
        except Exception as e:
            print(f"❌ Attempt {attempt + 1}: API server not responding - {e}")
            if attempt < max_retries - 1:
                print(f"   Retrying in 2 seconds...")
                time.sleep(2)
    
    print(f"❌ API server is not running at {api_url}")
    print(f"   Please start the server with: python rag_system/main.py")
    return False

def test_unified_processors_via_api():
    """Test unified processors through the API endpoints"""
    print_section("UNIFIED PROCESSORS VIA API")
    
    api_url = "http://localhost:8000"
    
    # Test documents for different processors
    test_documents = []
    
    # 1. Excel file (if available)
    excel_file = "document_generator/test_data/Facility_Managers_2024.xlsx"
    if os.path.exists(excel_file):
        test_documents.append({
            'name': 'Excel Facility Data',
            'path': excel_file,
            'type': 'excel',
            'endpoint': 'upload'
        })
    
    # 2. Create text documents for different processors
    text_documents = {
        'python_code.py': '''#!/usr/bin/env python3
"""
Sample Python code for unified processor testing
"""

def process_documents():
    """Process documents using unified processors"""
    processors = [
        'ExcelProcessor',
        'PDFProcessor', 
        'WordProcessor',
        'ImageProcessor',
        'TextProcessor',
        'ServiceNowProcessor'
    ]
    
    for processor in processors:
        print(f"Processing with {processor}")
    
    return "All processors tested successfully"

if __name__ == "__main__":
    result = process_documents()
    print(result)
''',
        'config.json': '''{
    "system": "unified-processors",
    "version": "2.0.0",
    "processors": {
        "excel": {
            "enabled": true,
            "extensions": [".xlsx", ".xls", ".xlsm", ".xlsb"]
        },
        "pdf": {
            "enabled": true,
            "extensions": [".pdf"],
            "azure_cv": true
        },
        "word": {
            "enabled": true,
            "extensions": [".docx", ".doc"]
        },
        "image": {
            "enabled": true,
            "extensions": [".jpg", ".png", ".bmp", ".tiff", ".gif"],
            "ocr": true
        },
        "text": {
            "enabled": true,
            "extensions": [".txt", ".md", ".py", ".js", ".json", ".csv"]
        },
        "servicenow": {
            "enabled": true,
            "api_integration": true
        }
    }
}''',
        'network_report.md': '''# Network Infrastructure Report

## Executive Summary
This report details the unified document processing system deployment across our network infrastructure.

## System Architecture
- **Unified Processors**: 6 different document types supported
- **API Integration**: RESTful endpoints for upload and ingestion
- **UI Interface**: Web-based document management
- **Folder Monitoring**: Automatic document processing

## Building Coverage
### Building A
- **WiFi**: 95% coverage with Cisco 3802I access points
- **Signal**: -65 dBm minimum strength
- **Processors**: Excel, PDF, Word, Image processing enabled

### Building B  
- **WiFi**: 90% coverage with Cisco 1562E access points
- **Signal**: -70 dBm minimum strength
- **Processors**: Full unified processor suite deployed

### Building C
- **WiFi**: Under deployment with mixed access points
- **Signal**: Variable by zone
- **Processors**: Testing phase with ServiceNow integration

## Recommendations
1. Complete Building C deployment
2. Enable folder monitoring for all buildings
3. Integrate ServiceNow ticketing system
4. Deploy Azure Computer Vision for PDF processing
''',
        'facility_data.csv': '''Name,Role,Building,Floor,Area,Phone,Email
John Smith,Senior Manager,Building A,Floor 2,North Wing,555-0101,john.smith@company.com
Maria Garcia,Facility Coordinator,Building A,Floor 1,Main Lobby,555-0102,maria.garcia@company.com
Michael Brown,Maintenance Lead,Building B,Floor 3,South Wing,555-0103,michael.brown@company.com
Lisa Wong,Security Manager,Building B,Floor 1,Security Office,555-0104,lisa.wong@company.com
David Chen,IT Support,Building C,Floor 2,Tech Center,555-0105,david.chen@company.com
Sarah Johnson,Operations Manager,Building A,Floor 3,Operations,555-0106,sarah.johnson@company.com
'''
    }
    
    # Create text files and add to test documents
    for filename, content in text_documents.items():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        test_documents.append({
            'name': filename.replace('_', ' ').replace('.py', ' (Python)').replace('.json', ' (JSON)').replace('.md', ' (Markdown)').replace('.csv', ' (CSV)').title(),
            'path': filename,
            'type': 'text',
            'endpoint': 'ingest'  # Text files use ingest endpoint
        })
    
    # Test each document through API
    results = []
    
    for doc in test_documents:
        print(f"\n📄 Testing: {doc['name']}")
        print(f"   File: {doc['path']}")
        print(f"   Type: {doc['type']}")
        print(f"   Endpoint: /{doc['endpoint']}")
        
        try:
            if doc['endpoint'] == 'ingest':
                # Text ingestion endpoint
                with open(doc['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata = {
                    "doc_path": f"/unified_test/{Path(doc['path']).stem}",
                    "title": doc['name'],
                    "source": "unified_processor_test",
                    "file_type": Path(doc['path']).suffix,
                    "processor_type": doc['type'],
                    "timestamp": datetime.now().isoformat()
                }
                
                payload = {
                    "text": content,
                    "metadata": metadata
                }
                
                response = requests.post(f"{api_url}/ingest", json=payload, timeout=30)
                
            else:
                # File upload endpoint
                metadata = {
                    "doc_path": f"/unified_test/{Path(doc['path']).stem}",
                    "title": doc['name'],
                    "source": "unified_processor_test",
                    "file_type": Path(doc['path']).suffix,
                    "processor_type": doc['type'],
                    "timestamp": datetime.now().isoformat()
                }
                
                with open(doc['path'], 'rb') as f:
                    files = {'file': (os.path.basename(doc['path']), f, 'application/octet-stream')}
                    data = {'metadata': json.dumps(metadata)}
                    
                    response = requests.post(f"{api_url}/upload", files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: {result.get('chunks_created', 0)} chunks created")
                
                results.append({
                    'document': doc['name'],
                    'status': 'success',
                    'chunks': result.get('chunks_created', 0),
                    'processor_type': doc['type'],
                    'is_update': result.get('is_update', False)
                })
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                
                results.append({
                    'document': doc['name'],
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}",
                    'processor_type': doc['type']
                })
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append({
                'document': doc['name'],
                'status': 'error',
                'error': str(e),
                'processor_type': doc['type']
            })
    
    # Clean up text files
    for filename in text_documents.keys():
        if os.path.exists(filename):
            os.remove(filename)
    
    # Summary
    print(f"\n📊 API INTEGRATION SUMMARY:")
    successful = sum(1 for r in results if r['status'] == 'success')
    total_chunks = sum(r.get('chunks', 0) for r in results if r['status'] == 'success')
    
    print(f"   • Total documents tested: {len(results)}")
    print(f"   • Successful: {successful}")
    print(f"   • Failed: {len(results) - successful}")
    print(f"   • Success rate: {successful/len(results)*100:.1f}%")
    print(f"   • Total chunks created: {total_chunks}")
    
    # Show results by processor type
    processor_stats = {}
    for result in results:
        proc_type = result['processor_type']
        if proc_type not in processor_stats:
            processor_stats[proc_type] = {'success': 0, 'total': 0, 'chunks': 0}
        
        processor_stats[proc_type]['total'] += 1
        if result['status'] == 'success':
            processor_stats[proc_type]['success'] += 1
            processor_stats[proc_type]['chunks'] += result.get('chunks', 0)
    
    print(f"\n   📋 Results by Processor Type:")
    for proc_type, stats in processor_stats.items():
        success_rate = stats['success'] / stats['total'] * 100
        print(f"      • {proc_type.upper()}: {stats['success']}/{stats['total']} ({success_rate:.1f}%) - {stats['chunks']} chunks")
    
    return results

def test_ui_functionality():
    """Test UI functionality by checking if it can be launched"""
    print_section("UI FUNCTIONALITY TEST")
    
    try:
        # Import the UI module
        from launch_fixed_ui import FixedRAGUI, check_server_status
        
        print("✅ UI module imported successfully")
        
        # Check if API server is accessible
        api_url = "http://localhost:8000"
        server_status = check_server_status(api_url)
        
        if server_status:
            print("✅ API server is accessible from UI")
            
            # Create UI instance
            ui = FixedRAGUI(api_url)
            print("✅ UI instance created successfully")
            
            # Test API connection check
            connection_status = ui.check_api_connection()
            print(f"✅ API connection status: {connection_status[:100]}...")
            
            # Test document paths retrieval
            doc_paths = ui.get_document_paths()
            print(f"✅ Document paths retrieved: {len(doc_paths)} documents")
            
            # Test vector store stats
            stats = ui.get_vector_store_stats()
            print(f"✅ Vector store stats: {stats[:100]}...")
            
            return True
        else:
            print("❌ API server not accessible from UI")
            return False
            
    except Exception as e:
        print(f"❌ UI functionality test failed: {e}")
        return False

def test_folder_monitoring_setup():
    """Test folder monitoring setup"""
    print_section("FOLDER MONITORING TEST")
    
    try:
        # Create test folder structure
        test_folder = Path("test_monitoring_folder")
        test_folder.mkdir(exist_ok=True)
        
        print(f"✅ Created test folder: {test_folder}")
        
        # Create test files in the folder
        test_files = {
            'auto_excel.xlsx': 'Excel file for auto-processing',
            'auto_document.txt': '''This is a test document for folder monitoring.

The unified processor system supports automatic folder monitoring that can:
1. Detect new files added to monitored folders
2. Automatically process them using the appropriate processor
3. Ingest the content into the RAG system
4. Update the vector store with new embeddings

This enables hands-free document processing workflows.''',
            'auto_config.json': '''{
    "monitoring": {
        "enabled": true,
        "folder": "test_monitoring_folder",
        "processors": ["excel", "text", "pdf", "word", "image"],
        "auto_ingest": true
    }
}'''
        }
        
        for filename, content in test_files.items():
            file_path = test_folder / filename
            if filename.endswith('.xlsx'):
                # For Excel, just create a placeholder (would need openpyxl for real Excel)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Excel placeholder - would be processed by ExcelProcessor")
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        print(f"✅ Created {len(test_files)} test files in monitoring folder")
        
        # Test folder monitoring API endpoint
        api_url = "http://localhost:8000"
        
        try:
            # Start monitoring
            response = requests.post(
                f"{api_url}/monitoring/start",
                json={"folder_path": str(test_folder.absolute())},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Folder monitoring started: {result.get('message', 'Success')}")
                
                # Check monitoring status
                time.sleep(2)  # Give it time to start
                
                status_response = requests.get(f"{api_url}/monitoring/status", timeout=5)
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"✅ Monitoring status: {status.get('status', 'unknown')}")
                    print(f"   Monitored folders: {len(status.get('monitored_folders', []))}")
                
                # Stop monitoring
                stop_response = requests.post(f"{api_url}/monitoring/stop", timeout=5)
                if stop_response.status_code == 200:
                    print("✅ Folder monitoring stopped successfully")
                
                return True
            else:
                print(f"❌ Failed to start folder monitoring: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Folder monitoring API test failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Folder monitoring setup failed: {e}")
        return False
    
    finally:
        # Clean up test folder
        try:
            import shutil
            if test_folder.exists():
                shutil.rmtree(test_folder)
                print(f"✅ Cleaned up test folder: {test_folder}")
        except Exception as e:
            print(f"⚠️ Failed to clean up test folder: {e}")

def test_query_functionality():
    """Test query functionality through API"""
    print_section("QUERY FUNCTIONALITY TEST")
    
    api_url = "http://localhost:8000"
    
    test_queries = [
        "What types of documents can the unified processors handle?",
        "Tell me about the network infrastructure in our buildings",
        "What are the facility management capabilities?",
        "How does the folder monitoring system work?",
        "What processors are available in the system?"
    ]
    
    successful_queries = 0
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        
        try:
            payload = {
                "query": query,
                "top_k": 3
            }
            
            response = requests.post(f"{api_url}/query", json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', 'No response')
                sources = result.get('sources', [])
                
                print(f"   ✅ Answer: {answer[:150]}...")
                print(f"   📚 Sources: {len(sources)} documents")
                successful_queries += 1
            else:
                print(f"   ❌ Query failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Query error: {e}")
    
    print(f"\n📊 QUERY TEST SUMMARY:")
    print(f"   • Total queries: {len(test_queries)}")
    print(f"   • Successful: {successful_queries}")
    print(f"   • Success rate: {successful_queries/len(test_queries)*100:.1f}%")
    
    return successful_queries == len(test_queries)

def main():
    """Main integration test"""
    print_header("UNIFIED PROCESSORS + UI + FOLDER MONITORING INTEGRATION")
    
    print(f"\n🎯 INTEGRATION TEST OVERVIEW:")
    print(f"   • Test unified processors through API endpoints")
    print(f"   • Verify UI functionality and API connectivity")
    print(f"   • Test folder monitoring capabilities")
    print(f"   • Validate query functionality")
    print(f"   • Complete end-to-end workflow verification")
    
    # Check if API server is running
    if not check_api_server():
        print(f"\n❌ INTEGRATION TEST FAILED")
        print(f"   Please start the API server first:")
        print(f"   cd rag_system && python main.py")
        return
    
    # Run integration tests
    test_results = {}
    
    # Test 1: Unified processors via API
    try:
        api_results = test_unified_processors_via_api()
        test_results['api_integration'] = len([r for r in api_results if r['status'] == 'success']) > 0
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        test_results['api_integration'] = False
    
    # Test 2: UI functionality
    try:
        test_results['ui_functionality'] = test_ui_functionality()
    except Exception as e:
        print(f"❌ UI functionality test failed: {e}")
        test_results['ui_functionality'] = False
    
    # Test 3: Folder monitoring
    try:
        test_results['folder_monitoring'] = test_folder_monitoring_setup()
    except Exception as e:
        print(f"❌ Folder monitoring test failed: {e}")
        test_results['folder_monitoring'] = False
    
    # Test 4: Query functionality
    try:
        test_results['query_functionality'] = test_query_functionality()
    except Exception as e:
        print(f"❌ Query functionality test failed: {e}")
        test_results['query_functionality'] = False
    
    # Final summary
    print_header("INTEGRATION TEST COMPLETE")
    
    successful_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\n🎉 INTEGRATION TEST RESULTS:")
    print(f"   • API Integration: {'✅' if test_results.get('api_integration') else '❌'}")
    print(f"   • UI Functionality: {'✅' if test_results.get('ui_functionality') else '❌'}")
    print(f"   • Folder Monitoring: {'✅' if test_results.get('folder_monitoring') else '❌'}")
    print(f"   • Query Functionality: {'✅' if test_results.get('query_functionality') else '❌'}")
    print(f"   • Overall Success: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    
    if successful_tests == total_tests:
        print(f"\n🚀 COMPLETE SUCCESS!")
        print(f"   • Unified processors working through API")
        print(f"   • UI interface fully functional")
        print(f"   • Folder monitoring operational")
        print(f"   • Query system responsive")
        print(f"   • End-to-end workflow verified")
        
        print(f"\n📋 USAGE INSTRUCTIONS:")
        print(f"   1. Start API server: python rag_system/main.py")
        print(f"   2. Launch UI: python launch_fixed_ui.py")
        print(f"   3. Upload files through UI or use folder monitoring")
        print(f"   4. Query documents using the chat interface")
        print(f"   5. Monitor processing through the UI dashboard")
    else:
        print(f"\n⚠️ PARTIAL SUCCESS - Some components need attention")
        print(f"   Please check the failed tests above for details")

if __name__ == "__main__":
    main() 