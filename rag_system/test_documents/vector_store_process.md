# Export command
    export_parser = subparsers.add_parser('export', help='Export system data')
    export_parser.add_argument('--output-dir', default='exports', help='Output directory')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze embeddings')
    analyze_parser.add_argument('--sample-size', type=int, default=10, help='Sample size for analysis')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create manager
    manager = VectorStoreManager(args.url, args.api_key)
    
    # Execute command
    try:
        if args.command == 'overview':
            manager.view_system_overview()
            
        elif args.command == 'list':
            if args.list_type == 'docs':
                manager.list_documents(args.limit, args.search)
            elif args.list_type == 'chunks':
                manager.list_chunks(args.limit, args.source_type, args.source_id)
            else:
                list_parser.print_help()
                
        elif args.command == 'view':
            if args.type == 'doc':
                manager.view_document_details(args.id)
            elif args.type == 'chunk':
                manager.view_chunk_details(args.id)
                
        elif args.command == 'search':
            manager.search_vectors(args.query, args.k)
            
        elif args.command == 'delete':
            manager.delete_document(args.file_id, args.yes)
            
        elif args.command == 'cleanup':
            manager.cleanup_orphaned_data(not args.no_dry_run)
            
        elif args.command == 'export':
            manager.export_data(args.output_dir, args.format)
            
        elif args.command == 'analyze':
            manager.analyze_embeddings(args.sample_size)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Operation cancelled by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
```

## File: system_prompt_manager.py
```python
#!/usr/bin/env python3
"""
System Prompt Manager - Configure and test LLM system prompts
Usage: python system_prompt_manager.py [command] [options]
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

class SystemPromptManager:
    """System prompt configuration and testing tool"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
        
        self.prompts_file = Path("system_prompts.json")
        self.default_prompts = self._get_default_prompts()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _get_default_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Get default system prompts for different scenarios"""
        return {
            "general_rag": {
                "name": "General RAG Assistant",
                "description": "Standard RAG system prompt for general knowledge queries",
                "prompt": """You are a helpful AI assistant that provides accurate, informative answers based on the provided context. 

Guidelines:
1. Use ONLY the information from the provided context
2. If the context doesn't contain enough information, clearly state this
3. Be concise but comprehensive in your responses
4. Cite specific details from the context when relevant
5. If asked about something not in the context, politely decline and suggest seeking additional sources
6. Maintain a professional and helpful tone

Context: {context}

Question: {query}

Answer:""",
                "temperature": 0.1,
                "max_tokens": 2048,
                "use_cases": ["general queries", "documentation search", "knowledge retrieval"]
            },
            
            "technical_support": {
                "name": "Technical Support Specialist",
                "description": "Specialized prompt for technical support and troubleshooting",
                "prompt": """You are an expert technical support specialist with deep knowledge of networking, systems administration, and IT infrastructure. Provide detailed, actionable solutions based on the provided documentation.

Guidelines:
1. Focus on practical, step-by-step solutions
2. Include relevant commands, configurations, or code when available in the context
3. Explain the reasoning behind recommendations
4. Highlight potential risks or considerations
5. If multiple solutions exist, present them in order of preference
6. Always reference the source documentation when providing specific procedures

Technical Context: {context}

Support Request: {query}

Technical Solution:""",
                "temperature": 0.05,
                "max_tokens": 3072,
                "use_cases": ["troubleshooting", "configuration help", "technical procedures"]
            },
            
            "security_analyst": {
                "name": "Security Analyst",
                "description": "Security-focused prompt for threat analysis and recommendations",
                "prompt": """You are a cybersecurity expert analyzing security-related queries. Provide comprehensive security guidance based on the available documentation and best practices.

Security Guidelines:
1. Always prioritize security over convenience
2. Provide specific, actionable security recommendations
3. Explain potential security risks and their impact
4. Reference security frameworks and standards when applicable
5. Include both preventive and detective controls
6. Consider compliance requirements and regulatory standards
7. Provide implementation priorities (Critical, High, Medium, Low)

Security Context: {context}

Security Query: {query}

Security Analysis:""",
                "temperature": 0.0,
                "max_tokens": 2048,
                "use_cases": ["security assessments", "threat analysis", "compliance guidance"]
            },
            
            "network_engineer": {
                "name": "Network Engineer",
                "description": "Specialized prompt for network configuration and troubleshooting",
                "prompt": """You are a senior network engineer with expertise in routing, switching, and network protocols. Provide detailed technical guidance for network-related queries.

Network Engineering Guidelines:
1. Provide specific CLI commands and configurations
2. Explain the technical rationale for recommendations
3. Consider network topology and scalability
4. Include troubleshooting steps and verification commands
5. Highlight best practices and common pitfalls
6. Reference relevant RFCs or standards when applicable
7. Consider performance and security implications

Network Documentation: {context}

Network Query: {query}

Network Engineering Response:""",
                "temperature": 0.1,
                "max_tokens": 3072,
                "use_cases": ["network configuration", "protocol troubleshooting", "topology design"]
            },
            
            "incident_responder": {
                "name": "Incident Response Specialist",
                "description": "Prompt for incident response and emergency procedures",
                "prompt": """You are an experienced incident response specialist. Provide immediate, actionable guidance for security incidents and operational emergencies based on established procedures.

Incident Response Guidelines:
1. Prioritize containment and damage limitation
2. Provide clear, sequential action steps
3. Include communication and escalation procedures
4. Consider legal and compliance requirements
5. Emphasize evidence preservation
6. Provide both immediate and follow-up actions
7. Include post-incident analysis recommendations

Incident Response Procedures: {context}

Incident Details: {query}

Incident Response Plan:""",
                "temperature": 0.0,
                "max_tokens": 2048,
                "use_cases": ["security incidents", "system outages", "emergency procedures"]
            },
            
            "code_reviewer": {
                "name": "Code Review Specialist",
                "description": "Prompt for code analysis and development guidance",
                "prompt": """You are an expert software developer and code reviewer. Analyze code, configurations, and development practices based on the provided documentation.

Code Review Guidelines:
1. Focus on security vulnerabilities and best practices
2. Identify potential performance issues
3. Suggest improvements for maintainability and readability
4. Check for compliance with coding standards
5. Provide specific, actionable recommendations
6. Explain the reasoning behind suggestions
7. Consider scalability and error handling

Development Documentation: {context}

Code Review Request: {query}

