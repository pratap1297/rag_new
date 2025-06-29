# -*- coding: utf-8 -*-
"""
Enhanced PDF Processor with Azure Computer Vision Integration
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import fitz  # PyMuPDF
    import PyPDF2
    HAS_PDF_LIBS = True
except ImportError:
    HAS_PDF_LIBS = False
    logging.warning("PDF processing libraries not available. Install PyMuPDF and PyPDF2.")

try:
    from .base_processor import BaseProcessor
except ImportError:
    class BaseProcessor:
        def __init__(self, config=None):
            self.config = config or {}
            self.logger = logging.getLogger(__name__)


class EnhancedPDFProcessor(BaseProcessor):
    def __init__(self, config=None, azure_client=None):
        super().__init__(config)
        self.azure_client = azure_client
        self.supported_extensions = ['.pdf']
        
        if not HAS_PDF_LIBS:
            self.logger.warning("PDF processing libraries not available. Limited functionality.")
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed by this processor"""
        return Path(file_path).suffix.lower() in self.supported_extensions
        
    def _process_image_with_azure(self, image_data: bytes) -> Dict[str, Any]:
        """Process image with Azure CV with proper error handling"""
        if not self.azure_client:
            return {'text': '[Azure CV not available]', 'error': 'No Azure client'}
        try:
            result = self.azure_client.process_image(image_data, image_type='document')
            if result.get('success'):
                return {
                    'text': result.get('text', ''),
                    'regions': result.get('regions', []),
                    'confidence': result.get('confidence', 0.0)
                }
            else:
                self.logger.warning(f"Azure CV processing failed: {result.get('error')}")
                return {'text': '[OCR failed]', 'error': result.get('error')}
        except Exception as e:
            self.logger.error(f"Azure CV exception: {e}")
            return {'text': '[OCR error]', 'error': str(e)}

    def process(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process PDF with full text, image, and metadata extraction"""
        start_time = datetime.now()
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"📄 Starting PDF processing: {file_path}")
        self.logger.info(f"📄 File size: {file_path.stat().st_size:,} bytes")
        
        result = {
            'status': 'success',
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'processing_start': start_time.isoformat(),
            'pages': [],
            'images': [],
            'tables': [],
            'metadata': self._extract_pdf_metadata(file_path),
            'chunks': []
        }
        
        # ADD LOGGING: After metadata extraction
        self.logger.info(f"📄 PDF Metadata Extracted:")
        self.logger.info(f"  - Title: {result['metadata'].get('title', 'N/A')}")
        self.logger.info(f"  - Author: {result['metadata'].get('author', 'N/A')}")
        self.logger.info(f"  - Page Count: {result['metadata'].get('page_count', 'Unknown')}")
        self.logger.info(f"  - Creation Date: {result['metadata'].get('creation_date', 'N/A')}")
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"  - Full metadata: {json.dumps(result['metadata'], indent=2, default=str)}")
        
        # Check if PDF libraries are available
        if not HAS_PDF_LIBS:
            self.logger.warning("PDF libraries not available, creating basic chunk")
            result['chunks'] = [{
                'text': f"PDF document: {file_path.name} (Enhanced processing not available)",
                'metadata': {
                    'source': str(file_path),
                    'chunk_type': 'pdf_basic',
                    'processor': 'enhanced_pdf_fallback'
                }
            }]
            return result
        
        # Process each page
        try:
            pdf_document = fitz.open(str(file_path))  # PyMuPDF
        except Exception as e:
            self.logger.error(f"Failed to open PDF with PyMuPDF: {e}")
            result['chunks'] = [{
                'text': f"PDF document: {file_path.name} (Processing failed: {str(e)})",
                'metadata': {
                    'source': str(file_path),
                    'chunk_type': 'pdf_error',
                    'processor': 'enhanced_pdf_error',
                    'error': str(e)
                }
            }]
            return result
        
        total_pages = len(pdf_document)
        self.logger.info(f"📄 PDF opened successfully - {total_pages} pages found")
        
        for page_num, page in enumerate(pdf_document):
            page_start = datetime.now()
            self.logger.debug(f"📄 Processing page {page_num + 1}/{total_pages}")
            
            page_data = {
                'page_number': page_num + 1,
                'text': page.get_text(),
                'images': [],
                'tables': [],
                'annotations': []
            }
            original_page_text_length = len(page_data['text'])
            
            # Extract images from page
            image_list = page.get_images()
            self.logger.debug(f"📄 Page {page_num + 1}: Found {len(image_list)} images")
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                image_data = self._extract_image(pdf_document, xref)
                
                if image_data:
                    ocr_result = self._process_image_with_azure(image_data)
                    if ocr_result.get('text') and not ocr_result.get('error'):
                        page_data['images'].append({
                            'image_index': img_index,
                            'page': page_num + 1,
                            'ocr_text': ocr_result['text'],
                            'regions': ocr_result.get('regions', [])
                        })
                        # Add OCR text to page text
                        page_data['text'] += f"\n[Image {img_index}]: {ocr_result['text']}"
                        
                        # ADD LOGGING: OCR results
                        self.logger.debug(f"  - Image {img_index + 1} OCR: {len(ocr_result['text'])} chars extracted")
                        self.logger.debug(f"    OCR Preview: {ocr_result['text'][:100]}..." if len(ocr_result['text']) > 100 else f"    OCR Text: {ocr_result['text']}")
                    else:
                        self.logger.debug(f"  - Image {img_index + 1}: OCR failed or no text found")
            
            # Extract tables (using tabula-py or camelot)
            tables = self._extract_tables_from_page(file_path, page_num + 1)
            page_data['tables'] = tables
            
            # ADD LOGGING: Table extraction
            if tables:
                self.logger.debug(f"📄 Page {page_num + 1}: Found {len(tables)} tables")
                for table_idx, table in enumerate(tables):
                    table_text_length = len(table.get('text', ''))
                    self.logger.debug(f"  - Table {table_idx + 1}: {table_text_length} chars, accuracy: {table.get('accuracy', 'N/A')}")
            
            # Extract annotations
            annotations = self._extract_annotations(page)
            page_data['annotations'] = annotations
            
            # ADD LOGGING: Page processing summary
            processing_time = (datetime.now() - page_start).total_seconds()
            final_text_length = len(page_data['text'])
            
            self.logger.info(f"📄 PDF Page {page_num + 1} Processed:")
            self.logger.info(f"  - Text length: {final_text_length} chars (original: {original_page_text_length})")
            self.logger.info(f"  - Images found: {len(page_data['images'])}")
            self.logger.info(f"  - Tables found: {len(page_data['tables'])}")
            self.logger.info(f"  - Annotations: {len(page_data['annotations'])}")
            self.logger.info(f"  - Processing time: {processing_time:.2f}s")
            
            result['pages'].append(page_data)
        
        # Close the PDF document
        pdf_document.close()
        
        # ADD LOGGING: Before creating chunks
        total_text_length = sum(len(page['text']) for page in result['pages'])
        total_images = sum(len(page['images']) for page in result['pages'])
        total_tables = sum(len(page['tables']) for page in result['pages'])
        total_annotations = sum(len(page.get('annotations', [])) for page in result['pages'])
        
        self.logger.info(f"📄 PDF Processing Complete - Creating chunks from {len(result['pages'])} pages")
        self.logger.info(f"📄 Content Summary:")
        self.logger.info(f"  - Total text: {total_text_length:,} chars")
        self.logger.info(f"  - Total images: {total_images}")
        self.logger.info(f"  - Total tables: {total_tables}")
        self.logger.info(f"  - Total annotations: {total_annotations}")
        
        # Create enriched chunks
        result['chunks'] = self._create_enriched_chunks(result)
        
        # Processing summary
        processing_time = (datetime.now() - start_time).total_seconds()
        result['processing_end'] = datetime.now().isoformat()
        result['processing_time_seconds'] = processing_time
        
        self.logger.info(f"✅ PDF processing completed in {processing_time:.2f}s")
        self.logger.info(f"📄 Final Result: {len(result['chunks'])} chunks created")
        
        # ADD LOGGING: Save debug data if enabled
        if os.getenv('RAG_SAVE_EXTRACTION_DUMPS', 'false').lower() == 'true' or self.logger.isEnabledFor(logging.DEBUG):
            debug_file = f"debug_pdf_extract_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            debug_path = Path("data/logs") / debug_file
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a serializable version
            debug_result = {k: v for k, v in result.items() if k != 'chunks'}
            debug_result['chunk_count'] = len(result['chunks'])
            debug_result['chunk_preview'] = [
                {
                    'text_length': len(chunk['text']),
                    'text_preview': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                    'metadata': chunk.get('metadata', {})
                }
                for chunk in result['chunks'][:3]  # First 3 chunks
            ]
            
            try:
                with open(debug_path, 'w', encoding='utf-8') as f:
                    json.dump(debug_result, f, indent=2, ensure_ascii=False, default=str)
                self.logger.debug(f"Full PDF extraction saved to {debug_path}")
            except Exception as e:
                self.logger.warning(f"Failed to save debug data: {e}")
        
        return result
    
    def _extract_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract PDF metadata"""
        metadata = {
            'processor': 'enhanced_pdf',
            'timestamp': datetime.now().isoformat(),
            'file_size': file_path.stat().st_size,
            'file_name': file_path.name
        }
        
        if not HAS_PDF_LIBS:
            return metadata
        
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if reader.metadata:
                    metadata.update({
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'subject': reader.metadata.get('/Subject', ''),
                        'creator': reader.metadata.get('/Creator', ''),
                        'producer': reader.metadata.get('/Producer', ''),
                        'creation_date': str(reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(reader.metadata.get('/ModDate', '')),
                        'keywords': reader.metadata.get('/Keywords', ''),
                        'page_count': len(reader.pages),
                        'is_encrypted': reader.is_encrypted,
                        'pdf_version': reader.pdf_header
                    })
        except Exception as e:
            self.logger.error(f"Failed to extract PDF metadata: {e}")
            metadata['metadata_error'] = str(e)
        
        return metadata
    
    def _extract_image(self, pdf_document, xref):
        """Extract image from PDF"""
        try:
            pix = fitz.Pixmap(pdf_document, xref)
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                img_data = pix.tobytes("png")
            else:  # CMYK
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix1.tobytes("png")
                pix1 = None
            pix = None
            return img_data
        except Exception as e:
            self.logger.error(f"Failed to extract image: {e}")
            return None
    
    def _extract_tables_from_page(self, file_path: str, page_num: int) -> List[Dict]:
        """Extract tables from PDF page"""
        try:
            import camelot
            tables = camelot.read_pdf(
                file_path,
                pages=str(page_num),
                flavor='stream'  # or 'lattice' for bordered tables
            )
            
            table_data = []
            for table in tables:
                table_data.append({
                    'data': table.df.to_dict('records'),
                    'accuracy': table.accuracy,
                    'text': table.df.to_string()
                })
            return table_data
        except Exception as e:
            self.logger.warning(f"Table extraction failed: {e}")
            return []
    
    def _extract_annotations(self, page) -> List[Dict]:
        """Extract annotations, comments, and highlights"""
        annotations = []
        
        for annot in page.annots():
            annot_dict = {
                'type': annot.type[1],  # Annotation type name
                'content': annot.info.get('content', ''),
                'author': annot.info.get('title', ''),
                'page': page.number + 1,
                'rect': list(annot.rect),  # Position on page
                'created': annot.info.get('creationDate', '')
            }
            
            # Extract highlighted text
            if annot.type[0] == 8:  # Highlight annotation
                highlighted_text = page.get_textbox(annot.rect)
                annot_dict['highlighted_text'] = highlighted_text
            
            annotations.append(annot_dict)
        
        return annotations
    
    def _create_enriched_chunks(self, processed_data: Dict) -> List[Dict]:
        """Create chunks with flat metadata structure compatible with metadata manager"""
        chunks = []
        
        # ADD LOGGING: Start of chunk creation
        self.logger.info(f"🔧 Creating enriched chunks from {len(processed_data['pages'])} pages")
        
        for page_num, page_data in enumerate(processed_data['pages']):
            # Chunk page text
            page_text = page_data['text']
            original_text_length = len(page_text)
            
            # Add image OCR text context
            ocr_text_added = 0
            if page_data['images']:
                for img in page_data['images']:
                    if img.get('ocr_text'):
                        ocr_addition = f"\n\n[Image on page {page_num + 1}]: {img['ocr_text']}"
                        page_text += ocr_addition
                        ocr_text_added += len(ocr_addition)
                
                # ADD LOGGING: After adding image text
                self.logger.debug(f"Page {page_data['page_number']}: Added {ocr_text_added} chars from {len(page_data['images'])} images")
            
            # Add table context
            table_text_added = 0
            if page_data['tables']:
                for table_idx, table in enumerate(page_data['tables']):
                    table_addition = f"\n\n[Table {table_idx + 1} on page {page_num + 1}]:\n{table.get('text', '')}"
                    page_text += table_addition
                    table_text_added += len(table_addition)
                
                # ADD LOGGING: After adding table text
                self.logger.debug(f"Page {page_data['page_number']}: Added {table_text_added} chars from {len(page_data['tables'])} tables")
            
            # Create chunk with flat metadata structure
            chunk = {
                'text': page_text.strip(),
                'metadata': {
                    'source_type': 'pdf',
                    'content_type': 'page_content',
                    'page_number': page_data['page_number'],
                    'has_images': len(page_data['images']) > 0,
                    'image_count': len(page_data['images']),
                    'has_tables': len(page_data['tables']) > 0,
                    'table_count': len(page_data['tables']),
                    'has_annotations': len(page_data.get('annotations', [])) > 0,
                    'annotation_count': len(page_data.get('annotations', [])),
                    'extraction_method': 'azure_computer_vision',
                    'pdf_title': processed_data['metadata'].get('title', ''),
                    'pdf_author': processed_data['metadata'].get('author', ''),
                    'pdf_page_count': processed_data['metadata'].get('page_count', 0),
                    'processor': 'enhanced_pdf',
                    # Text metrics for debugging
                    'original_text_length': original_text_length,
                    'enriched_text_length': len(page_text.strip()),
                    'ocr_text_added': ocr_text_added,
                    'table_text_added': table_text_added
                }
            }
            
            # ADD LOGGING: Chunk created
            self.logger.debug(f"Created chunk for page {page_data['page_number']}: {len(chunk['text'])} chars total")
            self.logger.debug(f"  - Original text: {original_text_length} chars")
            self.logger.debug(f"  - OCR text added: {ocr_text_added} chars")
            self.logger.debug(f"  - Table text added: {table_text_added} chars")
            
            chunks.append(chunk)
        
        # ADD LOGGING: Summary
        self.logger.info(f"✅ Created {len(chunks)} enriched chunks")
        self.logger.info(f"   Total text length: {sum(len(c['text']) for c in chunks)} chars")
        self.logger.info(f"   Azure CV OCR used: {'Yes' if self.azure_client else 'No'}")
        
        return chunks