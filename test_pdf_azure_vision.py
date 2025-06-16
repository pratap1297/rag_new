#!/usr/bin/env python3
"""
PDF Extraction using Azure Computer Vision
Extract PDF data page by page using Azure AI Vision services
Based on the enhanced document extraction pipeline
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from io import BytesIO
import base64
import logging
from typing import Optional, Dict, Any, List, Tuple

# Azure imports
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials

# PDF processing imports
try:
    import fitz  # PyMuPDF
    import pdf2image
    from PIL import Image
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Install with: pip install PyMuPDF pdf2image pillow python-dotenv azure-cognitiveservices-vision-computervision")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AzurePDFExtractor:
    """PDF extractor using Azure Computer Vision page by page."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vision_client = self._init_vision_client()
        
    def _init_vision_client(self) -> Optional[ComputerVisionClient]:
        """Initialize Computer Vision client."""
        endpoint = self.config.get('COMPUTER_VISION_ENDPOINT')
        key = self.config.get('COMPUTER_VISION_KEY')
        
        if endpoint and key:
            credentials = CognitiveServicesCredentials(key)
            return ComputerVisionClient(endpoint, credentials)
        else:
            logger.error("Missing Azure Computer Vision credentials")
            return None
    
    def extract_pdf_with_azure_vision(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract PDF content using Azure Computer Vision page by page."""
        
        logger.info(f"🔍 PDF Extraction with Azure Computer Vision")
        logger.info(f"📄 Processing: {Path(pdf_path).name}")
        
        if not os.path.exists(pdf_path):
            logger.error(f"❌ PDF file not found: {pdf_path}")
            return []
        
        if not self.vision_client:
            logger.error("❌ Azure Computer Vision client not initialized")
            return []
        
        file_size = os.path.getsize(pdf_path) / (1024 * 1024)
        logger.info(f"📊 File size: {file_size:.2f} MB")
        
        try:
            # Convert PDF to images
            logger.info("📄 Converting PDF pages to images...")
            pdf_images = self._convert_pdf_to_images(pdf_path)
            
            if not pdf_images:
                logger.error("❌ Failed to convert PDF to images")
                return []
            
            logger.info(f"✅ Converted PDF to {len(pdf_images)} images")
            
            # Extract text from each page
            extracted_pages = []
            
            for page_num, image_data in enumerate(pdf_images, 1):
                logger.info(f"📄 Processing Page {page_num}...")
                
                # Extract text using Azure Computer Vision
                page_text, confidence = self._extract_text_from_image(image_data)
                
                if page_text:
                    logger.info(f"✅ Page {page_num}: {len(page_text)} characters extracted")
                    logger.info(f"   Preview: {page_text[:100]}...")
                    
                    page_data = {
                        'page_number': page_num,
                        'text': page_text,
                        'char_count': len(page_text),
                        'word_count': len(page_text.split()),
                        'confidence': confidence,
                        'extraction_method': 'azure_computer_vision'
                    }
                    extracted_pages.append(page_data)
                else:
                    logger.warning(f"⚠️ Page {page_num}: No text extracted")
                    extracted_pages.append({
                        'page_number': page_num,
                        'text': '',
                        'char_count': 0,
                        'word_count': 0,
                        'confidence': 0.0,
                        'extraction_method': 'azure_computer_vision'
                    })
                
                # Small delay to avoid rate limiting
                time.sleep(1)
            
            # Summary
            total_chars = sum(page['char_count'] for page in extracted_pages)
            successful_pages = len([p for p in extracted_pages if p['char_count'] > 0])
            
            logger.info(f"📊 Extraction Summary:")
            logger.info(f"   Total Pages: {len(extracted_pages)}")
            logger.info(f"   Successful Extractions: {successful_pages}")
            logger.info(f"   Total Characters: {total_chars}")
            
            return extracted_pages
            
        except Exception as e:
            logger.error(f"❌ Error during PDF extraction: {e}")
            return []
    
    def _convert_pdf_to_images(self, pdf_path: str) -> List[bytes]:
        """Convert PDF pages to images."""
        try:
            # Try pdf2image first (better quality)
            try:
                logger.info("✅ Using pdf2image for conversion")
                images = pdf2image.convert_from_path(pdf_path, dpi=200)
                
                image_data_list = []
                for img in images:
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    image_data_list.append(img_byte_arr.getvalue())
                
                return image_data_list
                
            except Exception as e:
                logger.warning(f"pdf2image failed: {e}, trying PyMuPDF")
                
                # Fallback to PyMuPDF
                logger.info("✅ Using PyMuPDF for conversion")
                pdf_document = fitz.open(pdf_path)
                image_data_list = []
                
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    # Render page as image with 2x scale for better OCR
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.pil_tobytes(format="PNG")
                    image_data_list.append(img_data)
                
                pdf_document.close()
                return image_data_list
                
        except Exception as e:
            logger.error(f"❌ Error converting PDF to images: {e}")
            return []
    
    def _extract_text_from_image(self, image_data: bytes) -> Tuple[str, float]:
        """Extract text from image using Azure Computer Vision Read API."""
        try:
            # Submit image for analysis using Read API
            read_response = self.vision_client.read_in_stream(
                BytesIO(image_data),
                raw=True
            )
            
            # Get operation ID from headers
            operation_location = read_response.headers["Operation-Location"]
            operation_id = operation_location.split("/")[-1]
            
            # Poll for results
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(2)  # Wait before checking
                
                read_result = self.vision_client.get_read_result(operation_id)
                
                if read_result.status not in ['notStarted', 'running']:
                    break
            
            # Extract text from results
            text_lines = []
            total_confidence = 0
            word_count = 0
            
            if read_result.status == OperationStatusCodes.succeeded:
                for page in read_result.analyze_result.read_results:
                    for line in page.lines:
                        text_lines.append(line.text)
                        
                        # Calculate average confidence from words
                        if hasattr(line, 'words'):
                            for word in line.words:
                                if hasattr(word, 'confidence'):
                                    total_confidence += word.confidence
                                    word_count += 1
            
            avg_confidence = total_confidence / word_count if word_count > 0 else 0.9
            extracted_text = '\n'.join(text_lines)
            
            return extracted_text, avg_confidence
            
        except Exception as e:
            logger.error(f"❌ Error extracting text from image: {e}")
            return "", 0.0
    
    def save_extracted_content(self, extracted_pages: List[Dict[str, Any]], pdf_path: str) -> str:
        """Save extracted content to JSON file."""
        try:
            output_file = f"extracted_content_{Path(pdf_path).stem}.json"
            
            content = {
                'source_file': str(pdf_path),
                'extraction_method': 'azure_computer_vision',
                'total_pages': len(extracted_pages),
                'total_characters': sum(page['char_count'] for page in extracted_pages),
                'total_words': sum(page['word_count'] for page in extracted_pages),
                'successful_pages': len([p for p in extracted_pages if p['char_count'] > 0]),
                'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'pages': extracted_pages
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Extracted content saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error saving extracted content: {e}")
            return ""
    
    def ingest_into_rag_system(self, extracted_pages: List[Dict[str, Any]], pdf_path: str) -> bool:
        """Ingest extracted content into RAG system."""
        try:
            # Combine all page text
            full_text = '\n\n'.join([
                f"=== Page {page['page_number']} ===\n{page['text']}"
                for page in extracted_pages if page['text'].strip()
            ])
            
            if not full_text.strip():
                logger.error("❌ No text content to ingest")
                return False
            
            logger.info(f"📤 Ingesting {len(full_text)} characters of extracted text...")
            
            # Prepare metadata
            metadata = {
                "title": f"USAM Report - {Path(pdf_path).stem}",
                "source": "azure_computer_vision_extraction",
                "document_type": "pdf_report",
                "file_type": "pdf",
                "original_path": str(pdf_path),
                "extraction_method": "azure_computer_vision",
                "total_pages": len(extracted_pages),
                "total_characters": len(full_text),
                "successful_pages": len([p for p in extracted_pages if p['text'].strip()]),
                "description": f"PDF document extracted using Azure Computer Vision: {Path(pdf_path).name}"
            }
            
            # Test ingestion via API
            api_base_url = "http://localhost:8000"
            
            response = requests.post(
                f"{api_base_url}/ingest",
                json={
                    "text": full_text,
                    "metadata": metadata
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Ingestion successful!")
                logger.info(f"   Chunks created: {result.get('chunks_created', 0)}")
                logger.info(f"   Vectors stored: {result.get('vectors_stored', 0)}")
                return True
            else:
                logger.error(f"❌ Ingestion failed: HTTP {response.status_code}")
                logger.error(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing ingestion: {e}")
            return False
    
    def test_query_on_ingested_content(self, query: str = "What is this USAM report about?") -> bool:
        """Test querying the ingested content."""
        try:
            logger.info(f"🔍 Testing query: '{query}'")
            
            api_base_url = "http://localhost:8000"
            
            query_response = requests.post(
                f"{api_base_url}/query",
                json={"query": query, "max_results": 3},
                timeout=30
            )
            
            if query_response.status_code == 200:
                query_result = query_response.json()
                answer = query_result.get('response', query_result.get('answer', ''))
                logger.info(f"✅ Query successful!")
                logger.info(f"📄 Answer: {answer[:300]}...")
                return True
            else:
                logger.error(f"❌ Query failed: HTTP {query_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing query: {e}")
            return False


def load_config() -> Dict[str, Any]:
    """Load configuration from environment."""
    # Load from rag_system/.env file
    load_dotenv('rag_system/.env')
    
    config = {
        'COMPUTER_VISION_KEY': os.getenv('COMPUTER_VISION_KEY'),
        'COMPUTER_VISION_ENDPOINT': os.getenv('COMPUTER_VISION_ENDPOINT'),
    }
    
    # Validate required config
    missing = [k for k, v in config.items() if not v]
    if missing:
        logger.error(f"❌ Missing required environment variables: {missing}")
        logger.error("   Please check your .env file")
        return {}
    
    return config


def main():
    """Main function to test PDF extraction."""
    # PDF file path
    pdf_path = r"C:\Users\jaideepvm\Downloads\USAMReport-21-40-1-5.pdf"
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    # Initialize extractor
    extractor = AzurePDFExtractor(config)
    
    # Extract PDF content
    logger.info("🚀 Starting PDF extraction process...")
    extracted_pages = extractor.extract_pdf_with_azure_vision(pdf_path)
    
    if not extracted_pages:
        logger.error("❌ PDF extraction failed")
        return
    
    # Save extracted content
    output_file = extractor.save_extracted_content(extracted_pages, pdf_path)
    
    # Test ingestion into RAG system
    logger.info("🔄 Testing RAG System Ingestion...")
    ingestion_success = extractor.ingest_into_rag_system(extracted_pages, pdf_path)
    
    if ingestion_success:
        # Test queries
        test_queries = [
            "What is this USAM report about?",
            "What are the main topics covered in this document?",
            "Tell me about any findings or conclusions",
            "What recommendations are made in this report?",
            "Summarize the key points from this document"
        ]
        
        logger.info("🔍 Testing queries on ingested content...")
        for query in test_queries:
            extractor.test_query_on_ingested_content(query)
            time.sleep(1)  # Small delay between queries
    
    # Final summary
    total_chars = sum(page['char_count'] for page in extracted_pages)
    successful_pages = len([p for p in extracted_pages if p['char_count'] > 0])
    
    logger.info("🎉 PDF Extraction Complete!")
    logger.info(f"   📄 File: {Path(pdf_path).name}")
    logger.info(f"   📊 Pages processed: {len(extracted_pages)}")
    logger.info(f"   ✅ Successful extractions: {successful_pages}")
    logger.info(f"   📝 Total characters: {total_chars}")
    logger.info(f"   💾 Output saved to: {output_file}")
    logger.info(f"   🔄 RAG ingestion: {'✅ Success' if ingestion_success else '❌ Failed'}")


if __name__ == "__main__":
    main()