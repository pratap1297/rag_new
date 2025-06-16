#!/usr/bin/env python3
"""
Environment Check Script
"""
import os
from pathlib import Path

def check_environment():
    print("🔍 Environment Check")
    print("=" * 30)
    
    # Check .env file
    env_file = Path(".env")
    print(f".env file exists: {env_file.exists()}")
    
    if env_file.exists():
        print(f".env file size: {env_file.stat().st_size} bytes")
    
    # Check API keys
    groq_key = os.getenv("GROQ_API_KEY")
    cohere_key = os.getenv("COHERE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"GROQ_API_KEY: {'✅ Set' if groq_key else '❌ Not set'}")
    print(f"COHERE_API_KEY: {'✅ Set' if cohere_key else '❌ Not set'}")
    print(f"OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
    
    if groq_key:
        print(f"GROQ key length: {len(groq_key)} characters")
    if cohere_key:
        print(f"COHERE key length: {len(cohere_key)} characters")
    
    # Check if python-dotenv is available
    try:
        import dotenv
        print("✅ python-dotenv available")
        
        # Try loading .env
        dotenv.load_dotenv()
        print("✅ .env file loaded")
        
        # Check again after loading
        groq_key_after = os.getenv("GROQ_API_KEY")
        cohere_key_after = os.getenv("COHERE_API_KEY")
        
        print("\nAfter loading .env:")
        print(f"GROQ_API_KEY: {'✅ Set' if groq_key_after else '❌ Not set'}")
        print(f"COHERE_API_KEY: {'✅ Set' if cohere_key_after else '❌ Not set'}")
        
    except ImportError:
        print("❌ python-dotenv not available")
        print("Install with: pip install python-dotenv")

if __name__ == "__main__":
    check_environment() 