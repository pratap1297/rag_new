import os
import gradio as gr
import base64
import json
import requests
from PIL import Image
import io
import logging
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import sys

# Set default environment variables from .env configuration
os.environ.setdefault('AZURE_API_KEY', '6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr')
os.environ.setdefault('AZURE_CHAT_ENDPOINT', 'https://azurehub1910875317.services.ai.azure.com/models')
os.environ.setdefault('AZURE_EMBEDDINGS_ENDPOINT', 'https://azurehub1910875317.services.ai.azure.com/models')
os.environ.setdefault('COMPUTER_VISION_KEY', 'FSf3hSW3ogphcme0MgMMKZNTzkQTXo6sNikmlyUhSqahBHgnoaOFJQQJ99BFACYeBjFXJ3w3AAAFACOGPuhx')
os.environ.setdefault('COMPUTER_VISION_ENDPOINT', 'https://computervision1298.cognitiveservices.azure.com/')
os.environ.setdefault('COMPUTER_VISION_REGION', 'eastus')
os.environ.setdefault('CHAT_MODEL', 'Llama-4-Maverick-17B-128E-Instruct-FP8')
os.environ.setdefault('EMBEDDING_MODEL', 'Cohere-embed-v3-english')

# Also set the alternative environment variable names for compatibility
os.environ.setdefault('AZURE_CV_KEY', os.environ['COMPUTER_VISION_KEY'])
os.environ.setdefault('AZURE_CV_ENDPOINT', os.environ['COMPUTER_VISION_ENDPOINT'])

# Add the rag_system src to path for imports
current_dir = Path(__file__).parent
rag_src_path = current_dir / "rag_system" / "src"
if rag_src_path.exists():
    sys.path.insert(0, str(rag_src_path))

