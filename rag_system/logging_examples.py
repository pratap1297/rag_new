#!/usr/bin/env python3
"""
Logging Configuration Examples
Practical examples of managing logging configuration
"""
import json
from pathlib import Path

def show_current_config():
    """Show current logging configuration"""
    print("🔍 Current Logging Configuration")
    print("=" * 50)
    
    config_file = Path("data/config/system_config.json")
    if not config_file.exists():
        print("❌ Config file not found")
        return
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    logging_config = config.get('logging', {})
    
    for component, settings in logging_config.items():
        if isinstance(settings, dict):
            print(f"\n📋 {component.upper()}:")
            print(f"  ├─ Enabled: {settings.get('enabled', False)}")
            print(f"  ├─ Level: {settings.get('level', 'INFO')}")
            
            # Show feature-specific settings
            features = [k for k in settings.keys() if k.startswith('log_')]
            if features:
                print(f"  ├─ Features:")
                for feature in features:
                    status = "✅" if settings[feature] else "❌"
                    print(f"  │  ├─ {feature}: {status}")
            
            # Show other settings
            other_settings = {k: v for k, v in settings.items() 
                            if not k.startswith('log_') and k not in ['enabled', 'level']}
            if other_settings:
                print(f"  └─ Other Settings:")
                for key, value in other_settings.items():
                    print(f"     └─ {key}: {value}")

def disable_verbose_logging():
    """Disable verbose logging for production"""
    print("🔧 Disabling Verbose Logging for Production")
    print("=" * 50)
    
    config_file = Path("data/config/system_config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Disable detailed logging features
    changes = [
        ('pdf_processing', 'log_ocr_results', False),
        ('pdf_processing', 'log_page_details', False),
        ('excel_processing', 'log_cell_processing', False),
        ('azure_ai', 'log_api_responses', False),
        ('extraction_debug', 'save_dumps', False)
    ]
    
    for component, feature, value in changes:
        if component in config.get('logging', {}):
            config['logging'][component][feature] = value
            print(f"✅ Set {component}.{feature} = {value}")
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Verbose logging disabled for production")

def enable_debug_mode():
    """Enable comprehensive debug logging"""
    print("🐛 Enabling Debug Mode")
    print("=" * 50)
    
    config_file = Path("data/config/system_config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Enable all logging features and set to DEBUG level
    components = ['extraction_debug', 'pdf_processing', 'excel_processing', 'ingestion_engine', 'azure_ai']
    
    for component in components:
        if component in config.get('logging', {}):
            # Set to DEBUG level
            config['logging'][component]['level'] = 'DEBUG'
            config['logging'][component]['enabled'] = True
            
            # Enable all log_ features
            for key in config['logging'][component]:
                if key.startswith('log_'):
                    config['logging'][component][key] = True
            
            # Enable dump saving
            if 'save_dumps' in config['logging'][component]:
                config['logging'][component]['save_dumps'] = True
            if 'save_extraction_dumps' in config['logging'][component]:
                config['logging'][component]['save_extraction_dumps'] = True
            
            print(f"✅ Enabled debug mode for {component}")
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Debug mode enabled for all components")

def configure_for_azure_debugging():
    """Configure logging specifically for Azure AI debugging"""
    print("☁️ Configuring for Azure AI Debugging")
    print("=" * 50)
    
    config_file = Path("data/config/system_config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Azure-specific configuration
    azure_config = {
        'enabled': True,
        'level': 'DEBUG',
        'log_api_requests': True,
        'log_api_responses': True,  # Enable for debugging
        'log_service_health': True,
        'log_rate_limiting': True,
        'mask_sensitive_data': False  # Disable for debugging (be careful!)
    }
    
    pdf_config = {
        'enabled': True,
        'level': 'DEBUG',
        'log_azure_api_calls': True,
        'log_ocr_results': True,
        'log_image_processing': True,
        'save_extraction_dumps': True
    }
    
    config['logging']['azure_ai'].update(azure_config)
    config['logging']['pdf_processing'].update(pdf_config)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Azure AI debugging configuration applied")
    print("⚠️  Warning: Sensitive data masking is disabled - use only for debugging!")

def minimal_logging():
    """Configure minimal logging for performance"""
    print("⚡ Configuring Minimal Logging for Performance")
    print("=" * 50)
    
    config_file = Path("data/config/system_config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Minimal configuration - only errors and critical info
    for component in config.get('logging', {}):
        if isinstance(config['logging'][component], dict):
            config['logging'][component]['level'] = 'WARNING'
            
            # Disable most features
            for key in config['logging'][component]:
                if key.startswith('log_'):
                    config['logging'][component][key] = False
                elif key in ['save_dumps', 'save_extraction_dumps']:
                    config['logging'][component][key] = False
            
            print(f"✅ Minimized logging for {component}")
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Minimal logging configuration applied")

def main():
    """Main function with examples"""
    print("🔧 Logging Configuration Examples")
    print("=" * 40)
    print("1. show - Show current configuration")
    print("2. debug - Enable full debug mode")
    print("3. production - Disable verbose logging")
    print("4. azure - Configure for Azure debugging")
    print("5. minimal - Minimal logging for performance")
    print()
    
    choice = input("Enter choice (1-5) or 'show' to see current config: ").strip()
    
    if choice == '1' or choice.lower() == 'show':
        show_current_config()
    elif choice == '2' or choice.lower() == 'debug':
        enable_debug_mode()
    elif choice == '3' or choice.lower() == 'production':
        disable_verbose_logging()
    elif choice == '4' or choice.lower() == 'azure':
        configure_for_azure_debugging()
    elif choice == '5' or choice.lower() == 'minimal':
        minimal_logging()
    else:
        print("❌ Invalid choice")
        show_current_config()

if __name__ == "__main__":
    main() 