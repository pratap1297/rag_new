#!/usr/bin/env python3
"""
Test script to isolate dependency container log store creation issue
"""

print("🔧 Testing dependency container log store creation...")

try:
    print("1. Importing DependencyContainer...")
    from src.core.dependency_container import DependencyContainer, register_core_services
    print("   ✅ Import successful")
    
    print("2. Creating DependencyContainer...")
    container = DependencyContainer()
    print("   ✅ DependencyContainer created")
    
    print("3. Registering core services...")
    register_core_services(container)
    print("   ✅ Core services registered")
    
    print("4. Getting config manager...")
    config_manager = container.get('config_manager')
    print("   ✅ Config manager retrieved")
    
    print("5. Getting log store...")
    log_store = container.get('log_store')
    print("   ✅ Log store retrieved successfully")
    
    print("6. Testing log store functionality...")
    log_store.log_event("test", {"message": "Hello from dependency container"})
    logs = log_store.get_recent_logs("test")
    print(f"   ✅ Log store working - {len(logs)} logs retrieved")
    
    print("✅ Dependency container log store test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 