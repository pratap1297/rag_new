#!/usr/bin/env python3
"""
Test Logging Configuration System
"""
import json
from pathlib import Path

def test_logging_config():
    print("🧪 Testing Logging Configuration System")
    print("=" * 50)
    
    # Check if config file exists
    config_file = Path("data/config/system_config.json")
    print(f"Config file exists: {config_file.exists()}")
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            logging_config = config.get('logging', {})
            print(f"Logging config found: {bool(logging_config)}")
            
            if logging_config:
                print("\n📋 Available Components:")
                for component in logging_config.keys():
                    enabled = logging_config[component].get('enabled', False)
                    level = logging_config[component].get('level', 'INFO')
                    status = "✅" if enabled else "❌"
                    print(f"  {status} {component} (Level: {level})")
                
                # Test the logging config manager
                try:
                    import sys
                    sys.path.insert(0, 'src')
                    from core.logging_config import LoggingConfigManager
                    
                    manager = LoggingConfigManager()
                    print(f"\n🔧 Logging Config Manager initialized successfully")
                    
                    # Test some methods
                    print(f"PDF processing enabled: {manager.is_enabled('pdf_processing')}")
                    print(f"Excel processing enabled: {manager.is_enabled('excel_processing')}")
                    print(f"PDF processing level: {manager.get_log_level('pdf_processing')}")
                    print(f"Should save dumps: {manager.should_save_dumps('pdf_processing')}")
                    
                except Exception as e:
                    print(f"❌ Error testing logging config manager: {e}")
            
        except Exception as e:
            print(f"❌ Error reading config: {e}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_logging_config() 