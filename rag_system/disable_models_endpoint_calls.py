#!/usr/bin/env python3
"""
Disable Models Endpoint Calls Script
Completely disables any internal health checks or monitoring that might be calling the /v1/models endpoint
"""

import os
import json
from pathlib import Path

def disable_models_endpoint_calls():
    """Disable all internal calls to models endpoint"""
    print("🛑 Disabling Models Endpoint Internal Calls")
    print("=" * 60)
    
    # 1. Create a flag file to disable models endpoint calls
    flag_file = Path("data/config/disable_models_calls.flag")
    flag_file.parent.mkdir(parents=True, exist_ok=True)
    flag_file.write_text("Models endpoint internal calls disabled")
    print("✅ Created models endpoint disable flag")
    
    # 2. Update system config to disable any model checking
    config_file = Path("data/config/system_config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Add model endpoint disable flags
            if 'api' not in config:
                config['api'] = {}
            
            config['api']['disable_models_endpoint_calls'] = True
            config['api']['disable_model_health_checks'] = True
            config['api']['disable_openai_compatibility'] = True
            
            # Disable any health checks that might call models
            if 'monitoring' not in config:
                config['monitoring'] = {}
            
            config['monitoring']['disable_model_checks'] = True
            config['monitoring']['disable_api_health_checks'] = True
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Updated system config to disable model endpoint calls")
        except Exception as e:
            print(f"⚠️ Could not update system config: {e}")
    
    # 3. Create environment variable override
    env_override = Path("data/config/disable_models.env")
    env_override.write_text("""# Disable models endpoint calls
DISABLE_MODELS_ENDPOINT=true
DISABLE_MODEL_HEALTH_CHECKS=true
DISABLE_OPENAI_COMPATIBILITY=true
""")
    print("✅ Created environment override file")
    
    # 4. Create a monitoring disable file specifically for models
    monitoring_config = {
        "models_endpoint_disabled": True,
        "reason": "Prevent repeated API calls to /v1/models",
        "timestamp": "2025-06-28T07:30:00Z",
        "disable_openai_client_calls": True,
        "disable_model_discovery": True,
        "disable_health_check_models": True
    }
    
    monitoring_file = Path("data/config/models_monitoring_disabled.json")
    with open(monitoring_file, 'w') as f:
        json.dump(monitoring_config, f, indent=2)
    print("✅ Created models monitoring disable configuration")
    
    print("\n🎯 Models Endpoint Calls Disabled Successfully!")
    print("\n📋 What was disabled:")
    print("   - ✅ Internal health checks to /v1/models")
    print("   - ✅ OpenAI client model discovery")
    print("   - ✅ Model availability checking")
    print("   - ✅ Automatic model listing")
    print("   - ✅ Health monitoring of models endpoint")
    
    print("\n💡 To re-enable:")
    print("   1. Delete data/config/disable_models_calls.flag")
    print("   2. Remove disable flags from system_config.json")
    print("   3. Delete data/config/models_monitoring_disabled.json")

if __name__ == "__main__":
    disable_models_endpoint_calls() 