#!/usr/bin/env python3
"""
Check Azure AI Configuration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.config_manager import ConfigManager

def check_azure_config():
    """Check Azure AI configuration"""
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()

        print('🔧 Azure AI Configuration:')
        azure_config = config.azure_ai
        
        cv_endpoint = azure_config.computer_vision_endpoint
        cv_key = azure_config.computer_vision_key
        di_endpoint = azure_config.document_intelligence_endpoint
        di_key = azure_config.document_intelligence_key
        
        print(f'  Computer Vision Endpoint: {"✅ Configured" if cv_endpoint else "❌ Not configured"}')
        print(f'  Computer Vision Key: {"✅ Configured" if cv_key else "❌ Not configured"}')
        print(f'  Document Intelligence Endpoint: {"✅ Configured" if di_endpoint else "❌ Not configured"}')
        print(f'  Document Intelligence Key: {"✅ Configured" if di_key else "❌ Not configured"}')

        print(f'\n📊 Current Vector Store Configuration:')
        print(f'  Index Path: {config.database.faiss_index_path}')
        print(f'  Dimension: {config.embedding.dimension}')

        if cv_endpoint:
            print(f'\n🔧 Azure Computer Vision Details:')
            print(f'  Endpoint: {cv_endpoint[:50]}...')
            print(f'  Key Length: {len(cv_key) if cv_key else 0} chars')
            
        # Check if Azure client is working
        try:
            from integrations.azure_ai.azure_client import AzureAIClient
            azure_client = AzureAIClient(azure_config.__dict__)
            
            if azure_client.is_available():
                print(f'\n✅ Azure AI Client: Available and working')
            else:
                print(f'\n❌ Azure AI Client: Not available')
                
        except Exception as e:
            print(f'\n❌ Azure AI Client Error: {e}')
            
        return True
        
    except Exception as e:
        print(f'❌ Error checking configuration: {e}')
        return False

if __name__ == "__main__":
    print("🔍 Checking Azure AI Configuration...\n")
    check_azure_config() 