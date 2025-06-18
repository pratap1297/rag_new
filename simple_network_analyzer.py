# simple_network_analyzer.py
"""
Standalone Network Equipment Analyzer
Uses only the specific Azure environment variables
"""
import os
import gradio as gr
import base64
import json
import requests
from PIL import Image
import io
import logging
from typing import Dict, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set the specific environment variables
os.environ['AZURE_API_KEY'] = '6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr'
os.environ['AZURE_CHAT_ENDPOINT'] = 'https://azurehub1910875317.services.ai.azure.com/models'
os.environ['AZURE_EMBEDDINGS_ENDPOINT'] = 'https://azurehub1910875317.services.ai.azure.com/models'
os.environ['COMPUTER_VISION_KEY'] = 'FSf3hSW3ogphcme0MgMMKZNTzkQTXo6sNikmlyUhSqahBHgnoaOFJQQJ99BFACYeBjFXJ3w3AAAFACOGPuhx'
os.environ['COMPUTER_VISION_ENDPOINT'] = 'https://computervision1298.cognitiveservices.azure.com/'
os.environ['COMPUTER_VISION_REGION'] = 'eastus'
os.environ['CHAT_MODEL'] = 'Llama-4-Maverick-17B-128E-Instruct-FP8'
os.environ['EMBEDDING_MODEL'] = 'Cohere-embed-v3-english'

