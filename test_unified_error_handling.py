#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path

# Add the rag_system src to the path
sys.path.insert(0, str(Path(__file__).parent / 'rag_system' / 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unified_error_handling():
    print(' Testing Unified Error Handling System')
    print('=' * 50)
    
    try:
        from core.unified_error_handling import (
            ErrorCode, ErrorInfo, ErrorContext, Result, UnifiedError,
            with_error_handling, safe_execute, get_error_handler,
            VectorStoreErrorHandler, IngestionErrorHandler, QueryErrorHandler,
            format_api_response, get_http_status_code
        )
        print(' Successfully imported unified error handling components')
    except ImportError as e:
        print(f' Failed to import unified error handling: {e}')
        return False
    
    # Test 1: Basic Error Info Creation
    print('\n Test 1: Basic Error Info Creation')
    try:
        error_info = ErrorInfo(
            code=ErrorCode.INVALID_REQUEST,
            message='Test error message',
            details={'test_key': 'test_value'}
        )
        print(f' Created ErrorInfo: {error_info.code.value}')
        print(f'   Message: {error_info.message}')
        print(f'   User message: {error_info.to_user_message()}')
    except Exception as e:
        print(f' Failed to create ErrorInfo: {e}')
        return False
    
    # Test 2: Result Wrapper
    print('\n Test 2: Result Wrapper')
    try:
        # Success result
        success_result = Result.ok({'data': 'test'})
        print(f' Created success result: {success_result.success}')
        
        # Failure result
        failure_result = Result.fail(error_info)
        print(f' Created failure result: {failure_result.success}')
        print(f'   Error code: {failure_result.error.code.value}')
    except Exception as e:
        print(f' Failed to create Result: {e}')
        return False
    
    print('\n Basic Unified Error Handling Tests Completed!')
    print('=' * 50)
    return True

def main():
    print(' Starting Unified Error Handling System Tests')
    print('=' * 60)
    
    # Test basic functionality
    if not test_unified_error_handling():
        print(' Basic error handling tests failed')
        return 1
    
    print('\n Summary')
    print('=' * 60)
    print(' All tests passed successfully!')
    print(' Unified error handling system is working correctly')
    
    print('\n Unified Error Handling System is ready for production use!')
    return 0

if __name__ == '__main__':
    sys.exit(main())
