#!/usr/bin/env python3
"""
Simple test runner for the comprehensive RAG system test suite.
This script provides an easy way to run tests with different configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(url="http://localhost:8000", api_key="test_api_key_123", verbose=False, openai_config="openai.json"):
    """Run the comprehensive test suite with specified parameters"""
    
    # Build command
    cmd = [
        sys.executable, 
        "comprehensive_test_suite.py",
        "--url", url,
        "--api-key", api_key,
        "--openai-config", openai_config
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    print(f"🚀 Running comprehensive test suite...")
    print(f"   URL: {url}")
    print(f"   API Key: {api_key[:10]}...")
    print(f"   OpenAI Config: {openai_config}")
    print(f"   Verbose: {verbose}")
    print("=" * 60)
    
    try:
        # Run the test suite
        result = subprocess.run(cmd, check=False, capture_output=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Test suite interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running test suite: {e}")
        return 1

def main():
    """Main function for the test runner"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive RAG system tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_comprehensive_tests.py                    # Run with defaults
  python run_comprehensive_tests.py --verbose          # Run with verbose output
  python run_comprehensive_tests.py --url http://localhost:9000  # Custom URL
  python run_comprehensive_tests.py --quick            # Quick test mode
        """
    )
    
    parser.add_argument(
        '--url', 
        default='http://localhost:8000',
        help='RAG system base URL (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--api-key', 
        default='test_api_key_123',
        help='API key for authentication (default: test_api_key_123)'
    )
    
    parser.add_argument(
        '--openai-config', 
        default='openai.json',
        help='OpenAI configuration file (default: openai.json)'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Run quick tests only (not implemented yet)'
    )
    
    args = parser.parse_args()
    
    # Check if comprehensive_test_suite.py exists
    if not Path("comprehensive_test_suite.py").exists():
        print("❌ Error: comprehensive_test_suite.py not found in current directory")
        print("   Please run this script from the rag-system directory")
        return 1
    
    # Run tests
    exit_code = run_tests(
        url=args.url,
        api_key=args.api_key,
        verbose=args.verbose,
        openai_config=args.openai_config
    )
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 