Code Review Analysis:""",
                "temperature": 0.1,
                "max_tokens": 3072,
                "use_cases": ["code review", "development guidance", "API documentation"]
            }
        }
    
    def load_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Load prompts from file or create default ones"""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, 'r') as f:
                    prompts = json.load(f)
                self.logger.info(f"Loaded prompts from {self.prompts_file}")
                return prompts
            except Exception as e:
                self.logger.error(f"Failed to load prompts: {e}")
        
        # Create default prompts file
        self.save_prompts(self.default_prompts)
        return self.default_prompts
    
    def save_prompts(self, prompts: Dict[str, Dict[str, Any]]) -> bool:
        """Save prompts to file"""
        try:
            with open(self.prompts_file, 'w') as f:
                json.dump(prompts, f, indent=2)
            self.logger.info(f"Saved prompts to {self.prompts_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save prompts: {e}")
            return False
    
    def list_prompts(self):
        """List all available prompts"""
        print(f"\n{Fore.CYAN}📝 SYSTEM PROMPTS{Style.RESET_ALL}")
        print("=" * 50)
        
        prompts = self.load_prompts()
        
        if not prompts:
            print("📭 No prompts found")
            return
        
        for key, prompt_data in prompts.items():
            name = prompt_data.get('name', key)
            description = prompt_data.get('description', 'No description')
            use_cases = prompt_data.get('use_cases', [])
            
            print(f"\n🔹 {Fore.BLUE}{key}{Style.RESET_ALL}")
            print(f"   Name: {name}")
            print(f"   Description: {description}")
            print(f"   Use Cases: {', '.join(use_cases)}")
            print(f"   Temperature: {prompt_data.get('temperature', 0.1)}")
            print(f"   Max Tokens: {prompt_data.get('max_tokens', 2048)}")
    
    def view_prompt(self, prompt_key: str):
        """View detailed prompt information"""
        print(f"\n{Fore.CYAN}🔍 PROMPT DETAILS: {prompt_key}{Style.RESET_ALL}")
        print("=" * 50)
        
        prompts = self.load_prompts()
        prompt_data = prompts.get(prompt_key)
        
        if not prompt_data:
            print(f"{Fore.RED}❌ Prompt not found: {prompt_key}{Style.RESET_ALL}")
            return
        
        print(f"📝 Name: {prompt_data.get('name', 'Unknown')}")
        print(f"📄 Description: {prompt_data.get('description', 'No description')}")
        print(f"🎯 Use Cases: {', '.join(prompt_data.get('use_cases', []))}")
        print(f"🌡️ Temperature: {prompt_data.get('temperature', 0.1)}")
        print(f"📏 Max Tokens: {prompt_data.get('max_tokens', 2048)}")
        
        print(f"\n📋 PROMPT TEMPLATE:")
        print("-" * 30)
        print(prompt_data.get('prompt', 'No prompt defined'))
    
    def edit_prompt(self, prompt_key: str):
        """Interactive prompt editing"""
        print(f"\n{Fore.CYAN}✏️ EDIT PROMPT: {prompt_key}{Style.RESET_ALL}")
        print("=" * 50)
        
        prompts = self.load_prompts()
        
        if prompt_key in prompts:
            prompt_data = prompts[prompt_key].copy()
            print(f"Editing existing prompt: {prompt_data.get('name', 'Unknown')}")
        else:
            print(f"Creating new prompt: {prompt_key}")
            prompt_data = {
                "name": "",
                "description": "",
                "prompt": "",
                "temperature": 0.1,
                "max_tokens": 2048,
                "use_cases": []
            }
        
        # Interactive editing
        try:
            print(f"\nCurrent values (press Enter to keep current):")
            
            # Name
            current_name = prompt_data.get('name', '')
            new_name = input(f"Name [{current_name}]: ").strip()
            if new_name:
                prompt_data['name'] = new_name
            
            # Description
            current_desc = prompt_data.get('description', '')
            new_desc = input(f"Description [{current_desc}]: ").strip()
            if new_desc:
                prompt_data['description'] = new_desc
            
            # Temperature
            current_temp = prompt_data.get('temperature', 0.1)
            new_temp = input(f"Temperature [{current_temp}]: ").strip()
            if new_temp:
                try:
                    prompt_data['temperature'] = float(new_temp)
                except ValueError:
                    print(f"⚠️ Invalid temperature, keeping {current_temp}")
            
            # Max tokens
            current_tokens = prompt_data.get('max_tokens', 2048)
            new_tokens = input(f"Max Tokens [{current_tokens}]: ").strip()
            if new_tokens:
                try:
                    prompt_data['max_tokens'] = int(new_tokens)
                except ValueError:
                    print(f"⚠️ Invalid max tokens, keeping {current_tokens}")
            
            # Use cases
            current_cases = ', '.join(prompt_data.get('use_cases', []))
            new_cases = input(f"Use Cases (comma-separated) [{current_cases}]: ").strip()
            if new_cases:
                prompt_data['use_cases'] = [case.strip() for case in new_cases.split(',')]
            
            # Prompt template
            print(f"\nCurrent prompt template:")
            print("-" * 30)
            print(prompt_data.get('prompt', ''))
            print("-" * 30)
            
            edit_prompt = input("Edit prompt template? (y/N): ").strip().lower()
            if edit_prompt == 'y':
                print("Enter new prompt template (end with '###' on a new line):")
                prompt_lines = []
                while True:
                    line = input()
                    if line.strip() == '###':
                        break
                    prompt_lines.append(line)
                prompt_data['prompt'] = '\n'.join(prompt_lines)
            
            # Save changes
            save = input(f"\nSave changes? (Y/n): ").strip().lower()
            if save != 'n':
                prompts[prompt_key] = prompt_data
                if self.save_prompts(prompts):
                    print(f"{Fore.GREEN}✅ Prompt saved successfully{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ Failed to save prompt{Style.RESET_ALL}")
            else:
                print("❌ Changes discarded")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}❌ Editing cancelled{Style.RESET_ALL}")
    
    def test_prompt(self, prompt_key: str, test_query: str = None):
        """Test a prompt with a sample query"""
        print(f"\n{Fore.CYAN}🧪 TEST PROMPT: {prompt_key}{Style.RESET_ALL}")
        print("=" * 50)
        
        prompts = self.load_prompts()
        prompt_data = prompts.get(prompt_key)
        
        if not prompt_data:
            print(f"{Fore.RED}❌ Prompt not found: {prompt_key}{Style.RESET_ALL}")
            return
        
        if not test_query:
            test_query = input("Enter test query: ").strip()
            if not test_query:
                print("❌ No query provided")
                return
        
        print(f"🔍 Testing with query: {test_query}")
        print(f"📝 Using prompt: {prompt_data.get('name', 'Unknown')}")
        
        try:
            # Test via API
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={
                    "query": test_query,
                    "max_results": 5,
                    "system_prompt": prompt_data.get('prompt', ''),
                    "temperature": prompt_data.get('temperature', 0.1),
                    "max_tokens": prompt_data.get('max_tokens', 2048)
                },
                timeout=30
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✅ Response received ({response_time:.0f}ms)")
                print(f"📊 Sources found: {len(data.get('sources', []))}")
                
                answer = data.get('answer', '')
                print(f"\n🤖 AI RESPONSE:")
                print("-" * 30)
                print(answer)
                
                # Show sources
                sources = data.get('sources', [])
                if sources:
                    print(f"\n📚 SOURCES:")
                    for i, source in enumerate(sources[:3], 1):
                        print(f"{i}. {source.get('source_name', 'Unknown')} (Score: {source.get('relevance_score', 0):.3f})")
                
                return {
                    "success": True,
                    "response_time_ms": response_time,
                    "answer_length": len(answer),
                    "sources_count": len(sources)
                }
            else:
                print(f"{Fore.RED}❌ API request failed: {response.status_code}{Style.RESET_ALL}")
                print(f"Error: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"{Fore.RED}❌ Test failed: {e}{Style.RESET_ALL}")
            return {"success": False, "error": str(e)}
    
    def compare_prompts(self, prompt_keys: List[str], test_query: str = None):
        """Compare multiple prompts with the same query"""
        print(f"\n{Fore.CYAN}🔬 PROMPT COMPARISON{Style.RESET_ALL}")
        print("=" * 50)
        
        if not test_query:
            test_query = input("Enter test query for comparison: ").strip()
            if not test_query:
                print("❌ No query provided")
                return
        
        prompts = self.load_prompts()
        results = {}
        
        print(f"🔍 Testing query: {test_query}")
        print(f"📝 Comparing {len(prompt_keys)} prompts...\n")
        
        for prompt_key in prompt_keys:
            if prompt_key not in prompts:
                print(f"⚠️ Skipping unknown prompt: {prompt_key}")
                continue
            
            print(f"Testing {prompt_key}...")
            result = self.test_prompt(prompt_key, test_query)
            results[prompt_key] = result
            time.sleep(1)  # Small delay between tests
        
        # Display comparison
        print(f"\n{Fore.CYAN}📊 COMPARISON RESULTS{Style.RESET_ALL}")
        print("=" * 60)
        
        for prompt_key, result in results.items():
            if result.get('success'):
                prompt_name = prompts[prompt_key].get('name', prompt_key)
                print(f"\n🔹 {Fore.BLUE}{prompt_name}{Style.RESET_ALL}")
                print(f"   Response Time: {result.get('response_time_ms', 0):.0f}ms")
                print(f"   Answer Length: {result.get('answer_length', 0)} chars")
                print(f"   Sources Count: {result.get('sources_count', 0)}")
            else:
                print(f"\n❌ {prompt_key}: {result.get('error', 'Unknown error')}")
    
    def benchmark_prompts(self, test_queries: List[str] = None):
        """Benchmark all prompts with multiple queries"""
        print(f"\n{Fore.CYAN}⚡ PROMPT BENCHMARKING{Style.RESET_ALL}")
        print("=" * 50)
        
        if not test_queries:
            test_queries = [
                "How do I configure BGP on a Cisco router?",
                "What are network security best practices?",
                "How to troubleshoot a system outage?",
                "Explain cloud architecture patterns",
                "What are the steps for incident response?"
            ]
        
        prompts = self.load_prompts()
        benchmark_results = {}
        
        print(f"🧪 Benchmarking {len(prompts)} prompts with {len(test_queries)} queries...")
        
        for prompt_key in prompts.keys():
            print(f"\nBenchmarking {prompt_key}...")
            prompt_results = []
            
            for query in test_queries:
                result = self.test_prompt(prompt_key, query)
                if result.get('success'):
                    prompt_results.append({
                        "query": query,
                        "response_time_ms": result.get('response_time_ms', 0),
                        "answer_length": result.get('answer_length', 0),
                        "sources_count": result.get('sources_count', 0)
                    })
                
                time.sleep(0.5)  # Small delay
            
            if prompt_results:
                avg_response_time = sum(r['response_time_ms'] for r in prompt_results) / len(prompt_results)
                avg_answer_length = sum(r['answer_length'] for r in prompt_results) / len(prompt_results)
                avg_sources = sum(r['sources_count'] for r in prompt_results) / len(prompt_results)
                
                benchmark_results[prompt_key] = {
                    "successful_queries": len(prompt_results),
                    "avg_response_time_ms": avg_response_time,
                    "avg_answer_length": avg_answer_length,
                    "avg_sources_count": avg_sources,
                    "details": prompt_results
                }
        
        # Display benchmark results
        print(f"\n{Fore.CYAN}📊 BENCHMARK RESULTS{Style.RESET_ALL}")
        print("=" * 60)
        
        for prompt_key, result in benchmark_results.items():
            prompt_name = prompts[prompt_key].get('name', prompt_key)
            print(f"\n🔹 {Fore.BLUE}{prompt_name}{Style.RESET_ALL}")
            print(f"   Successful Queries: {result['successful_queries']}/{len(test_queries)}")
            print(f"   Avg Response Time: {result['avg_response_time_ms']:.0f}ms")
            print(f"   Avg Answer Length: {result['avg_answer_length']:.0f} chars")
            print(f"   Avg Sources: {result['avg_sources_count']:.1f}")
        
        # Save benchmark results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"prompt_benchmark_{timestamp}.json")
        
        try:
            with open(results_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "test_queries": test_queries,
                    "results": benchmark_results
                }, f, indent=2)
            print(f"\n💾 Benchmark results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Failed to save benchmark results: {e}")
    
    def export_prompts(self, output_file: str = None):
        """Export prompts to a file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"system_prompts_export_{timestamp}.json"
        
        prompts = self.load_prompts()
        
        try:
            with open(output_file, 'w') as f:
                json.dump(prompts, f, indent=2)
            print(f"✅ Prompts exported to: {output_file}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def import_prompts(self, input_file: str, merge: bool = True):
        """Import prompts from a file"""
        try:
            with open(input_file, 'r') as f:
                imported_prompts = json.load(f)
            
            if merge:
                # Merge with existing prompts
                existing_prompts = self.load_prompts()
                existing_prompts.update(imported_prompts)
                final_prompts = existing_prompts
            else:
                # Replace all prompts
                final_prompts = imported_prompts
            
            if self.save_prompts(final_prompts):
                print(f"✅ Imported {len(imported_prompts)} prompts from: {input_file}")
            else:
                print(f"❌ Failed to save imported prompts")
                
        except Exception as e:
            print(f"❌ Import failed: {e}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="System Prompt Manager")
    parser.add_argument('--url', default='http://localhost:8000', help='RAG system base URL')
    parser.add_argument('--api-key', help='API key for authentication')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List prompts
    list_parser = subparsers.add_parser('list', help='List all prompts')
    
    # View prompt
    view_parser = subparsers.add_parser('view', help='View prompt details')
    view_parser.add_argument('prompt_key', help='Prompt key to view')
    
    # Edit prompt
    edit_parser = subparsers.add_parser('edit', help='Edit or create prompt')
    edit_parser.add_argument('prompt_key', help='Prompt key to edit')
    
    # Test prompt
    test_parser = subparsers.add_parser('test', help='Test a prompt')
    test_parser.add_argument('prompt_key', help='Prompt key to test')
    test_parser.add_argument('--query', help='Test query')
    
    # Compare prompts
    compare_parser = subparsers.add_parser('compare', help='Compare multiple prompts')
    compare_parser.add_argument('prompt_keys', nargs='+', help='Prompt keys to compare')
    compare_parser.add_argument('--query', help='Test query for comparison')
    
    # Benchmark prompts
    benchmark_parser = subparsers.add_parser('benchmark', help='Benchmark all prompts')
    
    # Export prompts
    export_parser = subparsers.add_parser('export', help='Export prompts')
    export_parser.add_argument('--output', help='Output file path')
    
    # Import prompts
    import_parser = subparsers.add_parser('import', help='Import prompts')
    import_parser.add_argument('input_file', help='Input file path')
    import_parser.add_argument('--replace', action='store_true', help='Replace all prompts instead of merging')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create manager
    manager = SystemPromptManager(args.url, args.api_key)
    
    # Execute command
    try:
        if args.command == 'list':
            manager.list_prompts()
            
        elif args.command == 'view':
            manager.view_prompt(args.prompt_key)
            
        elif args.command == 'edit':
            manager.edit_prompt(args.prompt_key)
            
        elif args.command == 'test':
            manager.test_prompt(args.prompt_key, args.query)
            
        elif args.command == 'compare':
            manager.compare_prompts(args.prompt_keys, args.query)
            
        elif args.command == 'benchmark':
            manager.benchmark_prompts()
            
        elif args.command == 'export':
            manager.export_prompts(args.output)
            
        elif args.command == 'import':
            manager.import_prompts(args.input_file, not args.replace)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Operation cancelled by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
```

## Usage Examples

### Vector Store Manager Commands

```bash
# System overview
python vector_store_manager.py overview

# List all documents
python vector_store_manager.py list docs

# List documents with search
python vector_store_manager.py list docs --search "network" --limit 10

# List chunks from specific document
python vector_store_manager.py list chunks --source-id file_123 --limit 20

# View document details
python vector_store_manager.py view doc file_abc123

# View chunk details  
python vector_store_manager.py view chunk chunk_xyz789

# Search vectors
python vector_store_manager.py search "BGP configuration" --k 5

# Delete document (with confirmation)
python vector_store_manager.py delete file_abc123

# Delete document (skip confirmation)
python vector_store_manager.py delete file_abc123 --yes

# Cleanup orphaned data (dry run)
python vector_store_manager.py cleanup

# Actually perform cleanup
python vector_store_manager.py cleanup --no-dry-run

# Export system data
python vector_store_manager.py export --format csv --output-dir exports

# Analyze embeddings
python vector_store_manager.py analyze --sample-size 5
```

### System Prompt Manager Commands

```bash
# List all prompts
python system_prompt_manager.py list

# View specific prompt
python system_prompt_manager.py view general_rag

# Edit/create prompt (interactive)
python system_prompt_manager.py edit technical_support

# Test prompt with custom query
python system_prompt_manager.py test security_analyst --query "How to secure BGP?"

# Compare multiple prompts
python system_prompt_manager.py compare general_rag technical_support network_engineer --query "Configure OSPF"

# Benchmark all prompts
python system_prompt_manager.py benchmark

# Export prompts
python system_prompt_manager.py export --output my_prompts.json

# Import prompts (merge with existing)
python system_prompt_manager.py import custom_prompts.json

# Import prompts (replace all)
python system_prompt_manager.py import custom_prompts.json --replace
```

## Sample Output Examples

### Vector Store Overview
```
📊 RAG SYSTEM OVERVIEW
==================================================
📁 Total Files: 25
🧩 Total Chunks: 487
🔢 Total Vectors: 487
💾 Memory Usage: 156.3 MB
⚡ CPU Usage: 12.4%

🔍 Vector Store Details:
   Index Type: IndexHNSWFlat
   Dimension: 1024D
   Embedding Model: embed-english-v3.0
   Provider: cohere
```

### Document List
```
📄 DOCUMENTS OVERVIEW
==================================================
┌────────────┬─────────────────────┬────────┬─────────┬─────────────────┬─────────┐
│ File ID    │ Name                │ Chunks │ Vectors │ Ingested        │ Size    │
├────────────┼─────────────────────┼────────┼─────────┼─────────────────┼─────────┤
│ file_abc1…│ network_security.txt│   12   │   12    │ 2024-12-19 10:30│  45.2 KB│
│ file_def2…│ cisco_bgp_guide.txt │   23   │   23    │ 2024-12-19 10:35│  78.9 KB│
│ file_ghi3…│ cloud_architecture  │   18   │   18    │ 2024-12-19 10:40│  62.1 KB│
└────────────┴─────────────────────┴────────┴─────────┴─────────────────┴─────────┘

📊 Total: 3 documents
```

### Vector Search Results
```
🔍 VECTOR SEARCH: 'BGP configuration'
==================================================
🎯 Query: BGP configuration
📊 Found 5 similar vectors
⏱️ Response time: 247ms

┌──────┬─────────┬──────┬─────────────────────────┬──────────────────────────────┐
│ Rank │ Score   │ Type │ Source                  │ Content Preview              │
├──────┼─────────┼──────┼─────────────────────────┼──────────────────────────────┤
│   1  │  0.923  │ file │ cisco_bgp_guide.txt...  │ Advanced BGP Configuration...│
│   2  │  0.867  │ file │ network_protocols.txt...│ BGP Route Filtering: 1. Pr...│
│   3  │  0.834  │ file │ cisco_best_practices... │ BGP Security: 1. BGP authe...│
└──────┴─────────┴──────┴─────────────────────────┴──────────────────────────────┘

🤖 AI RESPONSE:
--------------------
To configure BGP on a Cisco router, follow these essential steps:

1. Enable BGP with your AS number: `router bgp 65001`
2. Configure BGP neighbors: `neighbor 192.168.1.2 remote-as 65002`
3. Advertise networks: `network 10.0.0.0 mask 255.0.0.0`...
```

### System Prompt List
```
📝 SYSTEM PROMPTS
==================================================

🔹 general_rag
   Name: General RAG Assistant
   Description: Standard RAG system prompt for general knowledge queries
   Use Cases: general queries, documentation search, knowledge retrieval
   Temperature: 0.1
   Max Tokens: 2048

🔹 technical_support
   Name: Technical Support Specialist
   Description: Specialized prompt for technical support and troubleshooting
   Use Cases: troubleshooting, configuration help, technical procedures
   Temperature: 0.05
   Max Tokens: 3072

🔹 security_analyst
   Name: Security Analyst
   Description: Security-focused prompt for threat analysis and recommendations
   Use Cases: security assessments, threat analysis, compliance guidance
   Temperature: 0.0
   Max Tokens: 2048
```

## Quick Setup Guide

### 1. Vector Store Manager Setup
```bash
# Make executable
chmod +x vector_store_manager.py

# Basic usage (no API key needed for read operations)
python vector_store_manager.py overview

# With API key for full functionality
python vector_store_manager.py --api-key your_rag_api_key list docs
```

### 2. System Prompt Manager Setup
```bash
# Initialize with default prompts
python system_prompt_manager.py list

# This creates system_prompts.json with 6 default prompts
```

### 3. Integration with RAG System

#### For vector_store_manager.py:
- Uses direct imports when available: `from config import config`
- Falls back to API calls when imports fail
- Works both standalone and integrated

#### For system_prompt_manager.py:
- Manages prompts in `system_prompts.json` 
- Tests prompts via API calls to your RAG system
- Can be used independently of main system

## Key Features

### Vector Store Manager:
✅ **Complete CRUD operations** for documents, chunks, vectors
✅ **Visual data exploration** with colored tables
✅ **Search and filtering** capabilities
✅ **Data export** in JSON/CSV formats
✅ **Cleanup tools** for orphaned data
✅ **Performance analysis** of embeddings
✅ **System health monitoring**

### System Prompt Manager:
✅ **6 specialized prompts** included by default
✅ **Interactive prompt editing** 
✅ **A/B testing** and comparison tools
✅ **Performance benchmarking**
✅ **Import/export** functionality
✅ **Real-time testing** against your RAG system

These scripts provide **complete management capabilities** for your RAG system's data and prompts! 🛠️✨# Vector Store Management & System Prompt Configuration Scripts

## File: vector_store_manager.py
```python
#!/usr/bin/env python3
"""
Vector Store Management Script - CRUD Operations for Documents, Chunks, and Embeddings
Usage: python vector_store_manager.py [command] [options]
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests
import pandas as pd
from tabulate import tabulate
import colorama
from colorama import Fore, Style
import numpy as np

