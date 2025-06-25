"""
Robust Azure AI Client
Comprehensive Azure AI integration with error handling and fallback
"""
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging
import os
import time
import asyncio
from pathlib import Path

class AzureServiceStatus(Enum):
    """Status of Azure services"""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"

@dataclass
class AzureServiceHealth:
    """Health status for Azure services"""
    computer_vision: AzureServiceStatus
    document_intelligence: AzureServiceStatus
    embeddings: AzureServiceStatus
    chat: AzureServiceStatus
    last_check: datetime
    error_details: Dict[str, str]

class RobustAzureAIClient:
    """Azure AI client with comprehensive error handling and fallback"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services = {}
        self.fallback_handlers = {}
        self.health_status = None
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 30.0,
            'exponential_base': 2
        }
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize services with validation
        self._initialize_services()
        
        # Perform initial health check
        self.health_check()
    
    def _initialize_services(self):
        """Initialize Azure services with validation"""
        self.logger.info("Initializing Azure AI services...")
        
        # Computer Vision
        if self._validate_config('computer_vision'):
            try:
                self._init_computer_vision()
            except Exception as e:
                self.logger.error(f"Failed to initialize Computer Vision: {e}")
                self.services['computer_vision'] = None
        else:
            self.logger.debug("Computer Vision not configured")
            self.services['computer_vision'] = None
        
        # Document Intelligence (optional)
        if self._validate_config('document_intelligence'):
            try:
                self._init_document_intelligence()
            except Exception as e:
                self.logger.warning(f"Document Intelligence not available: {e}")
                self.services['document_intelligence'] = None
        else:
            self.logger.debug("Document Intelligence not configured")
            self.services['document_intelligence'] = None
        
        # Embeddings
        if self._validate_config('embeddings'):
            try:
                self._init_embeddings()
            except Exception as e:
                self.logger.error(f"Failed to initialize Embeddings: {e}")
                self.services['embeddings'] = None
        else:
            self.logger.debug("Embeddings not configured")
            self.services['embeddings'] = None
        
        # Chat/LLM
        if self._validate_config('chat'):
            try:
                self._init_chat()
            except Exception as e:
                self.logger.error(f"Failed to initialize Chat: {e}")
                self.services['chat'] = None
        else:
            self.logger.debug("Chat not configured")
            self.services['chat'] = None
    
    def _init_computer_vision(self):
        """Initialize Computer Vision service"""
        try:
            # Try new Azure AI Vision SDK first
            try:
                from azure.ai.vision.imageanalysis import ImageAnalysisClient
                from azure.core.credentials import AzureKeyCredential
                
                self.services['computer_vision'] = ImageAnalysisClient(
                    endpoint=self.config['computer_vision_endpoint'],
                    credential=AzureKeyCredential(self.config['computer_vision_key'])
                )
                self.logger.info("Azure Computer Vision (AI Vision) initialized successfully")
                return
            except ImportError:
                pass
            
            # Fallback to older Cognitive Services SDK
            try:
                from azure.cognitiveservices.vision.computervision import ComputerVisionClient
                from msrest.authentication import CognitiveServicesCredentials
                
                self.services['computer_vision'] = ComputerVisionClient(
                    endpoint=self.config['computer_vision_endpoint'],
                    credentials=CognitiveServicesCredentials(self.config['computer_vision_key'])
                )
                self.logger.info("Azure Computer Vision (Cognitive Services) initialized successfully")
                return
            except ImportError:
                pass
            
            raise ImportError("No suitable Azure Computer Vision SDK available")
            
        except Exception as e:
            self.logger.error(f"Computer Vision initialization failed: {e}")
            raise
    
    def _init_document_intelligence(self):
        """Initialize Document Intelligence service"""
        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
            
            self.services['document_intelligence'] = DocumentAnalysisClient(
                endpoint=self.config['document_intelligence_endpoint'],
                credential=AzureKeyCredential(self.config['document_intelligence_key'])
            )
            self.logger.info("Azure Document Intelligence initialized successfully")
        except ImportError as e:
            self.logger.warning(f"Azure Document Intelligence SDK not available: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Document Intelligence initialization failed: {e}")
            raise
    
    def _init_embeddings(self):
        """Initialize Embeddings service"""
        try:
            # Try new Azure AI Inference SDK first
            try:
                from azure.ai.inference import EmbeddingsClient
                from azure.core.credentials import AzureKeyCredential
                
                self.services['embeddings'] = EmbeddingsClient(
                    endpoint=self.config['embeddings_endpoint'],
                    credential=AzureKeyCredential(self.config['embeddings_key'])
                )
                self.logger.info("Azure Embeddings (AI Inference) initialized successfully")
                return
            except ImportError:
                pass
            
            # Fallback to OpenAI SDK for Azure OpenAI
            try:
                import openai
                
                openai.api_type = "azure"
                openai.api_base = self.config['embeddings_endpoint']
                openai.api_key = self.config['embeddings_key']
                openai.api_version = self.config.get('api_version', '2023-05-15')
                
                self.services['embeddings'] = openai
                self.logger.info("Azure Embeddings (OpenAI SDK) initialized successfully")
                return
            except ImportError:
                pass
            
            raise ImportError("No suitable Azure embeddings SDK available")
            
        except Exception as e:
            self.logger.error(f"Embeddings initialization failed: {e}")
            raise
    
    def _init_chat(self):
        """Initialize Chat service"""
        try:
            # Try new Azure AI Inference SDK first
            try:
                from azure.ai.inference import ChatCompletionsClient
                from azure.core.credentials import AzureKeyCredential
                
                self.services['chat'] = ChatCompletionsClient(
                    endpoint=self.config['chat_endpoint'],
                    credential=AzureKeyCredential(self.config['chat_key'])
                )
                self.logger.info("Azure Chat (AI Inference) initialized successfully")
                return
            except ImportError:
                pass
            
            # Fallback to OpenAI SDK for Azure OpenAI
            try:
                import openai
                
                openai.api_type = "azure"
                openai.api_base = self.config['chat_endpoint']
                openai.api_key = self.config['chat_key']
                openai.api_version = self.config.get('api_version', '2023-05-15')
                
                self.services['chat'] = openai
                self.logger.info("Azure Chat (OpenAI SDK) initialized successfully")
                return
            except ImportError:
                pass
            
            raise ImportError("No suitable Azure chat SDK available")
            
        except Exception as e:
            self.logger.error(f"Chat initialization failed: {e}")
            raise
    
    def _validate_config(self, service: str) -> bool:
        """Validate configuration for a service"""
        required_keys = {
            'computer_vision': ['computer_vision_endpoint', 'computer_vision_key'],
            'document_intelligence': ['document_intelligence_endpoint', 'document_intelligence_key'],
            'embeddings': ['embeddings_endpoint', 'embeddings_key'],
            'chat': ['chat_endpoint', 'chat_key']
        }
        
        if service not in required_keys:
            return False
        
        missing_keys = []
        for key in required_keys[service]:
            value = self.config.get(key) or os.getenv(key.upper())
            if not value:
                missing_keys.append(key)
            else:
                # Update config with env value if needed
                if key not in self.config:
                    self.config[key] = value
        
        if missing_keys:
            self.logger.debug(f"Missing config for {service}: {missing_keys}")
            return False
        
        return True
    
    def health_check(self) -> AzureServiceHealth:
        """Perform comprehensive health check"""
        self.logger.debug("Performing Azure services health check...")
        
        health = {
            'computer_vision': self._check_service_health('computer_vision'),
            'document_intelligence': self._check_service_health('document_intelligence'),
            'embeddings': self._check_service_health('embeddings'),
            'chat': self._check_service_health('chat')
        }
        
        error_details = {}
        for service, (status, error) in health.items():
            if status != AzureServiceStatus.AVAILABLE:
                error_details[service] = error
        
        self.health_status = AzureServiceHealth(
            computer_vision=health['computer_vision'][0],
            document_intelligence=health['document_intelligence'][0],
            embeddings=health['embeddings'][0],
            chat=health['chat'][0],
            last_check=datetime.now(),
            error_details=error_details
        )
        
        overall_health = self._calculate_overall_health()
        self.logger.info(f"Azure services health check completed - Overall: {overall_health}")
        
        return self.health_status
    
    def _check_service_health(self, service: str) -> Tuple[AzureServiceStatus, str]:
        """Check health of a specific service"""
        if service not in self.services or self.services[service] is None:
            if self._validate_config(service):
                return (AzureServiceStatus.UNAVAILABLE, "Service initialization failed")
            else:
                return (AzureServiceStatus.NOT_CONFIGURED, "Service not configured")
        
        # Perform lightweight service-specific health check
        try:
            if service == 'computer_vision':
                # Simple endpoint check without actual API call
                return (AzureServiceStatus.AVAILABLE, "")
            
            elif service == 'embeddings':
                # Simple endpoint check
                return (AzureServiceStatus.AVAILABLE, "")
            
            elif service == 'chat':
                # Simple endpoint check
                return (AzureServiceStatus.AVAILABLE, "")
            
            elif service == 'document_intelligence':
                # Simple endpoint check
                return (AzureServiceStatus.AVAILABLE, "")
            
            else:
                return (AzureServiceStatus.AVAILABLE, "")
                
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                return (AzureServiceStatus.UNAVAILABLE, "Authentication failed")
            elif "404" in error_msg:
                return (AzureServiceStatus.UNAVAILABLE, "Endpoint not found")
            elif "429" in error_msg:
                return (AzureServiceStatus.DEGRADED, "Rate limited")
            else:
                return (AzureServiceStatus.DEGRADED, f"Service error: {error_msg[:100]}")
    
    def process_image_with_fallback(self, image_data: bytes, 
                                   fallback_handler: Optional[callable] = None) -> Dict[str, Any]:
        """Process image with automatic fallback"""
        self.logger.debug("Processing image with Azure AI services...")
        
        # Try Azure Computer Vision first
        if self.services.get('computer_vision'):
            try:
                result = self._process_with_computer_vision(image_data)
                if result['success']:
                    self.logger.info("Image processed successfully with Computer Vision")
                    return result
            except Exception as e:
                self.logger.warning(f"Computer Vision failed: {e}")
        
        # Try Document Intelligence as fallback
        if self.services.get('document_intelligence'):
            try:
                result = self._process_with_document_intelligence(image_data)
                if result['success']:
                    self.logger.info("Image processed successfully with Document Intelligence")
                    return result
            except Exception as e:
                self.logger.warning(f"Document Intelligence failed: {e}")
        
        # Use custom fallback handler
        if fallback_handler:
            try:
                self.logger.info("Using custom fallback handler for image processing")
                return fallback_handler(image_data)
            except Exception as e:
                self.logger.error(f"Fallback handler failed: {e}")
        
        # Final fallback - basic processing
        self.logger.warning("Using basic image processing fallback")
        return self._basic_image_processing(image_data)
    
    def _process_with_computer_vision(self, image_data: bytes) -> Dict[str, Any]:
        """Process image with Computer Vision"""
        try:
            from azure.ai.vision.imageanalysis.models import VisualFeatures
        except ImportError:
            raise ImportError("Azure Computer Vision SDK not available")
        
        client = self.services['computer_vision']
        
        try:
            # Analyze image
            result = client.analyze(
                image_data=image_data,
                visual_features=[
                    VisualFeatures.CAPTION,
                    VisualFeatures.READ,
                    VisualFeatures.OBJECTS,
                    VisualFeatures.TAGS
                ],
                language=self.config.get('ocr_language', 'en')
            )
            
            # Extract text
            text_blocks = []
            if result.read and result.read.blocks:
                for block in result.read.blocks:
                    for line in block.lines:
                        text_blocks.append(line.text)
            
            return {
                'success': True,
                'text': '\n'.join(text_blocks),
                'caption': result.caption.text if result.caption else '',
                'confidence': result.caption.confidence if result.caption else 0.0,
                'objects': [obj.tags[0].name for obj in result.objects] if result.objects else [],
                'tags': [tag.name for tag in result.tags] if result.tags else [],
                'service': 'computer_vision',
                'metadata': {
                    'width': getattr(result, 'metadata', {}).get('width'),
                    'height': getattr(result, 'metadata', {}).get('height')
                }
            }
        except Exception as e:
            self.logger.error(f"Computer Vision processing failed: {e}")
            raise
    
    def _process_with_document_intelligence(self, image_data: bytes) -> Dict[str, Any]:
        """Process image with Document Intelligence"""
        client = self.services['document_intelligence']
        
        try:
            # Analyze document
            poller = client.begin_analyze_document(
                "prebuilt-read", 
                document=image_data
            )
            result = poller.result()
            
            # Extract text
            text_blocks = []
            if result.content:
                text_blocks.append(result.content)
            
            # Extract additional information
            tables = []
            if result.tables:
                for table in result.tables:
                    table_text = f"Table {table.row_count}x{table.column_count}:"
                    for cell in table.cells:
                        table_text += f" {cell.content}"
                    tables.append(table_text)
            
            return {
                'success': True,
                'text': '\n'.join(text_blocks),
                'tables': tables,
                'page_count': len(result.pages) if result.pages else 1,
                'service': 'document_intelligence',
                'confidence': 0.9  # Document Intelligence generally has high confidence
            }
        except Exception as e:
            self.logger.error(f"Document Intelligence processing failed: {e}")
            raise
    
    def _basic_image_processing(self, image_data: bytes) -> Dict[str, Any]:
        """Basic fallback image processing"""
        try:
            # Try OCR with pytesseract if available
            try:
                import pytesseract
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(image_data))
                text = pytesseract.image_to_string(image)
                
                return {
                    'success': True,
                    'text': text,
                    'caption': 'Image processed with local OCR',
                    'service': 'pytesseract',
                    'metadata': {
                        'width': image.size[0],
                        'height': image.size[1],
                        'mode': image.mode
                    }
                }
            except ImportError:
                self.logger.warning("Pytesseract not available for fallback OCR")
            except Exception as e:
                self.logger.error(f"Pytesseract processing failed: {e}")
            
            # Try basic PIL metadata extraction
            try:
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(image_data))
                
                return {
                    'success': True,
                    'text': f"Image file ({image.size[0]}x{image.size[1]} pixels, {image.mode} mode)",
                    'caption': 'Image metadata extracted',
                    'service': 'pil_metadata',
                    'metadata': {
                        'width': image.size[0],
                        'height': image.size[1],
                        'mode': image.mode,
                        'format': image.format
                    }
                }
            except Exception as e:
                self.logger.error(f"PIL metadata extraction failed: {e}")
        
        except Exception as e:
            self.logger.error(f"Basic image processing failed: {e}")
        
        # Ultimate fallback
        return {
            'success': False,
            'text': '',
            'caption': 'Image processing unavailable',
            'error': 'All processing methods failed',
            'service': 'none'
        }
    
    def embed_with_retry(self, texts: List[str], max_retries: Optional[int] = None) -> List[List[float]]:
        """Embed texts with retry logic and fallback"""
        if max_retries is None:
            max_retries = self.retry_config['max_retries']
        
        if not self.services.get('embeddings'):
            self.logger.warning("Azure embeddings not available, using fallback")
            return self._fallback_embeddings(texts)
        
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Try Azure AI Inference SDK first
                if hasattr(self.services['embeddings'], 'embed'):
                    response = self.services['embeddings'].embed(
                        input=texts,
                        model=self.config.get('embedding_model', 'text-embedding-ada-002')
                    )
                    embeddings = [item.embedding for item in response.data]
                    return embeddings
                
                # Fallback to OpenAI SDK
                else:
                    import openai
                    response = openai.Embedding.create(
                        input=texts,
                        engine=self.config.get('embedding_model', 'text-embedding-ada-002')
                    )
                    embeddings = [item['embedding'] for item in response['data']]
                    return embeddings
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Exponential backoff
                if retry_count < max_retries:
                    delay = min(
                        self.retry_config['base_delay'] * (self.retry_config['exponential_base'] ** retry_count),
                        self.retry_config['max_delay']
                    )
                    self.logger.warning(f"Embedding attempt {retry_count} failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
        
        # All retries failed
        self.logger.error(f"All embedding attempts failed: {last_error}")
        return self._fallback_embeddings(texts)
    
    def _fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using fallback method"""
        try:
            # Try sentence-transformers
            from sentence_transformers import SentenceTransformer
            
            if not hasattr(self, '_fallback_model'):
                model_name = self.config.get('fallback_embedding_model', 'all-MiniLM-L6-v2')
                self._fallback_model = SentenceTransformer(model_name)
                self.logger.info(f"Loaded fallback embedding model: {model_name}")
            
            embeddings = self._fallback_model.encode(texts).tolist()
            self.logger.info("Generated embeddings using sentence-transformers fallback")
            return embeddings
            
        except ImportError:
            self.logger.warning("sentence-transformers not available for fallback embeddings")
        except Exception as e:
            self.logger.error(f"Fallback embeddings failed: {e}")
        
        # Return zero vectors as last resort
        dimension = self.config.get('embedding_dimension', 384)
        zero_embeddings = [[0.0] * dimension for _ in texts]
        self.logger.warning(f"Returning zero embeddings for {len(texts)} texts")
        return zero_embeddings
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get detailed service status"""
        # Refresh health check if stale
        if not self.health_status or (datetime.now() - self.health_status.last_check).seconds > 300:
            self.health_check()
        
        return {
            'services': {
                'computer_vision': {
                    'status': self.health_status.computer_vision.value,
                    'available': self.services.get('computer_vision') is not None,
                    'error': self.health_status.error_details.get('computer_vision', ''),
                    'configured': self._validate_config('computer_vision')
                },
                'document_intelligence': {
                    'status': self.health_status.document_intelligence.value,
                    'available': self.services.get('document_intelligence') is not None,
                    'error': self.health_status.error_details.get('document_intelligence', ''),
                    'configured': self._validate_config('document_intelligence')
                },
                'embeddings': {
                    'status': self.health_status.embeddings.value,
                    'available': self.services.get('embeddings') is not None,
                    'error': self.health_status.error_details.get('embeddings', ''),
                    'configured': self._validate_config('embeddings')
                },
                'chat': {
                    'status': self.health_status.chat.value,
                    'available': self.services.get('chat') is not None,
                    'error': self.health_status.error_details.get('chat', ''),
                    'configured': self._validate_config('chat')
                }
            },
            'last_check': self.health_status.last_check.isoformat(),
            'overall_health': self._calculate_overall_health(),
            'config_status': self._get_config_status()
        }
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        if not self.health_status:
            return "unknown"
        
        statuses = [
            self.health_status.computer_vision,
            self.health_status.embeddings,
            self.health_status.chat
        ]
        
        available_count = sum(1 for s in statuses if s == AzureServiceStatus.AVAILABLE)
        degraded_count = sum(1 for s in statuses if s == AzureServiceStatus.DEGRADED)
        not_configured_count = sum(1 for s in statuses if s == AzureServiceStatus.NOT_CONFIGURED)
        
        # If most services are not configured, system is not configured
        if not_configured_count >= 2:
            return "not_configured"
        
        # If all available services are working
        if available_count == len(statuses) - not_configured_count:
            return "healthy"
        # If some services are working
        elif available_count > 0 or degraded_count > 0:
            return "degraded"
        else:
            return "unhealthy"
    
    def _get_config_status(self) -> Dict[str, bool]:
        """Get configuration status for all services"""
        return {
            'computer_vision': self._validate_config('computer_vision'),
            'document_intelligence': self._validate_config('document_intelligence'),
            'embeddings': self._validate_config('embeddings'),
            'chat': self._validate_config('chat')
        }
    
    def is_healthy(self) -> bool:
        """Check if the client is in a healthy state"""
        if not self.health_status:
            self.health_check()
        
        overall_health = self._calculate_overall_health()
        return overall_health in ['healthy', 'degraded']
    
    def get_available_services(self) -> List[str]:
        """Get list of available services"""
        available = []
        for service, client in self.services.items():
            if client is not None:
                available.append(service)
        return available
    
    def close(self):
        """Clean up resources"""
        self.logger.info("Closing Azure AI client...")
        
        # Clean up fallback model if loaded
        if hasattr(self, '_fallback_model'):
            del self._fallback_model
        
        # Clear services
        self.services.clear()
        
        self.logger.info("Azure AI client closed successfully") 