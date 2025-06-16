#!/usr/bin/env python3
"""
Switch RAG System to Use Cohere Embeddings
"""
import os
import json
from pathlib import Path

def update_config_file():
    """Update the configuration file to use Cohere embeddings"""
    config_path = Path("data/config/system_config.json")
    
    # Create config directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new one
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Update embedding configuration
    if 'embedding' not in config:
        config['embedding'] = {}
    
    config['embedding'].update({
        "provider": "cohere",
        "model_name": "embed-english-v3.0",
        "dimension": 1024,
        "batch_size": 96,
        "device": "cpu"
    })
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Updated configuration file: {config_path}")
    print("📋 Cohere embedding settings:")
    print(f"   Provider: {config['embedding']['provider']}")
    print(f"   Model: {config['embedding']['model_name']}")
    print(f"   Dimension: {config['embedding']['dimension']}")

def set_environment_variables():
    """Show how to set environment variables"""
    print("\n🔧 Environment Variable Setup:")
    print("To use Cohere embeddings, set your API key:")
    print()
    print("Windows (PowerShell):")
    print("   $env:COHERE_API_KEY='your_api_key_here'")
    print()
    print("Windows (Command Prompt):")
    print("   set COHERE_API_KEY=your_api_key_here")
    print()
    print("Linux/Mac:")
    print("   export COHERE_API_KEY=your_api_key_here")
    print()
    
    # Check if already set
    if os.getenv('COHERE_API_KEY'):
        print("✅ COHERE_API_KEY is already set")
    else:
        print("❌ COHERE_API_KEY is not set")

def create_env_file():
    """Create a .env file template"""
    env_content = """# RAG System Environment Variables

# Cohere API Key (required for Cohere embeddings)
COHERE_API_KEY=your_cohere_api_key_here

# Optional: Override embedding provider
RAG_EMBEDDING_PROVIDER=cohere
RAG_EMBEDDING_MODEL=embed-english-v3.0

# Optional: LLM settings
RAG_LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Optional: System settings
RAG_ENVIRONMENT=development
RAG_DEBUG=true
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Created .env template file: {env_path}")
        print("📝 Please edit .env and add your actual API keys")
    else:
        print(f"ℹ️ .env file already exists: {env_path}")

def main():
    """Switch to Cohere embeddings"""
    print("🔄 Switching RAG System to Cohere Embeddings")
    print("=" * 50)
    
    # Update config file
    update_config_file()
    
    # Show environment setup
    set_environment_variables()
    
    # Create .env template
    print("\n" + "=" * 50)
    create_env_file()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Set your COHERE_API_KEY environment variable")
    print("2. Restart the RAG system server")
    print("3. Run: python test_cohere_embedding.py")
    print("\n✨ The system is now configured to use Cohere embeddings!")

if __name__ == "__main__":
    main() 