# Import from existing RAG system
try:
    from integrations.azure_ai.azure_client import AzureAIClient
    from retrieval.llm_client import LLMClient
    from core.config_manager import ConfigManager
    RAG_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"RAG system imports not available: {e}")
    RAG_IMPORTS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageAnalyzer:
    def __init__(self):
        """Initialize Image Analyzer with Azure services"""
        self.azure_client = None
        self.llm_client = None
        self._initialize_services()
        
    def _initialize_services(self):
        """Initialize Azure Computer Vision and LLM services"""
        if RAG_IMPORTS_AVAILABLE:
            try:
                # Initialize configuration manager
                config_manager = ConfigManager()
                
                # Initialize Azure Computer Vision client
                azure_ai_config = config_manager.get_config('azure_ai')
                if azure_ai_config and azure_ai_config.computer_vision_endpoint and azure_ai_config.computer_vision_key:
                    self.azure_client = AzureAIClient({
                        'computer_vision_endpoint': azure_ai_config.computer_vision_endpoint,
                        'computer_vision_key': azure_ai_config.computer_vision_key,
                        'document_intelligence_endpoint': azure_ai_config.document_intelligence_endpoint,
                        'document_intelligence_key': azure_ai_config.document_intelligence_key,
                        'max_image_size_mb': azure_ai_config.max_image_size_mb,
                        'ocr_language': azure_ai_config.ocr_language,
                        'enable_handwriting': azure_ai_config.enable_handwriting
                    })
                    logger.info("Azure Computer Vision client initialized successfully")
                else:
                    logger.warning("Azure Computer Vision not configured")
                
                # Initialize LLM client
                llm_config = config_manager.get_config('llm')
                if llm_config and llm_config.api_key:
                    endpoint = None
                    if llm_config.provider == 'azure':
                        endpoint = os.getenv('AZURE_CHAT_ENDPOINT')
                    
                    self.llm_client = LLMClient(
                        provider=llm_config.provider,
                        model_name=llm_config.model_name,
                        api_key=llm_config.api_key,
                        temperature=llm_config.temperature,
                        max_tokens=llm_config.max_tokens,
                        endpoint=endpoint
                    )
                    logger.info(f"LLM client initialized: {llm_config.provider}")
                else:
                    logger.warning("LLM client not configured")
                    
            except Exception as e:
                logger.error(f"Failed to initialize services from config: {e}")
                self._fallback_initialization()
        else:
            self._fallback_initialization()
    
    def _fallback_initialization(self):
        """Fallback initialization using environment variables directly"""
        logger.info("Using fallback initialization with environment variables")
        
        # Initialize Azure Computer Vision with fallback
        cv_endpoint = os.getenv('AZURE_CV_ENDPOINT') or os.getenv('COMPUTER_VISION_ENDPOINT')
        cv_key = os.getenv('AZURE_CV_KEY') or os.getenv('COMPUTER_VISION_KEY')
        
        if cv_endpoint and cv_key:
            try:
                if RAG_IMPORTS_AVAILABLE:
                    self.azure_client = AzureAIClient({
                        'computer_vision_endpoint': cv_endpoint,
                        'computer_vision_key': cv_key,
                        'max_image_size_mb': 4,
                        'ocr_language': 'en',
                        'enable_handwriting': True
                    })
                else:
                    # Create a simple fallback class
                    self.azure_client = self._create_fallback_cv_client(cv_endpoint, cv_key)
                logger.info("Azure Computer Vision client initialized (fallback)")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Computer Vision: {e}")
        
        # Initialize LLM client with fallback
        api_key = os.getenv('AZURE_API_KEY')
        endpoint = os.getenv('AZURE_CHAT_ENDPOINT')
        model_name = os.getenv('CHAT_MODEL', 'Llama-4-Maverick-17B-128E-Instruct-FP8')
        
        if api_key and endpoint:
            try:
                if RAG_IMPORTS_AVAILABLE:
                    self.llm_client = LLMClient(
                        provider='azure',
                        model_name=model_name,
                        api_key=api_key,
                        temperature=0.7,
                        max_tokens=2000,
                        endpoint=endpoint
                    )
                else:
                    # Create a simple fallback class
                    self.llm_client = self._create_fallback_llm_client(api_key, endpoint, model_name)
                logger.info("LLM client initialized (fallback)")
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
    
    def _create_fallback_cv_client(self, endpoint: str, key: str):
        """Create a fallback Computer Vision client"""
        class FallbackCVClient:
            def __init__(self, endpoint, key):
                self.endpoint = endpoint
                self.key = key
            
            def analyze_image(self, image_data: bytes, features=None):
                try:
                    # Convert image to bytes for API call
                    analyze_url = f"{self.endpoint}vision/v3.2/analyze"
                    headers = {
                        'Ocp-Apim-Subscription-Key': self.key,
                        'Content-Type': 'application/octet-stream'
                    }
                    params = {
                        'visualFeatures': 'Categories,Description,Objects,Tags,Color,Brands,Faces,ImageType',
                        'details': 'Landmarks'
                    }
                    
                    response = requests.post(analyze_url, headers=headers, params=params, data=image_data)
                    response.raise_for_status()
                    
                    return {
                        'success': True,
                        'analysis': response.json()
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'analysis': {}
                    }
        
        return FallbackCVClient(endpoint, key)
    
    def _create_fallback_llm_client(self, api_key: str, endpoint: str, model_name: str):
        """Create a fallback LLM client"""
        class FallbackLLMClient:
            def __init__(self, api_key, endpoint, model_name):
                self.api_key = api_key
                self.endpoint = endpoint
                self.model_name = model_name
            
            def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7):
                try:
                    # Try to use Azure AI Inference if available
                    try:
                        from azure.ai.inference import ChatCompletionsClient
                        from azure.core.credentials import AzureKeyCredential
                        from azure.ai.inference.models import SystemMessage, UserMessage
                        
                        client = ChatCompletionsClient(
                            endpoint=self.endpoint,
                            credential=AzureKeyCredential(self.api_key),
                            api_version="2024-05-01-preview"
                        )
                        
                        response = client.complete(
                            messages=[
                                SystemMessage(content="You are a helpful assistant."),
                                UserMessage(content=prompt)
                            ],
                            max_tokens=max_tokens,
                            temperature=temperature,
                            model=self.model_name
                        )
                        
                        return response.choices[0].message.content
                        
                    except ImportError:
                        # Fallback to direct API call if Azure AI Inference not available
                        logger.warning("Azure AI Inference library not available, using direct API call")
                        return self._direct_api_call(prompt, max_tokens, temperature)
                        
                except Exception as e:
                    logger.error(f"Azure AI Inference failed: {e}")
                    return self._direct_api_call(prompt, max_tokens, temperature)
            
            def _direct_api_call(self, prompt: str, max_tokens: int, temperature: float):
                """Direct API call as last resort"""
                try:
                    # Use the correct Azure AI endpoint format
                    headers = {
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    payload = {
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful assistant."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "model": self.model_name
                    }
                    
                    # Use the correct endpoint format for Azure AI
                    api_url = f"{self.endpoint}/chat/completions"
                    
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        error_msg = f"API Error: {response.status_code} - {response.text}"
                        logger.error(error_msg)
                        return error_msg
                        
                except Exception as e:
                    error_msg = f"Direct API call failed: {str(e)}"
                    logger.error(error_msg)
                    return error_msg
        
        return FallbackLLMClient(api_key, endpoint, model_name)
        
    def encode_image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def analyze_with_computer_vision(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image using Azure Computer Vision API with enhanced text extraction."""
        if not self.azure_client:
            return {"error": "Azure Computer Vision client not initialized"}
        
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Perform comprehensive analysis
            results = {}
            
            # 1. Visual feature analysis
            visual_analysis = self.azure_client.analyze_image(
                img_byte_arr, 
                features=['Categories', 'Description', 'Objects', 'Tags', 'Color', 'Brands']
            )
            
            if visual_analysis['success']:
                results.update(visual_analysis['analysis'])
            else:
                results['visual_analysis_error'] = visual_analysis.get('error', 'Visual analysis failed')
            
            # 2. OCR text extraction for data extraction
            try:
                ocr_results = self.azure_client.process_image(img_byte_arr, image_type='document')
                if ocr_results['success']:
                    results['ocr_text'] = ocr_results['text']
                    results['ocr_regions'] = ocr_results['regions']
                    results['extracted_data'] = self._extract_network_data(ocr_results['text'])
                else:
                    results['ocr_error'] = ocr_results.get('error', 'OCR failed')
            except Exception as ocr_e:
                results['ocr_error'] = f"OCR processing failed: {str(ocr_e)}"
            
            return results
            
        except Exception as e:
            logger.error(f"Computer Vision analysis error: {e}")
            return {"error": f"Computer Vision analysis failed: {str(e)}"}
    
    def _extract_network_data(self, ocr_text: str) -> Dict[str, Any]:
        """Extract specific network-related data from OCR text."""
        import re
        
        extracted = {
            'ip_addresses': [],
            'mac_addresses': [],
            'model_numbers': [],
            'port_numbers': [],
            'serial_numbers': [],
            'vlan_ids': [],
            'device_labels': [],
            'manufacturers': []
        }
        
        if not ocr_text:
            return extracted
        
        # IP Address patterns
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        extracted['ip_addresses'] = list(set(re.findall(ip_pattern, ocr_text)))
        
        # MAC Address patterns
        mac_pattern = r'\b[0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}\b'
        extracted['mac_addresses'] = list(set(re.findall(mac_pattern, ocr_text)))
        
        # Port numbers (Gi0/1, Fa0/1, etc.)
        port_pattern = r'\b(?:Gi|Fa|Et|Te|Hu)\d+/\d+(?:/\d+)?\b'
        extracted['port_numbers'] = list(set(re.findall(port_pattern, ocr_text, re.IGNORECASE)))
        
        # VLAN IDs
        vlan_pattern = r'\bVLAN\s*(\d+)\b'
        extracted['vlan_ids'] = list(set(re.findall(vlan_pattern, ocr_text, re.IGNORECASE)))
        
        # Serial numbers (common patterns)
        serial_pattern = r'\b(?:S/N|SN|Serial)[:\s]*([A-Z0-9]{8,})\b'
        extracted['serial_numbers'] = list(set(re.findall(serial_pattern, ocr_text, re.IGNORECASE)))
        
        # Common network equipment manufacturers
        manufacturers = ['Cisco', 'Juniper', 'HP', 'Dell', 'Aruba', 'Netgear', 'D-Link', 'TP-Link', 'Ubiquiti', 'Fortinet']
        for manufacturer in manufacturers:
            if manufacturer.lower() in ocr_text.lower():
                extracted['manufacturers'].append(manufacturer)
        
        # Model numbers (alphanumeric patterns that might be models)
        model_pattern = r'\b[A-Z]{2,}\d{2,}[A-Z0-9]*\b'
        potential_models = re.findall(model_pattern, ocr_text)
        extracted['model_numbers'] = list(set(potential_models))
        
        # Device labels (Port labels, interface names)
        label_pattern = r'\b(?:Port|Interface|Eth|Gi|Fa)\s*\d+\b'
        extracted['device_labels'] = list(set(re.findall(label_pattern, ocr_text, re.IGNORECASE)))
        
        return extracted
    
    def analyze_with_llama(self, image: Image.Image, cv_results: Dict[str, Any]) -> str:
        """Analyze image using LLaMA 4 Maverick with both image and Computer Vision context."""
        if not self.llm_client:
            return "LLM client not initialized. Please check your configuration."
        
        try:
            # Create context from Computer Vision results
            cv_context = self.format_cv_results(cv_results)
            
            # Enhanced prompt that references both image and CV analysis
            prompt = f"""You are analyzing a network equipment image. Use both the visual information from the image and the Analysis below to provide a comprehensive assessment.

ANALYSIS:
{cv_context}


Write a concise paragraph mentioning: the main equipment identified, any visible data (IPs, models, ports), whether this appears to be a mesh network setup, and the cable management quality.

Then on a NEW LINE, write:
ACTION REQUIRED: [Yes/No] - Only recommend "Yes - Wires need restructuring" if cables are in TOTALLY BAD SHAPE (severely tangled, creating safety hazards, completely blocking airflow, impossible to trace, or creating major operational risks). For anything less severe, write "No - Current wire organization is acceptable"."""

            # Check if we can use multimodal capabilities
            try:
                # Try to use the image with LLM if supported
                if hasattr(self.llm_client, 'generate_with_image'):
                    response = self.llm_client.generate_with_image(
                        prompt=prompt,
                        image=image,
                        max_tokens=400,
                        temperature=0.1
                    )
                else:
                    # Use Azure AI Inference with image if available
                    if RAG_IMPORTS_AVAILABLE:
                        response = self._generate_with_image_azure(prompt, image)
                    else:
                        response = self._generate_with_image_fallback(prompt, image)
            except Exception as e:
                logger.warning(f"Multimodal generation failed, using text-only: {e}")
                # Fallback to text-only analysis
                response = self.llm_client.generate(
                    prompt, 
                    max_tokens=400,
                    temperature=0.1
                )
            
            return response
                
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return f"LLM analysis failed: {str(e)}"
    
    def _generate_with_image_azure(self, prompt: str, image: Image.Image) -> str:
        """Generate response using Azure AI Inference with image support."""
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            from azure.ai.inference.models import SystemMessage, UserMessage, ImageContentItem, TextContentItem
            import base64
            import io
            
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Create client
            client = ChatCompletionsClient(
                endpoint=os.getenv('AZURE_CHAT_ENDPOINT'),
                credential=AzureKeyCredential(os.getenv('AZURE_API_KEY')),
                api_version="2024-05-01-preview"
            )
            
            # Create multimodal message
            response = client.complete(
                messages=[
                    SystemMessage(content="You are a network equipment analysis expert."),
                    UserMessage(content=[
                        TextContentItem(text=prompt),
                        ImageContentItem(image_url=f"data:image/jpeg;base64,{image_base64}")
                    ])
                ],
                max_tokens=400,
                temperature=0.1,
                model=os.getenv('CHAT_MODEL', 'Llama-4-Maverick-17B-128E-Instruct-FP8')
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"Azure multimodal generation failed: {e}")
            # Fallback to text-only
            return self.llm_client.generate(prompt, max_tokens=400, temperature=0.1)
    
    def _generate_with_image_fallback(self, prompt: str, image: Image.Image) -> str:
        """Fallback method using direct API call with image."""
        try:
            import requests
            import base64
            import io
            
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {os.getenv("AZURE_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a network equipment analysis expert."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 400,
                "temperature": 0.1,
                "model": os.getenv('CHAT_MODEL', 'Llama-4-Maverick-17B-128E-Instruct-FP8')
            }
            
            api_url = f"{os.getenv('AZURE_CHAT_ENDPOINT')}/chat/completions"
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.warning(f"Direct API multimodal failed: {response.status_code}")
                # Fallback to text-only
                return self.llm_client.generate(prompt, max_tokens=400, temperature=0.1)
                
        except Exception as e:
            logger.warning(f"Fallback multimodal generation failed: {e}")
            # Final fallback to text-only
            return self.llm_client.generate(prompt, max_tokens=400, temperature=0.1)
    
    def format_cv_results(self, cv_results: Dict[str, Any]) -> str:
        """Format Computer Vision results for context."""
        if "error" in cv_results:
            return f"Computer Vision Error: {cv_results['error']}"
        
        formatted = []
        
        # OCR Text and Extracted Data (Priority information)
        if 'ocr_text' in cv_results and cv_results['ocr_text']:
            formatted.append(f"📝 **EXTRACTED TEXT FROM IMAGE:**\n{cv_results['ocr_text']}")
        
        if 'extracted_data' in cv_results:
            data = cv_results['extracted_data']
            data_summary = []
            
            if data['ip_addresses']:
                data_summary.append(f"🌐 IP Addresses: {', '.join(data['ip_addresses'])}")
            if data['mac_addresses']:
                data_summary.append(f"🔗 MAC Addresses: {', '.join(data['mac_addresses'])}")
            if data['manufacturers']:
                data_summary.append(f"🏭 Manufacturers: {', '.join(data['manufacturers'])}")
            if data['model_numbers']:
                data_summary.append(f"📦 Model Numbers: {', '.join(data['model_numbers'])}")
            if data['port_numbers']:
                data_summary.append(f"🔌 Port Numbers: {', '.join(data['port_numbers'])}")
            if data['vlan_ids']:
                data_summary.append(f"🏷️ VLAN IDs: {', '.join(data['vlan_ids'])}")
            if data['serial_numbers']:
                data_summary.append(f"🔢 Serial Numbers: {', '.join(data['serial_numbers'])}")
            if data['device_labels']:
                data_summary.append(f"🏷️ Device Labels: {', '.join(data['device_labels'])}")
            
            if data_summary:
                formatted.append(f"📊 **EXTRACTED NETWORK DATA:**\n" + '\n'.join(data_summary))
        
        # Visual Analysis Results
        # Description
        if 'description' in cv_results and 'captions' in cv_results['description']:
            captions = [cap['text'] for cap in cv_results['description']['captions']]
            formatted.append(f"📷 **VISUAL DESCRIPTION:** {', '.join(captions)}")
        
        # Objects detected
        if 'objects' in cv_results:
            objects = [obj['object'] for obj in cv_results['objects']]
            formatted.append(f"🔍 **OBJECTS DETECTED:** {', '.join(set(objects))}")
        
        # Tags
        if 'tags' in cv_results:
            tags = [tag['name'] for tag in cv_results['tags'] if tag['confidence'] > 0.5]
            formatted.append(f"🏷️ **VISUAL TAGS:** {', '.join(tags[:15])}")  # Show more tags
        
        # Categories
        if 'categories' in cv_results:
            categories = [cat['name'] for cat in cv_results['categories']]
            formatted.append(f"📂 **CATEGORIES:** {', '.join(categories)}")
        
        # Brands detected
        if 'brands' in cv_results:
            brands = [brand['name'] for brand in cv_results['brands']]
            formatted.append(f"🏢 **BRANDS DETECTED:** {', '.join(brands)}")
        
        # Color analysis
        if 'color' in cv_results:
            dominant_colors = cv_results['color'].get('dominantColors', [])
            formatted.append(f"🎨 **DOMINANT COLORS:** {', '.join(dominant_colors[:5])}")
        
        # OCR Errors (if any)
        if 'ocr_error' in cv_results:
            formatted.append(f"⚠️ **OCR Warning:** {cv_results['ocr_error']}")
        
        return '\n\n'.join(formatted) if formatted else "No significant features detected."

def analyze_network_image(image: Image.Image) -> Tuple[str, str]:
    """Main function to analyze uploaded image."""
    if image is None:
        return "Please upload an image.", ""
    
    analyzer = ImageAnalyzer()
    
    # Check if services are available
    if not analyzer.azure_client and not analyzer.llm_client:
        return "Services not configured. Please check your Azure configuration.", ""
    
    # Analyze with Computer Vision
    cv_results = analyzer.analyze_with_computer_vision(image)
    cv_formatted = analyzer.format_cv_results(cv_results)
    
    # Analyze with LLaMA 4 Maverick
    llama_analysis = analyzer.analyze_with_llama(image, cv_results)
    
    return cv_formatted, llama_analysis

# Create Gradio interface
def create_interface():
    with gr.Blocks(title="Advanced Network Equipment Analyzer", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🔌 Advanced Network Equipment Analyzer
        
        **Comprehensive Network Infrastructure Analysis Tool**
        
        Upload an image of network equipment to get detailed analysis including:
        - **📊 Data Extraction**: Extract visible text, labels, model numbers, IP addresses, and technical specifications
        - **🕸️ Mesh Network Detection**: Identify network topology and mesh configurations
        - **📏 Cable Management Analysis**: Assess wire alignment and organization quality
        - **🔧 Actionable Recommendations**: Get specific guidance for improvements
        
        
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(
                    type="pil",
                    label="📸 Upload Network Equipment Image",
                    height=400
                )
                analyze_btn = gr.Button(
                    "🔍 Analyze Network Infrastructure", 
                    variant="primary",
                    size="lg"
                )
                
                gr.Markdown("""
                **💡 Best Results Tips:**
                - Use clear, well-lit images
                - Include visible labels, model numbers, and cable connections
                - Capture both equipment and cable management areas
                - Multiple angles can provide comprehensive analysis
                """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🖥️ Analysis")
                gr.Markdown("*OCR text extraction, object detection, and visual analysis*")
                cv_output = gr.Textbox(
                    label="Extracted Data & Visual Analysis",
                    placeholder="Computer Vision will extract text, identify objects, and analyze visual features...",
                    lines=12,
                    max_lines=20
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 🧠 AI Network Analysis")
                gr.Markdown("*Concise assessment with actionable recommendations*")
                llama_output = gr.Textbox(
                    label="Network Analysis & Recommendations",
                    placeholder="LLaMA 4 Maverick will provide a focused, direct analysis with key findings and actionable recommendations...",
                    lines=12,
                    max_lines=20
                )
        
        # Event handlers
        analyze_btn.click(
            fn=analyze_network_image,
            inputs=[image_input],
            outputs=[cv_output, llama_output],
            show_progress=True
        )
        
        # Enhanced documentation section
        gr.Markdown("""
        ---
        
        ## 📋 Analysis Capabilities
        
        ### 🔍 **Analysis**
        - **OCR Text Extraction**: Reads all visible text, labels, and identifiers
        - **Object Detection**: Identifies network devices, cables, and infrastructure
        - **Brand Recognition**: Detects equipment manufacturers and models
        - **Visual Classification**: Categorizes equipment types and configurations
        
        ### 🤖 **AI Network Analysis**
        - **📊 Data Extraction**: IP addresses, MAC addresses, model numbers, port assignments
        - **🕸️ Mesh Network Detection**: Identifies topology patterns and mesh configurations
        - **📏 Cable Management Assessment**: Evaluates wire alignment and organization quality
        - **🔧 Improvement Recommendations**: Specific, actionable guidance for optimization
        - **🚨 Risk Assessment**: Identifies potential issues and maintenance needs
        
        ### 🎯 **Specialized Features**
        - **Wire Alignment Analysis**: Detailed assessment of cable organization and routing
        - **Mesh Network Topology**: Detection and analysis of mesh network configurations
        - **Infrastructure Optimization**: Recommendations for better cable management
        - **Equipment Inventory**: Comprehensive cataloging of visible network components
        
        ---
        
        ### 🔧 Configuration Status
        
        **Environment Variables:**
        - `AZURE_API_KEY`: Azure API key for LLM ✅
        - `AZURE_CHAT_ENDPOINT`: Azure Chat endpoint ✅  
        - `COMPUTER_VISION_KEY`: Azure Computer Vision key ✅
        - `COMPUTER_VISION_ENDPOINT`: Azure Computer Vision endpoint ✅
        - `CHAT_MODEL`: LLaMA 4 Maverick model ✅
        
        **Features:**
        - 🔍 Visual Analysis: Object detection, brand recognition, color analysis
        - 📝 OCR Text Extraction: Reads labels, model numbers, configuration data
        - 🤖 AI Analysis: Network topology, cable management, recommendations
        - 📊 Data Extraction: IP addresses, MAC addresses, port numbers, VLANs
        """)
    
    return demo

if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch(
        share=False,
        show_error=True
    )