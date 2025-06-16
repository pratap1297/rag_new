#!/usr/bin/env python3
"""
Test Error Tracking Initialization
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_log_store():
    """Test LogStore creation"""
    print("🔧 Testing LogStore creation...")
    try:
        from src.core.json_store import LogStore
        print("   ✅ LogStore imported")
        
        log_store = LogStore('data/logs')
        print("   ✅ LogStore created successfully")
        return log_store
    except Exception as e:
        print(f"   ❌ LogStore failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_error_tracker():
    """Test ErrorTracker creation"""
    print("🔧 Testing ErrorTracker creation...")
    try:
        from src.core.error_handling import ErrorTracker
        print("   ✅ ErrorTracker imported")
        
        # Test without log_store first
        error_tracker = ErrorTracker()
        print("   ✅ ErrorTracker created (no log_store)")
        
        # Test with log_store
        log_store = test_log_store()
        if log_store:
            error_tracker_with_store = ErrorTracker(log_store)
            print("   ✅ ErrorTracker created (with log_store)")
        
        return error_tracker
    except Exception as e:
        print(f"   ❌ ErrorTracker failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_set_error_tracker():
    """Test set_error_tracker function"""
    print("🔧 Testing set_error_tracker...")
    try:
        from src.core.error_handling import set_error_tracker, get_error_tracker
        print("   ✅ Functions imported")
        
        error_tracker = test_error_tracker()
        if error_tracker:
            print("   🔧 Setting global error tracker...")
            set_error_tracker(error_tracker)
            print("   ✅ Global error tracker set")
            
            # Test getting it back
            retrieved_tracker = get_error_tracker()
            print("   ✅ Global error tracker retrieved")
            
            return True
    except Exception as e:
        print(f"   ❌ set_error_tracker failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🐛 ERROR TRACKING DEBUG")
    print("="*40)
    
    tests = [
        ("LogStore", test_log_store),
        ("ErrorTracker", test_error_tracker),
        ("set_error_tracker", test_set_error_tracker)
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