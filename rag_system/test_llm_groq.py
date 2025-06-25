#!/usr/bin/env python3
"""Test Groq LLM Switch"""
import os
import sys
from pathlib import Path

# Add rag_system/src to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

print(f"🔍 Current directory: {current_dir}")
print(f"🔍 Source directory: {src_dir}")
print(f"🔍 Source directory exists: {src_dir.exists()}")

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = current_dir / ".env"
    print(f"🔍 Looking for .env file: {env_file}")
    print(f"🔍 .env file exists: {env_file.exists()}")
    
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("✅ .env file loaded successfully")
            return True
        except ImportError:
            print("⚠️  python-dotenv not installed, trying manual parsing...")
            # Manual parsing as fallback
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            print("✅ .env file parsed manually")
            return True
    else:
        print("❌ .env file not found")
        return False

# Load environment variables
load_env_file()

# Get Groq API key from environment
groq_api_key = os.getenv('GROQ_API_KEY')
if not groq_api_key:
    print("⚠️  GROQ_API_KEY not found in environment, checking if it's commented out...")
    # Check if it's commented in .env file
    env_file = current_dir / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if '# GROQ_API_KEY=' in content:
                print("💡 Found commented GROQ_API_KEY in .env file")
                print("   You need to uncomment it and add your real API key")

def check_groq_api_key():
    """Check if Groq API key looks valid and provide guidance"""
    print("\n🔑 Checking Groq API Key")
    print("=" * 50)
    
    if not groq_api_key:
        print("❌ No Groq API key found in environment")
        print_groq_setup_instructions()
        return False
    
    if groq_api_key == 'your_groq_api_key_here':
        print("❌ Placeholder API key detected")
        print_groq_setup_instructions()
        return False
    
    if not groq_api_key.startswith('gsk_'):
        print("⚠️  API key doesn't start with 'gsk_' - might be invalid")
        print_groq_setup_instructions()
        return False
    
    if len(groq_api_key) < 50:
        print("⚠️  API key seems too short - might be invalid")
        print_groq_setup_instructions()
        return False
    
    print(f"✅ API key format looks valid: {groq_api_key[:10]}...{groq_api_key[-10:]}")
    print(f"📍 Source: Environment variable GROQ_API_KEY")
    return True

def print_groq_setup_instructions():
    """Print instructions for setting up Groq API key"""
    print("\n📋 How to Set Up Groq API Key:")
    print("1. Go to https://console.groq.com")
    print("2. Sign up for a free account")
    print("3. Navigate to API Keys section")
    print("4. Create a new API key")
    print("5. Copy the key (starts with 'gsk_')")
    print("6. Edit rag_system/.env file:")
    print("   - Uncomment the line: # GROQ_API_KEY=...")
    print("   - Replace with: GROQ_API_KEY=your_actual_key_here")
    print("\n💡 Groq offers free tier with generous limits!")
    print("💡 Example .env entry: GROQ_API_KEY=gsk_1234567890abcdef...")

def test_groq_switch():
    print("🧪 Testing Groq LLM Switch")
    print("=" * 50)
    
    try:
        print("📦 Importing LLMClient...")
        # Try multiple import paths
        try:
            from retrieval.llm_client import LLMClient
            print("✅ Import successful: retrieval.llm_client")
        except ImportError:
            try:
                from src.retrieval.llm_client import LLMClient
                print("✅ Import successful: src.retrieval.llm_client")
            except ImportError:
                # Direct path import
                llm_client_path = src_dir / "retrieval" / "llm_client.py"
                print(f"🔍 Looking for: {llm_client_path}")
                print(f"🔍 File exists: {llm_client_path.exists()}")
                
                if llm_client_path.exists():
                    spec = __import__('importlib.util').util.spec_from_file_location("llm_client", llm_client_path)
                    llm_module = __import__('importlib.util').util.module_from_spec(spec)
                    spec.loader.exec_module(llm_module)
                    LLMClient = llm_module.LLMClient
                    print("✅ Import successful: direct file import")
                else:
                    raise ImportError("Could not find LLMClient module")
        
        # Check API key before proceeding
        if not check_groq_api_key():
            return False
        
        # Test Groq client
        print("🤖 Creating Groq LLM Client...")
        client = LLMClient(
            provider="groq",
            model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
            api_key=groq_api_key,
            timeout=30
        )
        print("✅ Groq client created successfully")
        
        # Test generation
        print("🚀 Testing text generation...")
        test_prompt = "Say hello in one word"
        response = client.generate(test_prompt, max_tokens=10)
        print(f"✅ Groq LLAMA works!")
        print(f"📝 Prompt: {test_prompt}")
        print(f"🎯 Response: {response}")
        
        # Test with longer prompt
        print("\n🚀 Testing with longer prompt...")
        longer_prompt = "Explain what artificial intelligence is in one sentence."
        longer_response = client.generate(longer_prompt, max_tokens=50)
        print(f"📝 Prompt: {longer_prompt}")
        print(f"🎯 Response: {longer_response}")
        
        print("\n🎉 All Groq tests passed!")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ Groq test failed: {e}")
        
        # Check for specific error types
        if "invalid_api_key" in error_str.lower() or "401" in error_str:
            print("\n🔑 API Key Issue Detected!")
            print_groq_setup_instructions()
        elif "timeout" in error_str.lower():
            print("\n⏰ Timeout Issue - Check your internet connection")
        elif "quota" in error_str.lower():
            print("\n💳 Quota Issue - Check your Groq account limits")
        
        import traceback
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return False

def test_groq_dependencies():
    """Test if Groq package is installed"""
    print("\n🔍 Testing Groq Dependencies")
    print("=" * 50)
    
    try:
        import groq
        print("✅ Groq package is installed")
        print(f"📦 Groq version: {groq.__version__ if hasattr(groq, '__version__') else 'Unknown'}")
        return True
    except ImportError:
        print("❌ Groq package not installed")
        print("💡 Install with: pip install groq")
        return False

def main():
    """Run all tests"""
    print("🚀 Groq LLM Test Suite")
    print("=" * 60)
    
    # Test dependencies first
    deps_ok = test_groq_dependencies()
    if not deps_ok:
        print("\n❌ Dependencies missing. Install groq package first.")
        return False
    
    # Test Groq switch
    switch_ok = test_groq_switch()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if switch_ok:
        print("🎉 SUCCESS! Groq LLM is working correctly")
        print("\n💡 Next steps to switch your system to Groq:")
        print("1. Update .env file: RAG_LLM_PROVIDER=groq")
        print("2. Update system_config.json: provider: groq")
        print("3. Restart your RAG system")
        print("4. Enjoy fast responses instead of 300s timeouts!")
    else:
        print("❌ FAILED! Check the errors above")
        print("\n💡 Troubleshooting:")
        print("1. Get valid Groq API key from https://console.groq.com")
        print("2. Add it to .env file: GROQ_API_KEY=your_key")
        print("3. Check internet connection")
        print("4. Ensure groq package is installed")
    
    return switch_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)