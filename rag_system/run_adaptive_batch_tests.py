#!/usr/bin/env python3
"""
Test Runner for Adaptive Batch Sizing
Executes comprehensive tests and provides detailed reporting
"""

import sys
import os
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_unit_tests():
    """Run unit tests for adaptive batch sizing"""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    test_file = Path(__file__).parent / "tests" / "test_adaptive_batch_sizing.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Change to the tests directory and run the tests
        original_cwd = Path.cwd()
        tests_dir = test_file.parent
        
        # Run the tests with verbose output
        result = subprocess.run([
            sys.executable, "-m", "unittest", 
            "test_adaptive_batch_sizing", "-v"
        ], capture_output=True, text=True, timeout=300, cwd=tests_dir)
        
        if result.returncode == 0:
            print("✅ Unit tests passed successfully!")
            print("\nTest Output:")
            print(result.stdout)
            return True
        else:
            print("❌ Unit tests failed!")
            print("\nError Output:")
            print(result.stderr)
            print("\nTest Output:")
            print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Unit tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False

def run_example_tests():
    """Run example tests to verify functionality"""
    print("\n" + "=" * 60)
    print("RUNNING EXAMPLE TESTS")
    print("=" * 60)
    
    example_file = Path(__file__).parent / "examples" / "adaptive_batch_sizing_example.py"
    
    if not example_file.exists():
        print(f"❌ Example file not found: {example_file}")
        return False
    
    try:
        # Run the example with timeout
        result = subprocess.run([
            sys.executable, str(example_file)
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Example tests passed successfully!")
            print("\nExample Output:")
            print(result.stdout)
            return True
        else:
            print("❌ Example tests failed!")
            print("\nError Output:")
            print(result.stderr)
            print("\nExample Output:")
            print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Example tests timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running example tests: {e}")
        return False

def run_integration_tests():
    """Run integration tests with real embedding models"""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        # Test with sentence-transformers (local model)
        print("Testing with sentence-transformers...")
        
        test_script = """
import sys
import os
from pathlib import Path

# Get the current directory (rag_system)
current_dir = Path.cwd()
src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))

from ingestion.embedder import Embedder
import time

# Test basic functionality
embedder = Embedder(provider="sentence-transformers", batch_size=32)
print(f"✅ Embedder initialized: {embedder.provider}")

# Test single text
text = "This is a test text for embedding generation."
embedding = embedder.embed_text(text)
print(f"✅ Single text embedding: {len(embedding)} dimensions")

# Test multiple texts with adaptive batching
texts = [f"Text {i} for batch testing" for i in range(10)]
text_lengths = [len(text) for text in texts]
optimal_batch_size = embedder.calculate_optimal_batch_size(text_lengths)
print(f"✅ Optimal batch size calculated: {optimal_batch_size}")

start_time = time.time()
embeddings = embedder.embed_texts(texts)
elapsed_time = time.time() - start_time
print(f"✅ Batch embeddings generated: {len(embeddings)} texts in {elapsed_time:.2f}s")

# Test similarity
similarity = embedder.similarity("Hello world", "Hello there")
print(f"✅ Similarity calculation: {similarity:.4f}")

print("✅ All integration tests passed!")
"""
        
        result = subprocess.run([
            sys.executable, "-c", test_script
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Integration tests passed successfully!")
            print("\nIntegration Test Output:")
            print(result.stdout)
            return True
        else:
            print("❌ Integration tests failed!")
            print("\nError Output:")
            print(result.stderr)
            print("\nIntegration Test Output:")
            print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Integration tests timed out after 1 minute")
        return False
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False

def run_performance_tests():
    """Run performance tests to measure efficiency"""
    print("\n" + "=" * 60)
    print("RUNNING PERFORMANCE TESTS")
    print("=" * 60)
    
    try:
        performance_script = """
import sys
import time
import psutil
from pathlib import Path

# Get the current directory (rag_system)
current_dir = Path.cwd()
src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))

from ingestion.embedder import Embedder

# Initialize embedder
embedder = Embedder(provider="sentence-transformers", batch_size=32)

# Create test data
short_texts = ["Short text"] * 50
medium_texts = ["Medium length text with more content"] * 50
long_texts = ["Very long text " * 20] * 50

# Test memory usage and performance
def test_performance(texts, name):
    print(f"\\nTesting {name}...")
    
    # Get initial memory
    initial_memory = psutil.virtual_memory().available / 1024 / 1024
    
    # Calculate optimal batch size
    text_lengths = [len(text) for text in texts]
    optimal_batch_size = embedder.calculate_optimal_batch_size(text_lengths)
    print(f"  Optimal batch size: {optimal_batch_size}")
    
    # Time the processing
    start_time = time.time()
    embeddings = embedder.embed_texts(texts)
    elapsed_time = time.time() - start_time
    
    # Get final memory
    final_memory = psutil.virtual_memory().available / 1024 / 1024
    memory_used = initial_memory - final_memory
    
    print(f"  Processed {len(embeddings)} texts in {elapsed_time:.2f}s")
    print(f"  Memory used: {memory_used:.1f}MB")
    print(f"  Average time per text: {elapsed_time/len(texts)*1000:.1f}ms")
    
    return elapsed_time, memory_used

# Run performance tests
test_performance(short_texts, "Short texts")
test_performance(medium_texts, "Medium texts")
test_performance(long_texts, "Long texts")

print("\\n✅ Performance tests completed!")
"""
        
        result = subprocess.run([
            sys.executable, "-c", performance_script
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Performance tests completed successfully!")
            print("\nPerformance Test Output:")
            print(result.stdout)
            return True
        else:
            print("❌ Performance tests failed!")
            print("\nError Output:")
            print(result.stderr)
            print("\nPerformance Test Output:")
            print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Performance tests timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")
        return False

def run_memory_stress_tests():
    """Run memory stress tests to verify robustness"""
    print("\n" + "=" * 60)
    print("RUNNING MEMORY STRESS TESTS")
    print("=" * 60)
    
    try:
        stress_script = """
import sys
import psutil
from pathlib import Path

# Get the current directory (rag_system)
current_dir = Path.cwd()
src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))

from ingestion.embedder import Embedder

# Initialize embedder
embedder = Embedder(provider="sentence-transformers", batch_size=64)

# Create large dataset
large_texts = [f"Text {i} with some content for stress testing" for i in range(500)]

print(f"Testing with {len(large_texts)} texts...")

# Get initial memory
initial_memory = psutil.virtual_memory().available / 1024 / 1024
print(f"Initial available memory: {initial_memory:.1f}MB")

# Process in batches to test memory management
batch_size = 100
total_embeddings = 0

for i in range(0, len(large_texts), batch_size):
    batch = large_texts[i:i + batch_size]
    
    # Calculate optimal batch size for this batch
    text_lengths = [len(text) for text in batch]
    optimal_batch_size = embedder.calculate_optimal_batch_size(text_lengths)
    
    # Process batch
    embeddings = embedder.embed_texts(batch)
    total_embeddings += len(embeddings)
    
    # Check memory usage
    current_memory = psutil.virtual_memory().available / 1024 / 1024
    print(f"  Batch {i//batch_size + 1}: {len(embeddings)} texts, "
          f"optimal_batch_size: {optimal_batch_size}, "
          f"memory: {current_memory:.1f}MB")

print(f"\\n✅ Processed {total_embeddings} texts successfully!")
print(f"Final memory: {psutil.virtual_memory().available / 1024 / 1024:.1f}MB")
"""
        
        result = subprocess.run([
            sys.executable, "-c", stress_script
        ], capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            print("✅ Memory stress tests completed successfully!")
            print("\nStress Test Output:")
            print(result.stdout)
            return True
        else:
            print("❌ Memory stress tests failed!")
            print("\nError Output:")
            print(result.stderr)
            print("\nStress Test Output:")
            print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Memory stress tests timed out after 3 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running memory stress tests: {e}")
        return False

def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "=" * 60)
    print("TEST REPORT")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Test Categories: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    # Generate JSON report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "success_rate": (passed_tests/total_tests)*100,
        "results": results
    }
    
    report_file = Path(__file__).parent / "test_reports" / f"adaptive_batch_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return passed_tests == total_tests

def main():
    """Main test runner"""
    print("🧪 ADAPTIVE BATCH SIZING COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    
    # Run all test categories
    test_results = {
        "Unit Tests": run_unit_tests(),
        "Example Tests": run_example_tests(),
        "Integration Tests": run_integration_tests(),
        "Performance Tests": run_performance_tests(),
        "Memory Stress Tests": run_memory_stress_tests()
    }
    
    # Generate report
    all_passed = generate_test_report(test_results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Adaptive batch sizing is working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED. Please review the results above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 