# src/integrations/azure_ai/azure_client.py
"""
Azure AI Services Client
Handles Azure Computer Vision with optional Document Intelligence support
"""
import os
import logging
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import base64
from io import BytesIO

# Azure Computer Vision imports
try:
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    from msrest.authentication import CognitiveServicesCredentials
    AZURE_CV_AVAILABLE = True
except ImportError:
    AZURE_CV_AVAILABLE = False
    ComputerVisionClient = None

# Optional Azure Document Intelligence imports
try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_DI_AVAILABLE = True
except ImportError:
    AZURE_DI_AVAILABLE = False
    DocumentIntelligenceClient = None


class AzureAIClient:
    """Client for Azure AI services with focus on Computer Vision"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Azure AI client"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Computer Vision settings - support multiple env var names
        self.cv_endpoint = (self.config.get('computer_vision_endpoint') or 
                           os.getenv('AZURE_COMPUTER_VISION_ENDPOINT') or 
                           os.getenv('AZURE_CV_ENDPOINT'))
        self.cv_key = (self.config.get('computer_vision_key') or 
                      os.getenv('AZURE_COMPUTER_VISION_KEY') or 
                      os.getenv('AZURE_CV_KEY'))
        
        # Document Intelligence settings (optional) - support multiple env var names
        self.di_endpoint = (self.config.get('document_intelligence_endpoint') or 
                           os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT') or 
                           os.getenv('AZURE_DI_ENDPOINT'))
        self.di_key = (self.config.get('document_intelligence_key') or 
                      os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY') or 
                      os.getenv('AZURE_DI_KEY'))
        
        # Settings
        self.max_image_size_mb = self.config.get('max_image_size_mb', 4)
        self.ocr_language = self.config.get('ocr_language', 'en')
        self.enable_handwriting = self.config.get('enable_handwriting', True)
        
        # Initialize clients
        self.cv_client = None
        self.di_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Azure clients"""
        # Initialize Computer Vision
        if AZURE_CV_AVAILABLE and self.cv_endpoint and self.cv_key:
            try:
                self.cv_client = ComputerVisionClient(
                    self.cv_endpoint,
                    CognitiveServicesCredentials(self.cv_key)
                )
                self.logger.info("Azure Computer Vision client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Computer Vision client: {e}")
        else:
            self.logger.warning("Azure Computer Vision not available or not configured")
        
        # Initialize Document Intelligence (optional)
        if AZURE_DI_AVAILABLE and self.di_endpoint and self.di_key:
            try:
                self.di_client = DocumentIntelligenceClient(
                    endpoint=self.di_endpoint,
                    credential=AzureKeyCredential(self.di_key)
                )
                self.logger.info("Azure Document Intelligence client initialized (optional)")
            except Exception as e:
                self.logger.warning(f"Document Intelligence initialization failed (optional): {e}")
    
    def is_available(self) -> bool:
        """Check if at least Computer Vision is available"""
        return self.cv_client is not None
    
    def process_image(self, image_data: bytes, image_type: str = "general") -> Dict[str, Any]:
        """Process image using Computer Vision OCR"""
        if not self.cv_client:
            return {
                'success': False,
                'error': 'Computer Vision client not initialized',
                'text': '',
                'regions': []
            }
        
        try:
            # Check image size
            if len(image_data) > self.max_image_size_mb * 1024 * 1024:
                return {
                    'success': False,
                    'error': f'Image size exceeds {self.max_image_size_mb}MB limit',
                    'text': '',
                    'regions': []
                }
            
            # Convert to stream
            image_stream = BytesIO(image_data)
            
            # Perform OCR
            if self.enable_handwriting or image_type == "handwritten":
                # Use Read API for better accuracy (supports handwriting)
                return self._process_with_read_api(image_stream)
            else:
                # Use simple OCR for faster processing
                return self._process_with_ocr(image_stream)
            
        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'regions': []
            }
    
    def _process_with_read_api(self, image_stream: BytesIO) -> Dict[str, Any]:
        """Process image using Read API (supports handwriting)"""
        try:
            # Submit read operation
            read_response = self.cv_client.read_in_stream(
                image_stream,
                raw=True,
                language=self.ocr_language
            )
            
            # Get operation location
            operation_location = read_response.headers["Operation-Location"]
            operation_id = operation_location.split("/")[-1]
            
            # Wait for operation to complete
            result = None
            max_retries = 10
            retry_delay = 1
            
            for _ in range(max_retries):
                result = self.cv_client.get_read_result(operation_id)
                if result.status not in ['notStarted', 'running']:
                    break
                time.sleep(retry_delay)
            
            # Process results
            if result.status == OperationStatusCodes.succeeded:
                text_lines = []
                regions = []
                
                for page in result.analyze_result.read_results:
                    page_region = {
                        'page': page.page,
                        'width': page.width,
                        'height': page.height,
                        'lines': []
                    }
                    
                    for line in page.lines:
                        text_lines.append(line.text)
                        page_region['lines'].append({
                            'text': line.text,
                            'bounding_box': line.bounding_box
                        })
                    
                    regions.append(page_region)
                
                return {
                    'success': True,
                    'text': '\n'.join(text_lines),
                    'regions': regions,
                    'language': self.ocr_language
                }
            else:
                return {
                    'success': False,
                    'error': f'Read operation failed with status: {result.status}',
                    'text': '',
                    'regions': []
                }
                
        except Exception as e:
            self.logger.error(f"Read API error: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'regions': []
            }
    
    def _process_with_ocr(self, image_stream: BytesIO) -> Dict[str, Any]:
        """Process image using simple OCR API"""
        try:
            ocr_result = self.cv_client.recognize_printed_text_in_stream(
                image_stream,
                language=self.ocr_language
            )
            
            text_lines = []
            regions = []
            
            for region in ocr_result.regions:
                region_data = {
                    'bounding_box': region.bounding_box,
                    'lines': []
                }
                
                for line in region.lines:
                    line_text = ' '.join([word.text for word in line.words])
                    text_lines.append(line_text)
                    region_data['lines'].append({
                        'text': line_text,
                        'bounding_box': line.bounding_box,
                        'words': [{'text': w.text, 'bounding_box': w.bounding_box} for w in line.words]
                    })
                
                regions.append(region_data)
            
            return {
                'success': True,
                'text': '\n'.join(text_lines),
                'regions': regions,
                'language': self.ocr_language
            }
            
        except Exception as e:
            self.logger.error(f"OCR API error: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'regions': []
            }
    
    def analyze_image(self, image_data: bytes, features: List[str] = None) -> Dict[str, Any]:
        """Analyze image for various features beyond OCR"""
        if not self.cv_client:
            return {
                'success': False,
                'error': 'Computer Vision client not initialized',
                'analysis': {}
            }
        
        try:
            # Default features
            if features is None:
                features = ['description', 'tags', 'objects']
            
            image_stream = BytesIO(image_data)
            
            # Analyze image
            analysis = self.cv_client.analyze_image_in_stream(
                image_stream,
                visual_features=features
            )
            
            result = {
                'success': True,
                'analysis': {}
            }
            
            # Process different features
            if hasattr(analysis, 'description') and analysis.description:
                result['analysis']['description'] = {
                    'captions': [{'text': cap.text, 'confidence': cap.confidence} 
                               for cap in analysis.description.captions],
                    'tags': analysis.description.tags
                }
            
            if hasattr(analysis, 'tags') and analysis.tags:
                result['analysis']['tags'] = [
                    {'name': tag.name, 'confidence': tag.confidence} 
                    for tag in analysis.tags
                ]
            
            if hasattr(analysis, 'objects') and analysis.objects:
                result['analysis']['objects'] = [
                    {
                        'object': obj.object_property,
                        'confidence': obj.confidence,
                        'rectangle': {
                            'x': obj.rectangle.x,
                            'y': obj.rectangle.y,
                            'w': obj.rectangle.w,
                            'h': obj.rectangle.h
                        }
                    }
                    for obj in analysis.objects
                ]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Image analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': {}
            }
    
    def process_document_layout(self, document_data: bytes, document_type: str = "mixed") -> Dict[str, Any]:
        """Process document layout (optional - uses Document Intelligence if available)"""
        if self.di_client:
            return self._process_with_document_intelligence(document_data, document_type)
        else:
            # Fallback to Computer Vision
            self.logger.info("Document Intelligence not available, using Computer Vision")
            return self.process_image(document_data, image_type="document")
    
    def _process_with_document_intelligence(self, document_data: bytes, document_type: str) -> Dict[str, Any]:
        """Process document using Document Intelligence (optional feature)"""
        try:
            # Use prebuilt-layout model for general documents
            poller = self.di_client.begin_analyze_document(
                "prebuilt-layout",
                document_data,
                content_type="application/pdf" if document_type == "pdf" else "image/png"
            )
            
            result = poller.result()
            
            # Extract structured content
            extracted_data = {
                'success': True,
                'pages': [],
                'tables': [],
                'key_value_pairs': []
            }
            
            # Process pages
            for page in result.pages:
                page_data = {
                    'page_number': page.page_number,
                    'width': page.width,
                    'height': page.height,
                    'lines': []
                }
                
                for line in page.lines:
                    page_data['lines'].append({
                        'text': line.content,
                        'bounding_box': line.polygon
                    })
                
                extracted_data['pages'].append(page_data)
            
            # Process tables
            if hasattr(result, 'tables'):
                for table in result.tables:
                    table_data = {
                        'row_count': table.row_count,
                        'column_count': table.column_count,
                        'cells': []
                    }
                    
                    for cell in table.cells:
                        table_data['cells'].append({
                            'row_index': cell.row_index,
                            'column_index': cell.column_index,
                            'text': cell.content,
                            'row_span': getattr(cell, 'row_span', 1),
                            'column_span': getattr(cell, 'column_span', 1)
                        })
                    
                    extracted_data['tables'].append(table_data)
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Document Intelligence error: {e}")
            # Fallback to Computer Vision
            return self.process_image(document_data, image_type="document")
    
    def batch_process_images(self, images: List[Dict[str, Any]], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Batch process multiple images"""
        results = []
        
        # Process in batches to avoid overwhelming the service
        for i in range(0, len(images), max_concurrent):
            batch = images[i:i + max_concurrent]
            batch_results = []
            
            for image_info in batch:
                try:
                    result = self.process_image(
                        image_info['data'],
                        image_type=image_info.get('type', 'general')
                    )
                    result['id'] = image_info.get('id', f'image_{i}')
                    batch_results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing image {image_info.get('id')}: {e}")
                    batch_results.append({
                        'id': image_info.get('id', f'image_{i}'),
                        'success': False,
                        'error': str(e),
                        'text': '',
                        'regions': []
                    })
            
            results.extend(batch_results)
            
            # Small delay between batches
            if i + max_concurrent < len(images):
                time.sleep(0.5)
        
        return results
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about available services"""
        return {
            'computer_vision': {
                'available': self.cv_client is not None,
                'endpoint': self.cv_endpoint if self.cv_endpoint else 'Not configured',
                'features': ['OCR', 'Read API', 'Image Analysis', 'Handwriting Recognition']
            },
            'document_intelligence': {
                'available': self.di_client is not None,
                'endpoint': self.di_endpoint if self.di_endpoint else 'Not configured',
                'features': ['Layout Analysis', 'Table Extraction', 'Form Recognition']
            },
            'settings': {
                'max_image_size_mb': self.max_image_size_mb,
                'ocr_language': self.ocr_language,
                'enable_handwriting': self.enable_handwriting
            }
        }