# Import system components
try:
    from config import config
    from storage import json_store, vector_store
    from embedder import embedder
    from query_engine import query_engine
except ImportError:
    print("⚠️ Could not import system components. Make sure you're running from the correct directory.")
    config = None

# Initialize colorama
colorama.init()

class VectorStoreManager:
    """Comprehensive vector store management interface"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def view_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        print(f"\n{Fore.CYAN}📊 RAG SYSTEM OVERVIEW{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            # Get system status
            response = requests.get(f"{self.base_url}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Display overview
                print(f"📁 Total Files: {data.get('total_files', 0)}")
                print(f"🧩 Total Chunks: {data.get('total_chunks', 0)}")
                print(f"🔢 Total Vectors: {data.get('total_vectors', 0)}")
                print(f"💾 Memory Usage: {data.get('memory_usage_mb', 0):.1f} MB")
                print(f"⚡ CPU Usage: {data.get('cpu_usage_percent', 0):.1f}%")
                
                # Vector store details
                if config and vector_store:
                    stats = vector_store.get_stats()
                    print(f"\n🔍 Vector Store Details:")
                    print(f"   Index Type: {stats.get('index_type', 'Unknown')}")
                    print(f"   Dimension: {stats.get('dimension', 0)}D")
                    print(f"   Embedding Model: {stats.get('model', 'Unknown')}")
                    print(f"   Provider: {stats.get('embedding_provider', 'Unknown')}")
                
                return data
            else:
                print(f"{Fore.RED}❌ Failed to get system status: {response.status_code}{Style.RESET_ALL}")
                return {}
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error getting system overview: {e}{Style.RESET_ALL}")
            return {}
    
    def list_documents(self, limit: int = None, search: str = None) -> List[Dict[str, Any]]:
        """List all documents with optional filtering"""
        print(f"\n{Fore.CYAN}📄 DOCUMENTS OVERVIEW{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            # Get documents from system
            if config and json_store:
                files_data = json_store.load('metadata/files.json', {})
                documents = list(files_data.get('files', {}).values())
            else:
                # Fallback to API
                response = requests.get(f"{self.base_url}/status", timeout=10)
                documents = []  # API doesn't expose individual files yet
            
            # Apply search filter
            if search:
                documents = [
                    doc for doc in documents 
                    if search.lower() in doc.get('file_name', '').lower() or
                       search.lower() in doc.get('file_path', '').lower()
                ]
            
            # Apply limit
            if limit:
                documents = documents[:limit]
            
            if not documents:
                print("📭 No documents found")
                return []
            
            # Display documents table
            table_data = []
            for doc in documents:
                table_data.append([
                    doc.get('file_id', '')[:8] + '...',
                    doc.get('file_name', 'Unknown'),
                    doc.get('chunk_count', 0),
                    len(doc.get('vector_ids', [])),
                    doc.get('ingested_at', 'Unknown')[:16],
                    f"{doc.get('file_size', 0) / 1024:.1f} KB" if doc.get('file_size') else 'Unknown'
                ])
            
            print(tabulate(
                table_data,
                headers=['File ID', 'Name', 'Chunks', 'Vectors', 'Ingested', 'Size'],
                tablefmt='grid'
            ))
            
            print(f"\n📊 Total: {len(documents)} documents")
            
            return documents
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error listing documents: {e}{Style.RESET_ALL}")
            return []
    
    def view_document_details(self, file_id: str) -> Dict[str, Any]:
        """View detailed information about a specific document"""
        print(f"\n{Fore.CYAN}🔍 DOCUMENT DETAILS: {file_id}{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            if config and json_store:
                files_data = json_store.load('metadata/files.json', {})
                document = files_data.get('files', {}).get(file_id)
                
                if not document:
                    print(f"{Fore.RED}❌ Document not found: {file_id}{Style.RESET_ALL}")
                    return {}
                
                # Document metadata
                print(f"📁 File Name: {document.get('file_name', 'Unknown')}")
                print(f"📂 File Path: {document.get('file_path', 'Unknown')}")
                print(f"🔤 File Hash: {document.get('file_hash', 'Unknown')}")
                print(f"📅 Ingested: {document.get('ingested_at', 'Unknown')}")
                print(f"🧩 Chunk Count: {document.get('chunk_count', 0)}")
                print(f"🔢 Vector IDs: {len(document.get('vector_ids', []))}")
                
                # Show vector IDs
                vector_ids = document.get('vector_ids', [])
                if vector_ids:
                    print(f"🔢 Vector IDs: {vector_ids[:10]}{'...' if len(vector_ids) > 10 else ''}")
                
                # Get associated chunks
                chunks_data = json_store.load('metadata/chunks.json', {})
                doc_chunks = [
                    chunk for chunk in chunks_data.get('chunks', {}).values()
                    if chunk.get('source_id') == file_id
                ]
                
                if doc_chunks:
                    print(f"\n🧩 DOCUMENT CHUNKS ({len(doc_chunks)}):")
                    print("-" * 30)
                    
                    for i, chunk in enumerate(doc_chunks[:5], 1):  # Show first 5 chunks
                        content_preview = chunk.get('content', '')[:100] + '...'
                        print(f"{i}. Chunk {chunk.get('chunk_id', 'Unknown')[:8]}...")
                        print(f"   Content: {content_preview}")
                        print(f"   Vector ID: {chunk.get('vector_id', 'Unknown')}")
                        print(f"   Range: {chunk.get('start_index', 0)}-{chunk.get('end_index', 0)}")
                        print()
                    
                    if len(doc_chunks) > 5:
                        print(f"   ... and {len(doc_chunks) - 5} more chunks")
                
                return document
            else:
                print(f"{Fore.RED}❌ System components not available{Style.RESET_ALL}")
                return {}
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error viewing document details: {e}{Style.RESET_ALL}")
            return {}
    
    def list_chunks(self, limit: int = 20, source_type: str = None, 
                   source_id: str = None) -> List[Dict[str, Any]]:
        """List chunks with filtering options"""
        print(f"\n{Fore.CYAN}🧩 CHUNKS OVERVIEW{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            # Get chunks via API
            params = {"limit": limit}
            if source_type:
                params["source_type"] = source_type
            
            response = requests.get(
                f"{self.base_url}/chunks",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                chunks = data.get('chunks', [])
                
                # Apply source_id filter if specified
                if source_id:
                    chunks = [c for c in chunks if c.get('source_id') == source_id]
                
                if not chunks:
                    print("📭 No chunks found")
                    return []
                
                # Display chunks table
                table_data = []
                for chunk in chunks:
                    content_preview = chunk.get('content', '')[:50] + '...'
                    table_data.append([
                        chunk.get('chunk_id', 'Unknown')[:8] + '...',
                        chunk.get('source_type', 'Unknown'),
                        chunk.get('source_id', 'Unknown')[:8] + '...',
                        chunk.get('vector_id', 'Unknown'),
                        len(chunk.get('content', '')),
                        content_preview
                    ])
                
                print(tabulate(
                    table_data,
                    headers=['Chunk ID', 'Source Type', 'Source ID', 'Vector ID', 'Length', 'Content Preview'],
                    tablefmt='grid'
                ))
                
                print(f"\n📊 Showing {len(chunks)} chunks (Total: {data.get('total', 0)})")
                
                return chunks
            else:
                print(f"{Fore.RED}❌ Failed to get chunks: {response.status_code}{Style.RESET_ALL}")
                return []
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error listing chunks: {e}{Style.RESET_ALL}")
            return []
    
    def view_chunk_details(self, chunk_id: str) -> Dict[str, Any]:
        """View detailed information about a specific chunk"""
        print(f"\n{Fore.CYAN}🔍 CHUNK DETAILS: {chunk_id}{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            if config and json_store:
                chunks_data = json_store.load('metadata/chunks.json', {})
                chunk = chunks_data.get('chunks', {}).get(chunk_id)
                
                if not chunk:
                    print(f"{Fore.RED}❌ Chunk not found: {chunk_id}{Style.RESET_ALL}")
                    return {}
                
                # Chunk metadata
                print(f"🆔 Chunk ID: {chunk.get('chunk_id', 'Unknown')}")
                print(f"🔢 Vector ID: {chunk.get('vector_id', 'Unknown')}")
                print(f"📁 Source Type: {chunk.get('source_type', 'Unknown')}")
                print(f"📂 Source ID: {chunk.get('source_id', 'Unknown')}")
                print(f"📅 Created: {chunk.get('created_at', 'Unknown')}")
                print(f"📏 Content Length: {len(chunk.get('content', ''))}")
                print(f"📍 Range: {chunk.get('start_index', 0)}-{chunk.get('end_index', 0)}")
                
                # Content preview
                content = chunk.get('content', '')
                if content:
                    print(f"\n📄 CONTENT:")
                    print("-" * 20)
                    print(content[:500] + ('...' if len(content) > 500 else ''))
                
                # Get vector embedding if available
                vector_id = chunk.get('vector_id')
                if vector_id is not None and config and vector_store:
                    try:
                        # Check if vector exists in store
                        stats = vector_store.get_stats()
                        if vector_id < stats.get('vector_count', 0):
                            print(f"\n🔢 VECTOR INFO:")
                            print(f"   Vector ID: {vector_id}")
                            print(f"   Dimension: {stats.get('dimension', 0)}")
                            print(f"   Index Type: {stats.get('index_type', 'Unknown')}")
                    except Exception as e:
                        print(f"\n⚠️ Vector info unavailable: {e}")
                
                return chunk
            else:
                print(f"{Fore.RED}❌ System components not available{Style.RESET_ALL}")
                return {}
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error viewing chunk details: {e}{Style.RESET_ALL}")
            return {}
    
    def search_vectors(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search vectors using similarity search"""
        print(f"\n{Fore.CYAN}🔍 VECTOR SEARCH: '{query}'{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            # Perform search via API
            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={"query": query, "max_results": k, "include_sources": True},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                sources = data.get('sources', [])
                
                if not sources:
                    print("📭 No similar vectors found")
                    return []
                
                # Display search results
                print(f"🎯 Query: {query}")
                print(f"📊 Found {len(sources)} similar vectors")
                print(f"⏱️ Response time: {data.get('response_time_ms', 0):.0f}ms")
                print()
                
                table_data = []
                for i, source in enumerate(sources, 1):
                    content_preview = source.get('content_preview', '')[:60] + '...'
                    table_data.append([
                        i,
                        f"{source.get('relevance_score', 0):.3f}",
                        source.get('source_type', 'Unknown'),
                        source.get('source_name', 'Unknown')[:30] + '...',
                        content_preview
                    ])
                
                print(tabulate(
                    table_data,
                    headers=['Rank', 'Score', 'Type', 'Source', 'Content Preview'],
                    tablefmt='grid'
                ))
                
                # Show AI response
                answer = data.get('answer', '')
                if answer:
                    print(f"\n🤖 AI RESPONSE:")
                    print("-" * 20)
                    print(answer[:300] + ('...' if len(answer) > 300 else ''))
                
                return sources
            else:
                print(f"{Fore.RED}❌ Search failed: {response.status_code}{Style.RESET_ALL}")
                return []
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error searching vectors: {e}{Style.RESET_ALL}")
            return []
    
    def delete_document(self, file_id: str, confirm: bool = False) -> bool:
        """Delete a document and all associated chunks/vectors"""
        print(f"\n{Fore.YELLOW}🗑️ DELETE DOCUMENT: {file_id}{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            # Get document details first
            if config and json_store:
                files_data = json_store.load('metadata/files.json', {})
                document = files_data.get('files', {}).get(file_id)
                
                if not document:
                    print(f"{Fore.RED}❌ Document not found: {file_id}{Style.RESET_ALL}")
                    return False
                
                print(f"📁 Document: {document.get('file_name', 'Unknown')}")
                print(f"🧩 Chunks: {document.get('chunk_count', 0)}")
                print(f"🔢 Vectors: {len(document.get('vector_ids', []))}")
            
            # Confirmation
            if not confirm:
                response = input(f"\n{Fore.RED}⚠️ Are you sure you want to delete this document? (y/N): {Style.RESET_ALL}")
                if response.lower() != 'y':
                    print("❌ Deletion cancelled")
                    return False
            
            # Delete via API
            delete_response = requests.delete(
                f"{self.base_url}/files/{file_id}",
                headers=self.headers,
                timeout=15
            )
            
            if delete_response.status_code == 200:
                print(f"{Fore.GREEN}✅ Document deleted successfully{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ Failed to delete document: {delete_response.status_code}{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error deleting document: {e}{Style.RESET_ALL}")
            return False
    
    def cleanup_orphaned_data(self, dry_run: bool = True) -> Dict[str, int]:
        """Clean up orphaned chunks and vectors"""
        print(f"\n{Fore.CYAN}🧹 CLEANUP ORPHANED DATA{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            if not config or not json_store:
                print(f"{Fore.RED}❌ System components not available{Style.RESET_ALL}")
                return {}
            
            # Get all data
            files_data = json_store.load('metadata/files.json', {})
            chunks_data = json_store.load('metadata/chunks.json', {})
            
            files = files_data.get('files', {})
            chunks = chunks_data.get('chunks', {})
            
            # Find orphaned chunks (chunks without corresponding files)
            valid_file_ids = set(files.keys())
            orphaned_chunks = []
            
            for chunk_id, chunk in chunks.items():
                source_id = chunk.get('source_id')
                if source_id not in valid_file_ids:
                    orphaned_chunks.append(chunk_id)
            
            # Find orphaned vectors (vectors not referenced by any chunk)
            referenced_vector_ids = set()
            for chunk in chunks.values():
                vector_id = chunk.get('vector_id')
                if vector_id is not None:
                    referenced_vector_ids.add(vector_id)
            
            # Get vector store stats
            vector_stats = vector_store.get_stats()
            total_vectors = vector_stats.get('vector_count', 0)
            
            # Report findings
            print(f"📊 Analysis Results:")
            print(f"   Total Files: {len(files)}")
            print(f"   Total Chunks: {len(chunks)}")
            print(f"   Total Vectors: {total_vectors}")
            print(f"   Orphaned Chunks: {len(orphaned_chunks)}")
            print(f"   Referenced Vectors: {len(referenced_vector_ids)}")
            
            if orphaned_chunks:
                print(f"\n🗑️ Orphaned Chunks Found:")
                for chunk_id in orphaned_chunks[:10]:  # Show first 10
                    chunk = chunks[chunk_id]
                    print(f"   - {chunk_id}: {chunk.get('source_id', 'Unknown')}")
                if len(orphaned_chunks) > 10:
                    print(f"   ... and {len(orphaned_chunks) - 10} more")
            
            if dry_run:
                print(f"\n{Fore.YELLOW}ℹ️ DRY RUN - No changes made{Style.RESET_ALL}")
                print("Run with --no-dry-run to perform actual cleanup")
            else:
                # Perform cleanup
                cleaned_chunks = 0
                if orphaned_chunks:
                    for chunk_id in orphaned_chunks:
                        del chunks[chunk_id]
                        cleaned_chunks += 1
                    
                    # Save updated chunks
                    chunks_data['chunks'] = chunks
                    chunks_data['last_updated'] = datetime.now().isoformat()
                    json_store.save('metadata/chunks.json', chunks_data)
                    
                    print(f"{Fore.GREEN}✅ Cleaned up {cleaned_chunks} orphaned chunks{Style.RESET_ALL}")
            
            return {
                "total_files": len(files),
                "total_chunks": len(chunks),
                "total_vectors": total_vectors,
                "orphaned_chunks": len(orphaned_chunks),
                "cleaned_chunks": 0 if dry_run else cleaned_chunks
            }
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error during cleanup: {e}{Style.RESET_ALL}")
            return {}
    
    def export_data(self, output_dir: str = "exports", format: str = "json") -> bool:
        """Export all system data"""
        print(f"\n{Fore.CYAN}📤 EXPORT SYSTEM DATA{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            export_path = Path(output_dir)
            export_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if config and json_store:
                # Export files metadata
                files_data = json_store.load('metadata/files.json', {})
                files_export_path = export_path / f"files_{timestamp}.{format}"
                
                if format == "json":
                    with open(files_export_path, 'w') as f:
                        json.dump(files_data, f, indent=2, default=str)
                elif format == "csv":
                    if files_data.get('files'):
                        df = pd.DataFrame(list(files_data['files'].values()))
                        df.to_csv(files_export_path, index=False)
                
                # Export chunks metadata
                chunks_data = json_store.load('metadata/chunks.json', {})
                chunks_export_path = export_path / f"chunks_{timestamp}.{format}"
                
                if format == "json":
                    with open(chunks_export_path, 'w') as f:
                        json.dump(chunks_data, f, indent=2, default=str)
                elif format == "csv":
                    if chunks_data.get('chunks'):
                        df = pd.DataFrame(list(chunks_data['chunks'].values()))
                        df.to_csv(chunks_export_path, index=False)
                
                # Export vector store stats
                if vector_store:
                    stats = vector_store.get_stats()
                    stats_export_path = export_path / f"vector_stats_{timestamp}.json"
                    with open(stats_export_path, 'w') as f:
                        json.dump(stats, f, indent=2, default=str)
                
                print(f"✅ Data exported to: {export_path}")
                print(f"   📁 Files: {files_export_path}")
                print(f"   🧩 Chunks: {chunks_export_path}")
                if vector_store:
                    print(f"   📊 Stats: {stats_export_path}")
                
                return True
            else:
                print(f"{Fore.RED}❌ System components not available{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error exporting data: {e}{Style.RESET_ALL}")
            return False
    
    def analyze_embeddings(self, sample_size: int = 10) -> Dict[str, Any]:
        """Analyze embedding quality and distribution"""
        print(f"\n{Fore.CYAN}📊 EMBEDDING ANALYSIS{Style.RESET_ALL}")
        print("=" * 50)
        
        try:
            if not config or not json_store or not vector_store:
                print(f"{Fore.RED}❌ System components not available{Style.RESET_ALL}")
                return {}
            
            # Get vector store stats
            stats = vector_store.get_stats()
            
            print(f"🔢 Vector Store Statistics:")
            print(f"   Total Vectors: {stats.get('vector_count', 0)}")
            print(f"   Dimension: {stats.get('dimension', 0)}")
            print(f"   Index Type: {stats.get('index_type', 'Unknown')}")
            print(f"   Provider: {stats.get('embedding_provider', 'Unknown')}")
            print(f"   Model: {stats.get('model', 'Unknown')}")
            
            # Test embedding generation
            if embedder:
                test_texts = [
                    "Network security best practices",
                    "BGP routing configuration",
                    "Cloud architecture patterns",
                    "Database optimization techniques",
                    "API design guidelines"
                ]
                
                print(f"\n🧪 Testing Embedding Generation:")
                embedding_times = []
                
                for text in test_texts[:sample_size]:
                    start_time = time.time()
                    embedding = embedder.embed(text)
                    end_time = time.time()
                    
                    embedding_time = (end_time - start_time) * 1000
                    embedding_times.append(embedding_time)
                    
                    print(f"   '{text[:30]}...': {embedding_time:.0f}ms, {len(embedding)}D")
                
                avg_time = sum(embedding_times) / len(embedding_times)
                print(f"\n⏱️ Average Embedding Time: {avg_time:.0f}ms")
                
                # Test similarity search
                print(f"\n🔍 Testing Similarity Search:")
                test_query = "network security"
                search_start = time.time()
                
                # Use embedder to generate query embedding
                query_embedding = embedder.embed_query(test_query)
                vector_ids, scores = vector_store.search(query_embedding, k=5)
                
                search_time = (time.time() - search_start) * 1000
                
                print(f"   Query: '{test_query}'")
                print(f"   Results: {len(vector_ids)} vectors")
                print(f"   Search Time: {search_time:.0f}ms")
                if scores:
                    print(f"   Best Score: {min(scores):.3f}")
                    print(f"   Worst Score: {max(scores):.3f}")
            
            return {
                "vector_stats": stats,
                "average_embedding_time_ms": avg_time if 'avg_time' in locals() else 0,
                "search_time_ms": search_time if 'search_time' in locals() else 0,
                "sample_size": sample_size
            }
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error analyzing embeddings: {e}{Style.RESET_ALL}")
            return {}

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Vector Store Management Tool")
    parser.add_argument('--url', default='http://localhost:8000', help='RAG system base URL')
    parser.add_argument('--api-key', help='API key for authentication')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Overview command
    overview_parser = subparsers.add_parser('overview', help='Show system overview')
    
    # List commands
    list_parser = subparsers.add_parser('list', help='List items')
    list_subparsers = list_parser.add_subparsers(dest='list_type')
    
    docs_parser = list_subparsers.add_parser('docs', help='List documents')
    docs_parser.add_argument('--limit', type=int, help='Limit number of results')
    docs_parser.add_argument('--search', help='Search term')
    
    chunks_parser = list_subparsers.add_parser('chunks', help='List chunks')
    chunks_parser.add_argument('--limit', type=int, default=20, help='Limit number of results')
    chunks_parser.add_argument('--source-type', help='Filter by source type')
    chunks_parser.add_argument('--source-id', help='Filter by source ID')
    
    # View commands
    view_parser = subparsers.add_parser('view', help='View item details')
    view_parser.add_argument('type', choices=['doc', 'chunk'], help='Item type')
    view_parser.add_argument('id', help='Item ID')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search vectors')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--k', type=int, default=10, help='Number of results')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete document')
    delete_parser.add_argument('file_id', help='File ID to delete')
    delete_parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up orphaned data')
    cleanup_parser.add_argument('--no-dry-run', action='store_true', help='Actually perform cleanup')
    
    # Export command
    export_parser = subparsers.add_parser('