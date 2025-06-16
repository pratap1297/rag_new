# Comprehensive RAG System Test Suite

A comprehensive testing framework for the RAG (Retrieval-Augmented Generation) system that performs extensive analysis across multiple dimensions including functionality, performance, security, and integration testing.

## 🎯 Overview

This test suite provides:
- **21+ comprehensive tests** across 9 categories
- **Performance benchmarking** with response time and throughput analysis
- **Security testing** including input validation and injection protection
- **Integration testing** for LLM and embedding providers
- **OpenAI-powered analysis** for intelligent insights and recommendations
- **Detailed reporting** with JSON and human-readable summaries

## 📋 Test Categories

### 1. System Health Tests (4 tests)
- Basic health endpoint verification
- Component health monitoring
- System resource monitoring
- External API dependencies check

### 2. API Functionality Tests (3 tests)
- Health endpoint testing
- Query endpoint testing
- Stats endpoint testing

### 3. Document Processing Tests (3 tests)
- Document upload and ingestion
- Processing verification
- Content validation

### 4. Query Quality Tests (4 tests)
- Query response accuracy
- Topic coverage analysis
- Source attribution verification
- Response consistency testing

### 5. Performance Tests (2 tests)
- Response time benchmarking
- System throughput analysis

### 6. Concurrency Tests (1 test)
- Concurrent query processing
- Load handling verification

### 7. Edge Case Tests (1 test)
- Invalid query handling
- Error condition testing

### 8. Security Tests (1 test)
- Input validation security
- Injection attack protection

### 9. Integration Tests (2 tests)
- LLM provider integration
- Embedding provider integration

## 🚀 Quick Start

### Prerequisites
```bash
pip install requests asyncio openai numpy
```

### Basic Usage
```bash
# Run with default settings
python comprehensive_test_suite.py

# Run with verbose output
python comprehensive_test_suite.py --verbose

# Run against custom URL
python comprehensive_test_suite.py --url http://localhost:9000

# Use custom API key
python comprehensive_test_suite.py --api-key your_api_key_here
```

### Using the Test Runner
```bash
# Simple run
python run_comprehensive_tests.py

# Verbose mode
python run_comprehensive_tests.py --verbose

# Custom configuration
python run_comprehensive_tests.py --url http://localhost:9000 --verbose
```

## 🔧 Configuration

### OpenAI Integration (Optional)
Create `openai.json` for AI-powered analysis:
```json
{
  "api_key": "sk-your_openai_api_key_here",
  "model": "gpt-4-turbo-preview",
  "max_tokens": 2000,
  "temperature": 0.1
}
```

### Command Line Options
```
--url URL                 RAG system base URL (default: http://localhost:8000)
--api-key API_KEY         API key for authentication (default: test_api_key_123)
--openai-config FILE      OpenAI configuration file (default: openai.json)
--verbose                 Enable verbose logging
```

## 📊 Test Results

### Output Files
Results are saved to `test_results/` directory:
- `analysis_YYYYMMDD_HHMMSS.json` - Complete test results in JSON format
- `summary_YYYYMMDD_HHMMSS.txt` - Human-readable summary report
- `openai_analysis_YYYYMMDD_HHMMSS.json` - AI analysis (if OpenAI configured)

### Scoring System
- **Overall Score**: 0-100 based on test pass rate and performance
- **Performance Penalties**: Applied for slow tests (>10 seconds)
- **Critical Penalties**: Applied for security or health failures

### Example Results
```
============================================================
📊 ANALYSIS COMPLETE
============================================================
Overall Score: 97.1/100
Tests Passed: 21
Tests Failed: 0

🔧 Top Recommendations:
  1. Performance optimization needed: 7 tests took >5 seconds

📁 Detailed results saved to: test_results/
✅ System analysis completed successfully
```

## 🔍 Test Details

### Performance Thresholds
- **Response Time**: Average <15 seconds, individual <20 seconds
- **Throughput**: Minimum 60% success rate under load
- **Concurrency**: Minimum 50% success rate for concurrent operations

