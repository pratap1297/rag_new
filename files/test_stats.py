#!/usr/bin/env python3
"""
Test Stats Endpoint
"""
import requests
import json

try:
    print("Testing stats endpoint...")
    response = requests.get("http://localhost:8000/stats", timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print("Stats data:")
        print(json.dumps(data, indent=2))
    else:
        print("Error response:")
        try:
            error_data = response.json()
            print(json.dumps(error_data, indent=2))
        except:
            print(response.text)
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 