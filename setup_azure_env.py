#!/usr/bin/env python3
"""
Setup Azure Environment Variables
Creates .env file for Azure Vision API configuration
"""
import os
import shutil
from pathlib import Path

def setup_azure_env():
    """Set up Azure environment variables"""
    print("🔧 Azure Vision API Environment Setup")
    print("=" * 50)
    
    # Check if template exists
    template_file = Path("azure_config_template.env")
    env_file = Path(".env")
    
    if not template_file.exists():
        print(f"❌ Template file not found: {template_file}")
        print("Please make sure azure_config_template.env exists")
        return
    
    # Copy template to .env if it doesn't exist
    if not env_file.exists():
        shutil.copy(template_file, env_file)
        print(f"✅ Created {env_file} from template")
    else:
        print(f"📝 {env_file} already exists")
        overwrite = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if overwrite in ['y', 'yes']:
            shutil.copy(template_file, env_file)
            print(f"✅ Overwritten {env_file} with template")
        else:
            print("📝 Keeping existing .env file")
    
    print()
    print("📋 Next Steps:")
    print("1. Edit the .env file with your actual Azure credentials")
    print("2. Get your credentials from Azure Portal:")
    print("   - Go to https://portal.azure.com")
    print("   - Create a 'Computer Vision' resource")
    print("   - Go to 'Keys and Endpoint'")
    print("   - Copy the endpoint and key")
    print()
    print("3. Replace these placeholders in .env:")
    print("   AZURE_COMPUTER_VISION_ENDPOINT=https://your-actual-endpoint.com/")
    print("   AZURE_COMPUTER_VISION_KEY=your-actual-api-key")
    print()
    print("4. Test your configuration:")
    print("   python test_azure_pdf_extraction.py")

def check_env_vars():
    """Check if environment variables are set"""
    print("\n🔍 Checking Environment Variables...")
    
    required_vars = [
        'AZURE_COMPUTER_VISION_ENDPOINT',
        'AZURE_COMPUTER_VISION_KEY'
    ]
    
    optional_vars = [
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT',
        'AZURE_DOCUMENT_INTELLIGENCE_KEY'
    ]
    
    all_good = True
    
    print("\n📋 Required Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value and not value.startswith('your-'):
            print(f"   ✅ {var}: {value[:30]}...")
        else:
            print(f"   ❌ {var}: Not set or using placeholder")
            all_good = False
    
    print("\n📋 Optional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value and not value.startswith('your-'):
            print(f"   ✅ {var}: {value[:30]}...")
        else:
            print(f"   ⚠️  {var}: Not set or using placeholder")
    
    if all_good:
        print("\n🎉 All required Azure credentials are configured!")
        print("Your PDF files will now be processed with Azure Vision API")
    else:
        print("\n⚠️  Please configure the missing credentials in your .env file")
    
    return all_good

def main():
    """Main function"""
    print("Azure Vision API Environment Setup")
    print()
    
    # Load environment variables from .env if it exists
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Loaded variables from .env file")
        except ImportError:
            print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
            print("📝 You can still edit .env manually")
    
    choice = input("Choose an option:\n1. Create/update .env file\n2. Check current environment\n3. Both\n\nEnter choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        setup_azure_env()
    
    if choice in ['2', '3']:
        check_env_vars()

if __name__ == "__main__":
    main() 