### Security Testing
- SQL injection protection
- XSS attack prevention
- Path traversal protection
- Input validation verification

### Quality Metrics
- Topic coverage scoring
- Source attribution accuracy
- Response consistency analysis
- Answer relevance evaluation

## 🛠️ Customization

### Adding New Tests
1. Create test method in `ComprehensiveTestSuite` class
2. Add to appropriate test category method
3. Update test documentation

### Custom Test Documents
Modify `_create_test_documents()` method to add domain-specific content:
```python
def _create_test_documents(self) -> Dict[str, str]:
    return {
        "your_domain.txt": """
        Your domain-specific content here...
        """,
        # ... more documents
    }
```

### Custom Test Queries
Modify `_create_test_queries()` method for domain-specific queries:
```python
def _create_test_queries(self) -> List[Dict[str, Any]]:
    return [
        {
            "query": "Your domain-specific question?",
            "expected_topics": ["topic1", "topic2"],
            "expected_sources": ["your_domain.txt"],
            "complexity": "medium"
        },
        # ... more queries
    ]
```

## 📈 Performance Analysis

### Metrics Collected
- **Response Times**: Individual and average query response times
- **Throughput**: Queries per second under load
- **Concurrency**: Performance under concurrent load
- **Resource Usage**: System resource consumption
- **Error Rates**: Success/failure ratios

### Benchmarking
The test suite provides baseline performance metrics:
- Simple queries: ~2-3 seconds
- Complex queries: ~4-5 seconds
- Concurrent processing: 1+ QPS
- Document processing: ~2 seconds per document

## 🔒 Security Features

### Input Validation Testing
- Empty/null input handling
- Oversized input processing
- Special character handling
- Malformed request processing

### Injection Protection
- SQL injection attempts
- XSS attack vectors
- Path traversal attempts
- Command injection tests

## 🤖 AI-Powered Analysis

When OpenAI is configured, the test suite provides:
- **Intelligent Issue Detection**: AI identifies patterns in failures
- **Performance Recommendations**: Optimization suggestions
- **Risk Assessment**: Security and reliability risk analysis
- **Priority Actions**: Ranked list of improvement actions

### Sample AI Analysis
```json
{
  "health_score": 85,
  "issues": [
    "Response times above optimal thresholds",
    "Security validation concerns detected"
  ],
  "recommendations": [
    "Implement response caching for frequently asked queries",
    "Add input sanitization for security endpoints"
  ],
  "risks": [
    "Performance degradation under high load",
    "Potential security vulnerabilities"
  ],
  "priorities": [
    "Address security validation immediately",
    "Optimize query response times",
    "Implement monitoring and alerting"
  ]
}
```

## 🚨 Troubleshooting

### Common Issues

**Server Not Running**
```
Error: Health check failed: Connection refused
```
Solution: Ensure RAG system is running on specified URL

**API Key Issues**
```
Error: API call failed: 401 Unauthorized
```
Solution: Verify API key configuration

**OpenAI Configuration**
```
Warning: OpenAI API key not found in config
```
Solution: Create `openai.json` with valid API key or run without AI analysis

**Performance Issues**
```
Error: Average response time too high: 20000ms
```
Solution: Check system resources and optimize query processing

### Debug Mode
Run with `--verbose` flag for detailed logging:
```bash
python comprehensive_test_suite.py --verbose
```

## 📝 Contributing

To extend the test suite:
1. Add new test methods following the existing pattern
2. Update documentation
3. Test thoroughly
4. Submit pull request

### Test Method Template
```python
async def _test_your_feature(self) -> Dict[str, Any]:
    """Test your specific feature"""
    try:
        # Your test logic here
        result = await your_test_logic()
        
        if not result.success:
            raise Exception("Test condition failed")
        
        return {
            "metric1": result.value1,
            "metric2": result.value2,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e)}
```

## 📄 License

This test suite is part of the RAG system project and follows the same licensing terms.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review test logs in verbose mode
3. Check system requirements
4. Verify configuration files

---

**Happy Testing! 🧪✨** 