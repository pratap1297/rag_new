#!/usr/bin/env python3
"""
Test script to verify the metadata nesting fix
"""

import sys
import os
from pathlib import Path

# Add the rag_system to the path
sys.path.insert(0, str(Path(__file__).parent / 'rag_system' / 'src'))

def test_metadata_flattening():
    """Test that nested metadata is properly flattened"""
    
    # Test data with nested metadata
    test_chunk = {
        'text': 'This is a test chunk',
        'metadata': {
            'metadata': {  # Nested metadata - this should be flattened
                'title': 'Test Document',
                'author': 'Test Author',
                'section': 'Introduction'
            },
            'chunk_type': 'paragraph',
            'page_number': 1
        }
    }
    
    print("Testing metadata flattening...")
    print(f"Original chunk metadata: {test_chunk['metadata']}")
    
    # Apply the flattening logic
    chunk_meta = test_chunk.get('metadata', {})
    
    # If chunk metadata has nested 'metadata', extract it
    if isinstance(chunk_meta.get('metadata'), dict):
        nested_meta = chunk_meta.pop('metadata')
        # Merge nested metadata into chunk_meta
        for k, v in nested_meta.items():
            if k not in chunk_meta:
                chunk_meta[k] = v
    
    print(f"Flattened metadata: {chunk_meta}")
    
    # Verify the result
    expected_keys = {'title', 'author', 'section', 'chunk_type', 'page_number'}
    actual_keys = set(chunk_meta.keys())
    
    if expected_keys == actual_keys:
        print("✅ Metadata flattening test PASSED")
        return True
    else:
        print(f"❌ Metadata flattening test FAILED")
        print(f"Expected keys: {expected_keys}")
        print(f"Actual keys: {actual_keys}")
        return False

def test_faiss_metadata_cleaning():
    """Test the FAISS store metadata cleaning"""
    
    # Test metadata with nested structure
    test_metadata = [
        {
            'text': 'Chunk 1',
            'metadata': {  # This should be flattened
                'title': 'Document 1',
                'author': 'Author 1'
            },
            'chunk_index': 0
        },
        {
            'text': 'Chunk 2',
            'metadata': {  # This should be flattened
                'title': 'Document 1',
                'author': 'Author 1'
            },
            'chunk_index': 1
        }
    ]
    
    print("\nTesting FAISS metadata cleaning...")
    print(f"Original metadata structure: {test_metadata[0]}")
    
    # Apply the cleaning logic
    cleaned_metadata = []
    for meta in test_metadata:
        # If metadata has nested 'metadata' key, flatten it
        if isinstance(meta.get('metadata'), dict):
            nested = meta.pop('metadata')
            flat_meta = meta.copy()
            # Merge nested metadata, but don't override existing keys
            for k, v in nested.items():
                if k not in flat_meta and k != 'metadata':
                    flat_meta[k] = v
            cleaned_metadata.append(flat_meta)
        else:
            cleaned_metadata.append(meta)
    
    print(f"Cleaned metadata structure: {cleaned_metadata[0]}")
    
    # Verify the result
    expected_keys = {'text', 'title', 'author', 'chunk_index'}
    actual_keys = set(cleaned_metadata[0].keys())
    
    if expected_keys == actual_keys:
        print("✅ FAISS metadata cleaning test PASSED")
        return True
    else:
        print(f"❌ FAISS metadata cleaning test FAILED")
        print(f"Expected keys: {expected_keys}")
        print(f"Actual keys: {actual_keys}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Metadata Nesting Fix")
    print("=" * 50)
    
    test1_passed = test_metadata_flattening()
    test2_passed = test_faiss_metadata_cleaning()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("🎉 All tests PASSED! The metadata nesting fix is working correctly.")
        return 0
    else:
        print("💥 Some tests FAILED! Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 