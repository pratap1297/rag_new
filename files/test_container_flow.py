#!/usr/bin/env python3
"""
Test Dependency Container Flow
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_container_flow():
    """Test the exact dependency container flow"""
    print("🔧 Testing dependency container flow...")
    
    try:
        # Step 1: Create container
        print("   📦 Creating dependency container...")
        from src.core.dependency_container import DependencyContainer
        container = DependencyContainer()
        print("   ✅ Container created")
        
        # Step 2: Register services
        print("   📦 Registering core services...")
        from src.core.dependency_container import register_core_services
        register_core_services(container)
        print("   ✅ Services registered")
        
        # Step 3: Get config manager
        print("   📦 Getting config manager...")
        config_manager = container.get('config_manager')
        print("   ✅ Config manager retrieved")
        
        # Step 4: Get log store (this is where it might hang)
        print("   📦 Getting log store...")
        log_store = container.get('log_store')
        print("   ✅ Log store retrieved")
        
        # Step 5: Test error tracking initialization
        print("   📦 Testing error tracking...")
        from src.core.error_handling import ErrorTracker, set_error_tracker
        
        print("     🔧 Creating error tracker...")
        error_tracker = ErrorTracker(log_store)
        print("     ✅ Error tracker created")
        
        print("     🔧 Setting global error tracker...")
        set_error_tracker(error_tracker)
        print("     ✅ Global error tracker set")
        
        print("   ✅ Error tracking completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Container flow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_factories():
    """Test individual factory functions"""
    print("🔧 Testing individual factory functions...")
    
    try:
        # Create container and config manager first
        from src.core.dependency_container import DependencyContainer, create_config_manager
        container = DependencyContainer()
        
        print("   📦 Testing config manager factory...")
        config_manager = create_config_manager(container)
        container.register_instance('config_manager', config_manager)
        print("   ✅ Config manager factory works")
        
        print("   📦 Testing log store factory...")
        from src.core.dependency_container import create_log_store
        log_store = create_log_store(container)
        print("   ✅ Log store factory works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🐛 DEPENDENCY CONTAINER DEBUG")
    print("="*40)
    
    tests = [
        ("Individual Factories", test_individual_factories),
        ("Container Flow", test_container_flow)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                break
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            break
    
    print(f"\n🏁 Debug completed!")

if __name__ == "__main__":
    main() 