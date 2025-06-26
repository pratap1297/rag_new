#!/usr/bin/env python3
"""
Simple Test Runner for Metadata Fixes
Runs the comprehensive test suite and provides clear output
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the comprehensive metadata tests"""
    print("🚀 Metadata Fixes Test Runner")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("rag_system").exists():
        print("❌ Error: rag_system directory not found!")
        print("Please run this script from the project root directory.")
        return 1
    
    # Check if the test file exists
    test_file = Path("comprehensive_metadata_test.py")
    if not test_file.exists():
        print("❌ Error: comprehensive_metadata_test.py not found!")
        print("Please ensure the test file is in the current directory.")
        return 1
    
    print("✅ Found test files and directories")
    print("🔧 Running comprehensive metadata fixes test suite...")
    print()
    
    try:
        # Run the test suite
        result = subprocess.run([
            sys.executable, "comprehensive_metadata_test.py"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n🎉 All tests completed successfully!")
            return 0
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            return 1
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 