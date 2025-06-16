#!/usr/bin/env python3
"""
Simple test to verify RAG system is running
"""
import requests
import time

def test_endpoint(url, name):
    """Test a specific endpoint"""
    try:
        print(f"🔍 Testing {name}: {url}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ {name}: SUCCESS")
            try:
                data = response.json()
                print(f"   Response: {data}")
            except:
                print(f"   Response length: {len(response.text)} characters")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print(f"❌ {name}: Connection timeout")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ {name}: Connection error - {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {name}: Request timeout")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def test_system():
    """Test if the RAG system is running"""
    print("🧪 Simple RAG System Test")
    print("=" * 40)
    
    # Try different addresses
    addresses = [
        "http://127.0.0.1:8000",
        "http://localhost:8000", 
        "http://0.0.0.0:8000"
    ]
    
    success = False
    working_address = None
    
    for address in addresses:
        health_url = f"{address}/health"
        if test_endpoint(health_url, f"Health Check ({address})"):
            success = True
            working_address = address
            break
        print()
    
    if success:
        print(f"\n🎉 RAG System is running successfully!")
        print(f"🌐 Server: {working_address}")
        print(f"📚 API Docs: {working_address}/docs")
        print(f"🔧 Health: {working_address}/health")
        
        # Test additional endpoints
        print(f"\n🔍 Testing additional endpoints...")
        test_endpoint(f"{working_address}/docs", "API Documentation")
        test_endpoint(f"{working_address}/openapi.json", "OpenAPI Schema")
        
        return True
    else:
        print("\n❌ Could not connect to RAG system on any address")
        print("💡 Make sure the system is running with: python start.py")
        return False

if __name__ == "__main__":
    success = test_system()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!") 