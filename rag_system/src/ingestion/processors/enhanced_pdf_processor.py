# -*- coding: utf-8 -*-
"""
Enhanced PDF Processor with Azure Computer Vision Integration
"""
import logging
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
        
    def process(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process PDF with full text, image, and metadata extraction"""
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.logger.info(f"Processing PDF file: {file_path}")
        
        result = {
            'status': 'success',
            'file_path': str(file_path),
            'file_name': file_path.name,
            'pages': [],
            'images': [],
            'tables': [],
            'metadata': self._extract_pdf_metadata(file_path),
            'chunks': []
        }
        
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
        
        for page_num, page in enumerate(pdf_document):
            page_data = {
                'page_number': page_num + 1,
                'text': page.get_text(),
                'images': [],
                'tables': [],
                'annotations': []
            }
            
            # Extract images from page
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                image_data = self._extract_image(pdf_document, xref)
                
                if image_data and self.azure_client:
                    # OCR the image
                    ocr_result = self.azure_client.process_image(
                        image_data,
                        image_type='document'
                    )
                    
                    if ocr_result['success']:
                        page_data['images'].append({
                            'image_index': img_index,
                            'page': page_num + 1,
                            'ocr_text': ocr_result['text'],
                            'regions': ocr_result['regions']
                        })
                        
                        # Add OCR text to page text
                        page_data['text'] += f"\n[Image {img_index}]: {ocr_result['text']}"
            
            # Extract tables (using tabula-py or camelot)
            tables = self._extract_tables_from_page(file_path, page_num + 1)
            page_data['tables'] = tables
            
            # Extract annotations
            annotations = self._extract_annotations(page)
            page_data['annotations'] = annotations
            
            result['pages'].append(page_data)
        
        # Close the PDF document
        pdf_document.close()
        
        # Create enriched chunks
        result['chunks'] = self._create_enriched_chunks(result)
        
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
        
        for page_data in processed_data['pages']:
            # Chunk page text
            page_text = page_data['text']
            
            # Add image OCR text context
            if page_data['images']:
                image_context = "\n".join([
                    f"[Image content: {img['ocr_text'][:100]}...]" 
                    for img in page_data['images']
                ])
                page_text += f"\n\nImages found on page:\n{image_context}"
            
            # Add table context
            if page_data['tables']:
                table_context = "\n".join([
                    f"[Table with {len(table['data'])} rows]"
                    for table in page_data['tables']
                ])
                page_text += f"\n\nTables found on page:\n{table_context}"
            
            # Create chunk with flat metadata structure
            chunk = {
                'text': page_text,
                'metadata': {
                    'source_type': 'pdf',
                    'content_type': 'page_content',
                    'page_number': page_data['page_number'],
                    'has_images': len(page_data['images']) > 0,
                    'image_count': len(page_data['images']),
                    'has_tables': len(page_data['tables']) > 0,
                    'table_count': len(page_data['tables']),
                    'has_annotations': len(page_data['annotations']) > 0,
                    'annotation_count': len(page_data['annotations']),
                    'extraction_method': 'enhanced_with_ocr',
                    'pdf_title': processed_data['metadata'].get('title', ''),
                    'pdf_author': processed_data['metadata'].get('author', ''),
                    'pdf_page_count': processed_data['metadata'].get('page_count', 0)
                }
            }
            
            chunks.append(chunk)
        
        return chunks