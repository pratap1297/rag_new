#!/usr/bin/env python3
"""
ServiceNow Environment Setup Helper
Helps create and configure the .env file with ServiceNow credentials.
"""

import os
import shutil
from pathlib import Path

def setup_env_file():
    """Setup .env file with ServiceNow credentials"""
    
    root_dir = Path(__file__).parent.parent.parent
    env_path = root_dir / '.env'
    template_path = root_dir / 'env_template_root.txt'
    
    print("🔧 ServiceNow Environment Setup")
    print("=" * 40)
    
    # Check if template exists
    if not template_path.exists():
        print("❌ Template file 'env_template_root.txt' not found")
        return False
    
    # Check if .env already exists
    if env_path.exists():
        print("⚠️  .env file already exists")
        overwrite = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("Setup cancelled.")
            return False
    
    print("\n📝 Please provide your ServiceNow credentials:")
    print("(Press Enter to skip and manually edit later)")
    
    # Get ServiceNow credentials
    instance = input("\nServiceNow Instance (e.g., dev12345.service-now.com): ").strip()
    username = input("ServiceNow Username: ").strip()
    password = input("ServiceNow Password: ").strip()
    
    # Copy template to .env
    try:
        shutil.copy2(template_path, env_path)
        print(f"\n✅ Copied template to {env_path}")
        
        # Update credentials if provided
        if instance or username or password:
            print("📝 Updating credentials in .env file...")
            
            # Read the file
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Replace placeholders
            if instance:
                content = content.replace('your-instance.service-now.com', instance)
                print(f"   ✓ Set SERVICENOW_INSTANCE={instance}")
            
            if username:
                content = content.replace('your_username', username)
                print(f"   ✓ Set SERVICENOW_USERNAME={username}")
            
            if password:
                content = content.replace('your_password', password)
                print(f"   ✓ Set SERVICENOW_PASSWORD=***")
            
            # Write back
            with open(env_path, 'w') as f:
                f.write(content)
        
        print(f"\n✅ .env file created successfully!")
        print(f"\n📍 Location: {env_path}")
        
        if not (instance and username and password):
            print("\n📝 Next steps:")
            print(f"1. Edit {env_path}")
            print("2. Fill in your ServiceNow credentials:")
            print("   - SERVICENOW_INSTANCE=your-instance.service-now.com")
            print("   - SERVICENOW_USERNAME=your_username")
            print("   - SERVICENOW_PASSWORD=your_password")
        
        print("\n🧪 Test your setup:")
        print("   python test_servicenow_connection.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def show_current_config():
    """Show current .env configuration"""
    root_dir = Path(__file__).parent.parent.parent
    env_path = root_dir / '.env'
    
    if not env_path.exists():
        print("❌ .env file not found")
        return
    
    print("📋 Current .env configuration:")
    print("-" * 30)
    
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        servicenow_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('SERVICENOW_') and '=' in line:
                key, value = line.split('=', 1)
                if 'PASSWORD' in key:
                    value = '***' if value and not value.startswith('your_') else value
                servicenow_lines.append(f"{key}={value}")
        
        if servicenow_lines:
            for line in servicenow_lines:
                print(f"   {line}")
        else:
            print("   No ServiceNow configuration found")
            
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")

def main():
    """Main function"""
    print("🔧 ServiceNow Environment Setup Helper")
    print("=" * 50)
    
    root_dir = Path(__file__).parent.parent.parent
    env_path = root_dir / '.env'
    
    print("\nSelect an option:")
    print("1. Create/Update .env file with ServiceNow credentials")
    print("2. Show current .env configuration")
    print("3. Test ServiceNow connection")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            setup_env_file()
        elif choice == "2":
            show_current_config()
        elif choice == "3":
            if env_path.exists():
                print("\n🧪 Running connection test...")
                os.system("python test_servicenow_connection.py")
            else:
                print("❌ .env file not found. Please create it first (option 1)")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n🛑 Setup cancelled by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 