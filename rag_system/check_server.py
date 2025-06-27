#!/usr/bin/env python3
import time
import requests

print('Checking if server is running...')
try:
    response = requests.get('http://127.0.0.1:8000/health', timeout=5)
    if response.status_code == 200:
        print('✅ Server is running!')
        
        # Test conversation endpoint
        print('Testing conversation endpoint...')
        conv_response = requests.post('http://127.0.0.1:8000/api/conversation/start', json={})
        print(f'Conversation endpoint status: {conv_response.status_code}')
        
        if conv_response.status_code == 200:
            print('✅ Conversation system is working!')
            data = conv_response.json()
            print(f'Thread ID: {data.get("thread_id")}')
        else:
            print(f'❌ Conversation error: {conv_response.text}')
    else:
        print(f'❌ Server health check failed: {response.status_code}')
        
except requests.exceptions.RequestException as e:
    print(f'❌ Server is not running: {e}') 