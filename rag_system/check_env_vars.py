#!/usr/bin/env python3
"""
Check environment variables for Azure Vision API
"""

import os
from dotenv import load_dotenv

def check_env_vars():
    """Check environment variables"""
    print("🔍 Checking environment variables...")
    
    # Load .env file
    load_dotenv()
    
    print("\n📋 Environment variables from .env file:")
    azure_vars = [
        'AZURE_COMPUTER_VISION_ENDPOINT',
        'AZURE_COMPUTER_VISION_KEY', 
        'AZURE_CV_ENDPOINT',
        'AZURE_CV_KEY',
        'AZURE_API_KEY',
        'AZURE_CHAT_ENDPOINT',
        'AZURE_EMBEDDINGS_ENDPOINT'
    ]
    
    for var in azure_vars:
        value = os.getenv(var, "NOT SET")
        if value != "NOT SET":
            # Mask sensitive data
            if 'KEY' in var or 'key' in var:
                masked = value[:8] + '*' * (len(value) - 12) + value[-4:] if len(value) > 12 else '*' * len(value)
                print(f"  {var}: {masked}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: ❌ NOT SET")

if __name__ == "__main__":
    check_env_vars() 