class SimpleNetworkAnalyzer:
    """Simple Network Analyzer using Azure services"""
    
    def __init__(self):
        """Initialize with environment variables"""
        self.azure_api_key = os.environ['AZURE_API_KEY']
        self.azure_chat_endpoint = os.environ['AZURE_CHAT_ENDPOINT']
        self.cv_key = os.environ['COMPUTER_VISION_KEY']
        self.cv_endpoint = os.environ['COMPUTER_VISION_ENDPOINT']
        self.chat_model = os.environ['CHAT_MODEL']
        
        logger.info("Simple Network Analyzer initialized")
    
    def encode_image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        try:
            # Optimize image size
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=85, optimize=True)
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    def analyze_with_computer_vision(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image using Azure Computer Vision API"""
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Analyze image
            analyze_url = f"{self.cv_endpoint}vision/v3.2/analyze"
            headers = {
                'Ocp-Apim-Subscription-Key': self.cv_key,
                'Content-Type': 'application/octet-stream'
            }
            params = {
                'visualFeatures': 'Categories,Description,Objects,Tags,Color',
                'details': 'Landmarks'
            }
            
            response = requests.post(analyze_url, headers=headers, params=params, data=img_byte_arr, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Computer Vision API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Computer Vision analysis failed: {str(e)}"}
    
    def ocr_analysis(self, image: Image.Image) -> Dict[str, Any]:
        """Perform OCR on the image"""
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr = img_byte_arr.getvalue()
            
            # OCR API call
            ocr_url = f"{self.cv_endpoint}vision/v3.2/read/analyze"
            headers = {
                'Ocp-Apim-Subscription-Key': self.cv_key,
                'Content-Type': 'application/octet-stream'
            }
            
            response = requests.post(ocr_url, headers=headers, data=img_byte_arr, timeout=30)
            
            if response.status_code == 202:
                # Get operation location
                operation_url = response.headers.get('Operation-Location')
                
                # Poll for results
                import time
                max_attempts = 10
                for _ in range(max_attempts):
                    time.sleep(2)
                    result_response = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': self.cv_key})
                    
                    if result_response.status_code == 200:
                        result = result_response.json()
                        if result['status'] == 'succeeded':
                            return result
                        elif result['status'] == 'failed':
                            return {"error": "OCR operation failed"}
                
                return {"error": "OCR operation timed out"}
            else:
                return {"error": f"OCR API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"OCR analysis failed: {str(e)}"}
    
    def analyze_with_llama4(self, image: Image.Image, cv_results: Dict[str, Any]) -> str:
        """Analyze image using LLAMA4 Maverick"""
        try:
            # Encode image
            base64_image = self.encode_image_to_base64(image)
            
            # Create context from Computer Vision results
            cv_context = self.format_cv_results(cv_results)
            
            # Network analysis prompt
            prompt = f"""You are an expert network engineer analyzing network equipment and infrastructure.

Computer Vision detected the following in this image:
{cv_context}

Please analyze this image of network equipment and provide detailed insights about:

1. **Equipment Identification**: What types of network devices, cables, and infrastructure do you see?
2. **Network Topology**: Can you determine the network setup and topology type?
3. **Cable Management**: Assess the cable organization and management approach
4. **Equipment Types**: Identify specific networking hardware (switches, routers, patch panels, etc.)
5. **Infrastructure Assessment**: Comment on the overall network infrastructure setup
6. **Technical Recommendations**: Suggest improvements or observations about the setup

Focus on technical networking aspects and provide specific, actionable insights."""

            # Call LLAMA4 Maverick API
            headers = {
                'Authorization': f'Bearer {self.azure_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": self.chat_model,
                "messages": [
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
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.3,
                "top_p": 0.9
            }
            
            response = requests.post(
                f"{self.azure_chat_endpoint}/{self.chat_model}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"LLAMA4 API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"LLAMA4 analysis failed: {str(e)}"
    
    def format_cv_results(self, cv_results: Dict[str, Any]) -> str:
        """Format Computer Vision results for context"""
        if "error" in cv_results:
            return f"Computer Vision Error: {cv_results['error']}"
        
        formatted = []
        
        # Description
        if 'description' in cv_results and 'captions' in cv_results['description']:
            captions = [f"{cap['text']} (confidence: {cap['confidence']:.2f})" 
                       for cap in cv_results['description']['captions']]
            formatted.append(f"Description: {'; '.join(captions)}")
        
        # Objects
        if 'objects' in cv_results:
            objects = [f"{obj['object']} (confidence: {obj['confidence']:.2f})" 
                      for obj in cv_results['objects']]
            formatted.append(f"Objects: {'; '.join(objects[:10])}")
        
        # Tags
        if 'tags' in cv_results:
            tags = [f"{tag['name']} ({tag['confidence']:.2f})" 
                   for tag in cv_results['tags'] if tag['confidence'] > 0.5]
            formatted.append(f"Tags: {'; '.join(tags[:15])}")
        
        # Categories
        if 'categories' in cv_results:
            categories = [f"{cat['name']} ({cat['score']:.2f})" 
                         for cat in cv_results['categories']]
            formatted.append(f"Categories: {'; '.join(categories[:5])}")
        
        # Color
        if 'color' in cv_results:
            color_info = []
            if 'dominantColors' in cv_results['color']:
                color_info.append(f"Dominant colors: {', '.join(cv_results['color']['dominantColors'][:5])}")
            if 'accentColor' in cv_results['color']:
                color_info.append(f"Accent color: {cv_results['color']['accentColor']}")
            if color_info:
                formatted.append('; '.join(color_info))
        
        return '\n'.join(formatted) if formatted else "No significant features detected."
    
    def extract_ocr_text(self, ocr_results: Dict[str, Any]) -> str:
        """Extract text from OCR results"""
        if "error" in ocr_results:
            return f"OCR Error: {ocr_results['error']}"
        
        if 'analyzeResult' not in ocr_results:
            return "No text detected"
        
        text_lines = []
        for page in ocr_results['analyzeResult']['readResults']:
            for line in page['lines']:
                text_lines.append(line['text'])
        
        return '\n'.join(text_lines) if text_lines else "No text detected"
    
    def comprehensive_analysis(self, image: Image.Image) -> Tuple[str, str, str, str]:
        """Perform comprehensive analysis"""
        if image is None:
            return "Please upload an image.", "", "", ""
        
        try:
            # Computer Vision analysis
            logger.info("Starting Computer Vision analysis...")
            cv_results = self.analyze_with_computer_vision(image)
            cv_formatted = self.format_cv_results(cv_results)
            
            # OCR analysis
            logger.info("Starting OCR analysis...")
            ocr_results = self.ocr_analysis(image)
            ocr_text = self.extract_ocr_text(ocr_results)
            
            # LLAMA4 analysis
            logger.info("Starting LLAMA4 analysis...")
            llama_analysis = self.analyze_with_llama4(image, cv_results)
            
            # Generate summary
            summary = self.generate_summary(cv_results, ocr_text, llama_analysis)
            
            logger.info("Analysis completed successfully")
            return cv_formatted, ocr_text, llama_analysis, summary
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg)
            return error_msg, "", "", ""
    
    def generate_summary(self, cv_results: Dict[str, Any], ocr_text: str, llama_analysis: str) -> str:
        """Generate a summary of all analyses"""
        summary_parts = []
        
        # CV summary
        if 'objects' in cv_results and not "error" in cv_results:
            object_count = len(cv_results['objects'])
            summary_parts.append(f"🔍 Computer Vision detected {object_count} objects")
        
        if 'tags' in cv_results:
            high_conf_tags = [tag['name'] for tag in cv_results['tags'] if tag['confidence'] > 0.8]
            if high_conf_tags:
                summary_parts.append(f"🏷️ Key elements: {', '.join(high_conf_tags[:5])}")
        
        # OCR summary
        if ocr_text and "No text detected" not in ocr_text and "OCR Error" not in ocr_text:
            text_lines = len(ocr_text.split('\n'))
            summary_parts.append(f"📝 OCR extracted {text_lines} lines of text")
        
        # LLAMA analysis summary
        analysis_lower = llama_analysis.lower()
        if "switch" in analysis_lower:
            summary_parts.append("🔗 Network switches identified")
        if "router" in analysis_lower:
            summary_parts.append("📡 Router equipment detected")
        if "cable" in analysis_lower:
            summary_parts.append("🔌 Cable infrastructure analyzed")
        if "rack" in analysis_lower:
            summary_parts.append("🏗️ Rack infrastructure assessed")
        
        return "\n".join(summary_parts) if summary_parts else "✅ Analysis completed successfully"
    
    def test_connections(self) -> str:
        """Test Azure service connections"""
        try:
            results = []
            
            # Test Computer Vision
            try:
                test_url = f"{self.cv_endpoint}vision/v3.2/analyze"
                headers = {'Ocp-Apim-Subscription-Key': self.cv_key}
                params = {'visualFeatures': 'Categories'}
                
                # Use a small test image URL
                test_data = {'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Test_card.png/256px-Test_card.png'}
                response = requests.post(test_url, headers=headers, params=params, json=test_data, timeout=10)
                
                if response.status_code == 200:
                    results.append("✅ Computer Vision: Connected")
                else:
                    results.append(f"❌ Computer Vision: Error {response.status_code}")
            except Exception as e:
                results.append(f"❌ Computer Vision: {str(e)}")
            
            # Test LLAMA4
            try:
                headers = {
                    'Authorization': f'Bearer {self.azure_api_key}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    "model": self.chat_model,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5
                }
                response = requests.post(
                    f"{self.azure_chat_endpoint}/{self.chat_model}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results.append("✅ LLAMA4 Maverick: Connected")
                else:
                    results.append(f"❌ LLAMA4 Maverick: Error {response.status_code}")
            except Exception as e:
                results.append(f"❌ LLAMA4 Maverick: {str(e)}")
            
            # Configuration info
            config_info = [
                f"🔧 Chat Model: {self.chat_model}",
                f"🌍 CV Region: {os.environ['COMPUTER_VISION_REGION']}",
                f"📡 CV Endpoint: {self.cv_endpoint}",
                f"🤖 Chat Endpoint: {self.azure_chat_endpoint}"
            ]
            
            return "\n".join(results) + "\n\n" + "\n".join(config_info)
            
        except Exception as e:
            return f"❌ Connection test failed: {str(e)}"

def create_interface():
    """Create the Gradio interface"""
    analyzer = SimpleNetworkAnalyzer()
    
    # Custom CSS
    custom_css = """
    .gradio-container {
        max-width: 1400px !important;
    }
    .analysis-header {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    """
    
    with gr.Blocks(title="Simple Network Equipment Analyzer", theme=gr.themes.Soft(), css=custom_css) as demo:
        
        gr.HTML("""
        <div class="analysis-header">
            <h1>🔌 Simple Network Equipment Analyzer</h1>
            <p>AI-powered network infrastructure analysis using Azure Computer Vision and LLAMA4 Maverick</p>
        </div>
        """)
        
        # Connection test section
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("### 📡 Azure Services Status")
                connection_status = gr.Textbox(
                    label="Service Status",
                    value="Click 'Test Connection' to check Azure services",
                    lines=6,
                    interactive=False
                )
            with gr.Column(scale=1):
                test_btn = gr.Button("🔍 Test Connection", variant="secondary", size="lg")
        
        gr.Markdown("---")
        
        # Main interface
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📤 Upload Network Image")
                image_input = gr.Image(
                    type="pil",
                    label="Network Equipment Image",
                    height=400,
                    sources=["upload", "clipboard", "webcam"]
                )
                
                with gr.Row():
                    analyze_btn = gr.Button("🚀 Analyze Equipment", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ Clear", variant="secondary", size="lg")
                
                gr.Markdown("### 📊 Analysis Summary")
                summary_output = gr.Textbox(
                    label="Quick Summary",
                    placeholder="Analysis summary will appear here...",
                    lines=6,
                    interactive=False
                )
        
        # Analysis results
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🖥️ Computer Vision Analysis")
                cv_output = gr.Textbox(
                    label="Visual Analysis Results",
                    placeholder="Computer Vision analysis will appear here...",
                    lines=12,
                    interactive=False,
                    show_copy_button=True
                )
            
            with gr.Column():
                gr.Markdown("### 📝 OCR Text Extraction")
                ocr_output = gr.Textbox(
                    label="Extracted Text",
                    placeholder="OCR text extraction will appear here...",
                    lines=12,
                    interactive=False,
                    show_copy_button=True
                )
        
        with gr.Row():
            gr.Markdown("### 🧠 LLAMA4 Maverick Expert Analysis")
            llama_output = gr.Textbox(
                label="AI Network Engineering Analysis",
                placeholder="Expert AI analysis will appear here...",
                lines=15,
                interactive=False,
                show_copy_button=True
            )
        
        # Event handlers
        test_btn.click(
            fn=analyzer.test_connections,
            outputs=[connection_status],
            show_progress=True
        )
        
        analyze_btn.click(
            fn=analyzer.comprehensive_analysis,
            inputs=[image_input],
            outputs=[cv_output, ocr_output, llama_output, summary_output],
            show_progress=True
        )
        
        clear_btn.click(
            fn=lambda: (None, "", "", "", ""),
            outputs=[image_input, cv_output, ocr_output, llama_output, summary_output]
        )
        
        # Auto-test connection on load
        demo.load(
            fn=analyzer.test_connections,
            outputs=[connection_status]
        )
    
    return demo

if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch(
        share=False,
        show_error=True,
        server_name="0.0.0.0",
        server_port=7860,
        show_api=True
    )