#!/usr/bin/env python3
"""
Disable Monitoring Script
Disables all background monitoring, health checks, and schedulers that might be making API calls.
"""

import os
import sys
import json
from pathlib import Path

def disable_heartbeat_monitoring():
    """Disable heartbeat monitoring by modifying config"""
    try:
        config_path = Path("data/config/system_config.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Disable monitoring
            if 'monitoring' not in config:
                config['monitoring'] = {}
            
            config['monitoring']['heartbeat_enabled'] = False
            config['monitoring']['health_checks_enabled'] = False
            config['monitoring']['auto_start'] = False
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Disabled heartbeat monitoring in system config")
        else:
            print("⚠️  System config file not found")
    except Exception as e:
        print(f"❌ Error disabling heartbeat monitoring: {e}")

def disable_schedulers():
    """Disable all schedulers"""
    try:
        # Create a flag file to disable schedulers
        flag_file = Path("data/config/disable_schedulers.flag")
        flag_file.parent.mkdir(parents=True, exist_ok=True)
        flag_file.write_text("Schedulers disabled to prevent API calls")
        
        print("✅ Created scheduler disable flag")
    except Exception as e:
        print(f"❌ Error creating scheduler disable flag: {e}")

def create_monitoring_config():
    """Create a monitoring config that disables everything"""
    try:
        monitoring_config = {
            "enabled": False,
            "heartbeat_enabled": False,
            "health_checks_enabled": False,
            "api_monitoring_enabled": False,
            "scheduler_enabled": False,
            "auto_start_monitoring": False,
            "reason": "Disabled to prevent repeated API calls",
            "disabled_timestamp": "2025-01-27T10:00:00Z"
        }
        
        config_dir = Path("data/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_dir / "monitoring_config.json", 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        print("✅ Created monitoring disable configuration")
    except Exception as e:
        print(f"❌ Error creating monitoring config: {e}")

def show_status():
    """Show current monitoring status"""
    print("\n📊 Current Monitoring Status:")
    
    # Check system config
    config_path = Path("data/config/system_config.json")
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            monitoring = config.get('monitoring', {})
            print(f"   Heartbeat Enabled: {monitoring.get('heartbeat_enabled', 'Not set')}")
            print(f"   Health Checks Enabled: {monitoring.get('health_checks_enabled', 'Not set')}")
        except Exception as e:
            print(f"   System Config: Error reading - {e}")
    else:
        print("   System Config: Not found")
    
    # Check disable flags
    disable_flag = Path("data/config/disable_schedulers.flag")
    print(f"   Scheduler Disable Flag: {'✅ Present' if disable_flag.exists() else '❌ Not found'}")
    
    # Check monitoring config
    monitoring_config = Path("data/config/monitoring_config.json")
    if monitoring_config.exists():
        try:
            with open(monitoring_config, 'r') as f:
                config = json.load(f)
            print(f"   Monitoring Config: Enabled = {config.get('enabled', 'Unknown')}")
        except Exception as e:
            print(f"   Monitoring Config: Error reading - {e}")
    else:
        print("   Monitoring Config: Not found")

def main():
    """Main function"""
    print("🛑 RAG System Monitoring Disable Script")
    print("=" * 50)
    
    # Show current status
    show_status()
    
    print("\n🔧 Disabling monitoring components...")
    
    # Disable all monitoring
    disable_heartbeat_monitoring()
    disable_schedulers()
    create_monitoring_config()
    
    print("\n✅ Monitoring disable completed!")
    print("\n💡 To re-enable monitoring:")
    print("   1. Delete data/config/disable_schedulers.flag")
    print("   2. Set monitoring.enabled = true in system_config.json")
    print("   3. Restart the RAG system")
    
    print("\n🔍 Final status:")
    show_status()

if __name__ == "__main__":
    main() 