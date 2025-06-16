#!/usr/bin/env python3
"""
Test script to isolate log store creation issue
"""

print("🔧 Testing log store creation...")

try:
    print("1. Importing MemoryLogStore...")
    from src.core.memory_store import MemoryLogStore
    print("   ✅ Import successful")
    
    print("2. Creating MemoryLogStore instance...")
    log_store = MemoryLogStore("data/logs")
    print("   ✅ MemoryLogStore created successfully")
    
    print("3. Testing log store functionality...")
    log_store.log_event("test", {"message": "Hello World"})
    print("   ✅ Log event added successfully")
    
    print("4. Retrieving logs...")
    logs = log_store.get_recent_logs("test")
    print(f"   ✅ Retrieved {len(logs)} logs")
    
    print("✅ Log store test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 