"""
Azure AI Configuration Validator
Validates and fixes Azure AI configuration issues
"""
import os
import logging
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

class AzureAIConfigValidator:
    """Validate and fix Azure AI configuration"""
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        'AZURE_CV_ENDPOINT': 'computer_vision_endpoint',
        'AZURE_COMPUTER_VISION_ENDPOINT': 'computer_vision_endpoint',
        'AZURE_CV_KEY': 'computer_vision_key',
        'AZURE_COMPUTER_VISION_KEY': 'computer_vision_key',
        'AZURE_DI_ENDPOINT': 'document_intelligence_endpoint',
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': 'document_intelligence_endpoint',
        'AZURE_DI_KEY': 'document_intelligence_key',
        'AZURE_DOCUMENT_INTELLIGENCE_KEY': 'document_intelligence_key',
        'AZURE_EMBEDDINGS_ENDPOINT': 'embeddings_endpoint',
        'AZURE_OPENAI_ENDPOINT': 'embeddings_endpoint',
        'AZURE_EMBEDDINGS_KEY': 'embeddings_key',
        'AZURE_OPENAI_KEY': 'embeddings_key',
        'AZURE_API_KEY': 'embeddings_key',
        'AZURE_CHAT_ENDPOINT': 'chat_endpoint',
        'AZURE_CHAT_KEY': 'chat_key',
        'AZURE_API_VERSION': 'api_version',
        'AZURE_EMBEDDING_MODEL': 'embedding_model',
        'AZURE_CHAT_MODEL': 'chat_model'
    }
    
    # Required configurations for each service
    REQUIRED_CONFIGS = {
        'computer_vision': ['computer_vision_endpoint', 'computer_vision_key'],
        'document_intelligence': ['document_intelligence_endpoint', 'document_intelligence_key'],
        'embeddings': ['embeddings_endpoint', 'embeddings_key'],
        'chat': ['chat_endpoint', 'chat_key']
    }
    
    # Default values
    DEFAULTS = {
        'api_version': '2023-05-15',
        'embedding_model': 'text-embedding-ada-002',
        'chat_model': 'gpt-35-turbo',
        'ocr_language': 'en',
        'enable_handwriting': True,
        'max_image_size_mb': 20,
        'fallback_embedding_model': 'all-MiniLM-L6-v2',
        'embedding_dimension': 1536
    }
    
    @classmethod
    def validate_and_fix(cls, config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Validate configuration and apply fixes"""
        fixed_config = config.copy() if config else {}
        issues = []
        
        # Apply environment variables
        env_issues = cls._apply_environment_variables(fixed_config)
        issues.extend(env_issues)
        
        # Apply defaults
        default_issues = cls._apply_defaults(fixed_config)
        issues.extend(default_issues)
        
        # Validate and fix endpoints
        endpoint_issues = cls._validate_and_fix_endpoints(fixed_config)
        issues.extend(endpoint_issues)
        
        # Validate keys
        key_issues = cls._validate_keys(fixed_config)
        issues.extend(key_issues)
        
        # Check service completeness
        service_issues = cls._check_service_completeness(fixed_config)
        issues.extend(service_issues)
        
        # Log issues
        if issues:
            logging.info(f"Azure AI configuration fixes applied: {len(issues)} issues resolved")
            for issue in issues:
                logging.debug(f"Config fix: {issue}")
        
        return fixed_config, issues
    
    @classmethod
    def _apply_environment_variables(cls, config: Dict[str, Any]) -> List[str]:
        """Apply environment variables to configuration"""
        issues = []
        
        for env_key, config_key in cls.ENV_MAPPINGS.items():
            env_value = os.getenv(env_key)
            if env_value:
                if not config.get(config_key):
                    config[config_key] = env_value
                    issues.append(f"Added {config_key} from environment variable {env_key}")
                elif config[config_key] != env_value:
                    # Environment variable takes precedence
                    old_value = config[config_key]
                    config[config_key] = env_value
                    issues.append(f"Overrode {config_key} with environment variable {env_key}")
        
        return issues
    
    @classmethod
    def _apply_defaults(cls, config: Dict[str, Any]) -> List[str]:
        """Apply default values to configuration"""
        issues = []
        
        for key, default_value in cls.DEFAULTS.items():
            if key not in config or not config[key]:
                config[key] = default_value
                issues.append(f"Applied default value for {key}: {default_value}")
        
        return issues
    
    @classmethod
    def _validate_and_fix_endpoints(cls, config: Dict[str, Any]) -> List[str]:
        """Validate and fix endpoint URLs"""
        issues = []
        
        endpoint_keys = [
            'computer_vision_endpoint',
            'document_intelligence_endpoint', 
            'embeddings_endpoint',
            'chat_endpoint'
        ]
        
        for key in endpoint_keys:
            if key in config and config[key]:
                endpoint = config[key]
                original_endpoint = endpoint
                
                # Ensure https protocol
                if not endpoint.startswith(('http://', 'https://')):
                    endpoint = f"https://{endpoint}"
                    issues.append(f"Added https:// protocol to {key}")
                
                # Parse URL to validate
                try:
                    parsed = urlparse(endpoint)
                    if not parsed.netloc:
                        issues.append(f"Invalid endpoint format for {key}: {endpoint}")
                        continue
                    
                    # Ensure proper Azure endpoint format
                    if 'azure' in parsed.netloc.lower():
                        # Azure endpoints should end with /
                        if not endpoint.endswith('/'):
                            endpoint = f"{endpoint}/"
                            issues.append(f"Added trailing slash to Azure endpoint {key}")
                        
                        # Check for common Azure endpoint patterns
                        if 'cognitiveservices' in parsed.netloc and 'vision' in key:
                            # Computer Vision endpoint
                            if not endpoint.endswith('/vision/'):
                                if endpoint.endswith('/'):
                                    endpoint = f"{endpoint}vision/"
                                else:
                                    endpoint = f"{endpoint}/vision/"
                                issues.append(f"Fixed Computer Vision endpoint path for {key}")
                        
                        elif 'openai' in parsed.netloc:
                            # Azure OpenAI endpoint
                            if not endpoint.endswith('/openai/'):
                                if endpoint.endswith('/'):
                                    endpoint = f"{endpoint}openai/"
                                else:
                                    endpoint = f"{endpoint}/openai/"
                                issues.append(f"Fixed Azure OpenAI endpoint path for {key}")
                
                except Exception as e:
                    issues.append(f"Failed to parse endpoint {key}: {e}")
                    continue
                
                # Update config if changed
                if endpoint != original_endpoint:
                    config[key] = endpoint
        
        return issues
    
    @classmethod
    def _validate_keys(cls, config: Dict[str, Any]) -> List[str]:
        """Validate API keys"""
        issues = []
        
        key_fields = [
            'computer_vision_key',
            'document_intelligence_key',
            'embeddings_key',
            'chat_key'
        ]
        
        for key_field in key_fields:
            if key_field in config and config[key_field]:
                key_value = config[key_field]
                
                # Check key format
                if len(key_value) < 10:
                    issues.append(f"API key {key_field} appears too short (length: {len(key_value)})")
                
                # Check for common key format patterns
                if not any(c.isalnum() for c in key_value):
                    issues.append(f"API key {key_field} contains no alphanumeric characters")
                
                # Mask key in logs
                masked_key = key_value[:4] + '*' * (len(key_value) - 8) + key_value[-4:] if len(key_value) > 8 else '*' * len(key_value)
                logging.debug(f"Validated API key {key_field}: {masked_key}")
        
        return issues
    
    @classmethod
    def _check_service_completeness(cls, config: Dict[str, Any]) -> List[str]:
        """Check if services have complete configuration"""
        issues = []
        
        for service, required_keys in cls.REQUIRED_CONFIGS.items():
            missing_keys = []
            for key in required_keys:
                if not config.get(key):
                    missing_keys.append(key)
            
            if missing_keys:
                issues.append(f"Service {service} incomplete - missing: {', '.join(missing_keys)}")
            else:
                issues.append(f"Service {service} configuration complete")
        
        return issues
    
    @classmethod
    def get_configuration_status(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed configuration status"""
        status = {
            'services': {},
            'environment_variables': {},
            'issues': []
        }
        
        # Check each service
        for service, required_keys in cls.REQUIRED_CONFIGS.items():
            service_status = {
                'configured': True,
                'missing_keys': [],
                'present_keys': []
            }
            
            for key in required_keys:
                if config.get(key):
                    service_status['present_keys'].append(key)
                else:
                    service_status['missing_keys'].append(key)
                    service_status['configured'] = False
            
            status['services'][service] = service_status
        
        # Check environment variables
        for env_key, config_key in cls.ENV_MAPPINGS.items():
            env_value = os.getenv(env_key)
            status['environment_variables'][env_key] = {
                'present': env_value is not None,
                'maps_to': config_key,
                'used_in_config': config.get(config_key) == env_value if env_value else False
            }
        
        # Overall status
        configured_services = sum(1 for s in status['services'].values() if s['configured'])
        total_services = len(status['services'])
        
        status['overall'] = {
            'configured_services': configured_services,
            'total_services': total_services,
            'configuration_complete': configured_services > 0,
            'all_services_configured': configured_services == total_services
        }
        
        return status
    
    @classmethod
    def create_sample_config(cls) -> Dict[str, Any]:
        """Create a sample configuration with placeholders"""
        return {
            # Computer Vision
            'computer_vision_endpoint': 'https://your-cv-resource.cognitiveservices.azure.com/vision/',
            'computer_vision_key': 'your-computer-vision-key',
            
            # Document Intelligence (optional)
            'document_intelligence_endpoint': 'https://your-di-resource.cognitiveservices.azure.com/',
            'document_intelligence_key': 'your-document-intelligence-key',
            
            # Azure OpenAI for embeddings
            'embeddings_endpoint': 'https://your-openai-resource.openai.azure.com/openai/',
            'embeddings_key': 'your-azure-openai-key',
            'embedding_model': 'text-embedding-ada-002',
            
            # Azure OpenAI for chat
            'chat_endpoint': 'https://your-openai-resource.openai.azure.com/openai/',
            'chat_key': 'your-azure-openai-key',
            'chat_model': 'gpt-35-turbo',
            
            # Common settings
            'api_version': '2023-05-15',
            'ocr_language': 'en',
            'enable_handwriting': True,
            'max_image_size_mb': 20,
            
            # Fallback settings
            'fallback_embedding_model': 'all-MiniLM-L6-v2',
            'embedding_dimension': 1536
        }
    
    @classmethod
    def generate_env_file_template(cls) -> str:
        """Generate a .env file template"""
        template = """# Azure AI Configuration
# Copy this template to .env and fill in your actual values

# Computer Vision
AZURE_COMPUTER_VISION_ENDPOINT=https://your-cv-resource.cognitiveservices.azure.com/vision/
AZURE_COMPUTER_VISION_KEY=your-computer-vision-key

# Document Intelligence (optional)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-di-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-document-intelligence-key

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/openai/
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_API_VERSION=2023-05-15

# Models
AZURE_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_CHAT_MODEL=gpt-35-turbo

# OCR Settings
AZURE_OCR_LANGUAGE=en
AZURE_ENABLE_HANDWRITING=true
AZURE_MAX_IMAGE_SIZE_MB=20
"""
        return template 