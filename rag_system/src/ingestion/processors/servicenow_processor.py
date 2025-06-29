# -*- coding: utf-8 -*-
"""
ServiceNow Processor
Enhanced with comprehensive logging and JSON data analysis
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from .base_processor import BaseProcessor
except ImportError:
    class BaseProcessor:
        def __init__(self, config=None):
            self.config = config or {}
            self.logger = logging.getLogger(__name__)


class ServiceNowProcessor(BaseProcessor):
    """ServiceNow ticket processor with comprehensive logging"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ServiceNow processor"""
        super().__init__(config)
        self.supported_extensions = ['servicenow']  # Special identifier
        
        # Debug configuration
        self.extraction_debug = os.getenv('RAG_EXTRACTION_DEBUG', 'false').lower() == 'true'
        self.save_extraction_dumps = os.getenv('RAG_SAVE_EXTRACTION_DUMPS', 'false').lower() == 'true'
        
        if self.extraction_debug:
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("🔍 ServiceNow Processor - Debug mode enabled")
        
        self.logger.info("ServiceNow processor initialized")
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed by this processor"""
        return 'servicenow' in file_path.lower() or file_path.lower().endswith('.json')
    
    def process(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process ServiceNow/JSON data with comprehensive logging"""
        start_time = datetime.now()
        file_path_obj = Path(file_path)
        
        self.logger.info(f"🎫 Starting ServiceNow/JSON processing: {file_path}")
        self.logger.info(f"🎫 File type: JSON | File size: {file_path_obj.stat().st_size:,} bytes")
        self.logger.info(f"🎫 Processor: ServiceNowProcessor")
        
        if not file_path_obj.exists():
            error_msg = f"File not found: {file_path}"
            self.logger.error(f"❌ {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'processor': 'servicenow'
            }
        
        try:
            # Read and parse JSON data
            self.logger.debug(f"🎫 Reading JSON file...")
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Analyze JSON structure
            data_analysis = self._analyze_json_structure(json_data)
            self.logger.info(f"🎫 JSON Structure Analysis:")
            self.logger.info(f"  - Data type: {data_analysis['data_type']}")
            self.logger.info(f"  - Total records: {data_analysis['record_count']}")
            self.logger.info(f"  - Structure depth: {data_analysis['max_depth']}")
            self.logger.info(f"  - Field count: {data_analysis['field_count']}")
            self.logger.info(f"  - ServiceNow detected: {'Yes' if data_analysis['is_servicenow'] else 'No'}")
            
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"  - Sample fields: {data_analysis['sample_fields'][:10]}")
                self.logger.debug(f"  - Data preview: {str(json_data)[:300]}...")
            
            # Process the data
            result = {
                'status': 'success',
                'file_path': str(file_path_obj),
                'file_name': file_path_obj.name,
                'file_size': file_path_obj.stat().st_size,
                'processing_start': start_time.isoformat(),
                'data_analysis': data_analysis,
                'metadata': {
                    'processor': 'servicenow',
                    'timestamp': datetime.now().isoformat(),
                    'is_servicenow_data': data_analysis['is_servicenow'],
                    'record_count': data_analysis['record_count'],
                    'structure_type': data_analysis['data_type'],
                    **(metadata or {})
                },
                'chunks': []
            }
            
            # Create chunks based on data structure
            chunks = self._create_chunks_from_json(json_data, data_analysis, file_path_obj)
            result['chunks'] = chunks
            
            # Processing summary
            processing_time = (datetime.now() - start_time).total_seconds()
            result['processing_end'] = datetime.now().isoformat()
            result['processing_time_seconds'] = processing_time
            
            self.logger.info(f"✅ ServiceNow/JSON processing completed in {processing_time:.2f}s")
            self.logger.info(f"🎫 Final Result:")
            self.logger.info(f"  - Records processed: {data_analysis['record_count']}")
            self.logger.info(f"  - Chunks created: {len(chunks)}")
            self.logger.info(f"  - Total text length: {sum(len(chunk['text']) for chunk in chunks):,} chars")
            
            # Log chunk details
            if chunks and self.logger.isEnabledFor(logging.DEBUG):
                for i, chunk in enumerate(chunks[:3]):  # First 3 chunks
                    self.logger.debug(f"Chunk {i} preview: {chunk['text'][:200]}...")
                    chunk_metadata = chunk.get('metadata', {})
                    self.logger.debug(f"Chunk {i} metadata: {list(chunk_metadata.keys())}")
            
            # Save debug data if enabled
            if self.save_extraction_dumps or self.logger.isEnabledFor(logging.DEBUG):
                debug_file = f"debug_servicenow_extract_{file_path_obj.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                debug_path = Path("data/logs") / debug_file
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create a serializable version
                debug_result = {k: v for k, v in result.items() if k != 'chunks'}
                debug_result['chunk_count'] = len(chunks)
                debug_result['chunk_preview'] = [
                    {
                        'text_length': len(chunk['text']),
                        'text_preview': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                        'metadata': chunk.get('metadata', {})
                    }
                    for chunk in chunks[:3]  # First 3 chunks
                ]
                
                try:
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        json.dump(debug_result, f, indent=2, ensure_ascii=False, default=str)
                    self.logger.debug(f"Full ServiceNow extraction saved to {debug_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to save debug data: {e}")
            
            return result
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ {error_msg} (after {processing_time:.2f}s)")
            return {
                'status': 'error',
                'error': error_msg,
                'processor': 'servicenow',
                'processing_time_seconds': processing_time
            }
        except Exception as e:
            error_msg = f"ServiceNow processing failed: {str(e)}"
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ {error_msg} (after {processing_time:.2f}s)")
            return {
                'status': 'error',
                'error': error_msg,
                'processor': 'servicenow',
                'processing_time_seconds': processing_time
            }
    
    def _analyze_json_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze JSON data structure and content"""
        analysis = {
            'data_type': type(data).__name__,
            'record_count': 0,
            'max_depth': 0,
            'field_count': 0,
            'sample_fields': [],
            'is_servicenow': False,
            'servicenow_indicators': []
        }
        
        if isinstance(data, list):
            analysis['record_count'] = len(data)
            if data:
                # Analyze first record
                first_record = data[0]
                if isinstance(first_record, dict):
                    analysis['field_count'] = len(first_record.keys())
                    analysis['sample_fields'] = list(first_record.keys())
                    analysis['max_depth'] = self._calculate_depth(first_record)
                    
                    # Check for ServiceNow indicators
                    servicenow_fields = ['number', 'sys_id', 'created', 'assigned_to', 'priority', 'category', 'state']
                    found_indicators = [field for field in servicenow_fields if field in first_record]
                    analysis['servicenow_indicators'] = found_indicators
                    analysis['is_servicenow'] = len(found_indicators) >= 3
                    
        elif isinstance(data, dict):
            analysis['record_count'] = 1
            analysis['field_count'] = len(data.keys())
            analysis['sample_fields'] = list(data.keys())
            analysis['max_depth'] = self._calculate_depth(data)
            
            # Check for ServiceNow indicators
            servicenow_fields = ['number', 'sys_id', 'created', 'assigned_to', 'priority', 'category', 'state']
            found_indicators = [field for field in servicenow_fields if field in data]
            analysis['servicenow_indicators'] = found_indicators
            analysis['is_servicenow'] = len(found_indicators) >= 3
        
        return analysis
    
    def _calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate the maximum depth of nested structures"""
        if not isinstance(obj, (dict, list)):
            return current_depth
        
        max_depth = current_depth
        if isinstance(obj, dict):
            for value in obj.values():
                depth = self._calculate_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        elif isinstance(obj, list):
            for item in obj:
                depth = self._calculate_depth(item, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _create_chunks_from_json(self, data: Any, analysis: Dict[str, Any], file_path: Path) -> List[Dict[str, Any]]:
        """Create chunks from JSON data based on structure"""
        chunks = []
        
        if isinstance(data, list) and data:
            # Process each record as a separate chunk
            for i, record in enumerate(data):
                if isinstance(record, dict):
                    chunk_text = self._format_record_as_text(record, analysis['is_servicenow'])
                    
                    chunk = {
                        'text': chunk_text,
                        'metadata': {
                            'source_type': 'servicenow' if analysis['is_servicenow'] else 'json',
                            'content_type': 'record',
                            'record_index': i,
                            'record_id': record.get('number') or record.get('sys_id') or f"record_{i}",
                            'total_records': len(data),
                            'processor': 'servicenow',
                            'file_name': file_path.name,
                            'is_servicenow_data': analysis['is_servicenow']
                        }
                    }
                    chunks.append(chunk)
                    
                    # Log individual record processing
                    if self.logger.isEnabledFor(logging.DEBUG):
                        record_id = record.get('number') or record.get('sys_id') or f"record_{i}"
                        self.logger.debug(f"🎫 Processed record {i+1}/{len(data)}: {record_id}")
                        self.logger.debug(f"  - Text length: {len(chunk_text)} chars")
                        self.logger.debug(f"  - Fields: {list(record.keys())[:5]}...")
        
        elif isinstance(data, dict):
            # Single record
            chunk_text = self._format_record_as_text(data, analysis['is_servicenow'])
            
            chunk = {
                'text': chunk_text,
                'metadata': {
                    'source_type': 'servicenow' if analysis['is_servicenow'] else 'json',
                    'content_type': 'single_record',
                    'record_id': data.get('number') or data.get('sys_id') or 'single_record',
                    'processor': 'servicenow',
                    'file_name': file_path.name,
                    'is_servicenow_data': analysis['is_servicenow']
                }
            }
            chunks.append(chunk)
        
        else:
            # Fallback for other data types
            chunk_text = f"JSON Data from {file_path.name}:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
            
            chunk = {
                'text': chunk_text,
                'metadata': {
                    'source_type': 'json',
                    'content_type': 'raw_data',
                    'processor': 'servicenow',
                    'file_name': file_path.name,
                    'data_type': analysis['data_type']
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def _format_record_as_text(self, record: Dict[str, Any], is_servicenow: bool) -> str:
        """Format a record as readable text"""
        if is_servicenow:
            return self._format_servicenow_record(record)
        else:
            return self._format_generic_record(record)
    
    def _format_servicenow_record(self, record: Dict[str, Any]) -> str:
        """Format ServiceNow ticket as readable text"""
        text_parts = []
        
        # Header information
        if 'number' in record:
            text_parts.append(f"Incident: {record['number']}")
        
        if 'priority' in record:
            text_parts.append(f"Priority: {record['priority']}")
            
        if 'category' in record and 'subcategory' in record:
            text_parts.append(f"Category: {record['category']} - {record['subcategory']}")
        elif 'category' in record:
            text_parts.append(f"Category: {record['category']}")
        
        # Timing information
        if 'created' in record:
            text_parts.append(f"Created: {record['created']}")
        if 'resolved' in record:
            text_parts.append(f"Resolved: {record['resolved']}")
        
        # People and location
        if 'reporter' in record:
            text_parts.append(f"Reporter: {record['reporter']}")
        if 'assigned_to' in record:
            text_parts.append(f"Assigned to: {record['assigned_to']}")
        if 'location' in record:
            text_parts.append(f"Location: {record['location']}")
        
        # Description and resolution
        if 'short_description' in record:
            text_parts.append(f"Summary: {record['short_description']}")
        if 'description' in record:
            text_parts.append(f"Description: {record['description']}")
        if 'resolution' in record:
            text_parts.append(f"Resolution: {record['resolution']}")
        
        # Work notes
        if 'work_notes' in record and isinstance(record['work_notes'], list):
            text_parts.append("Work Notes:")
            for note in record['work_notes']:
                text_parts.append(f"  - {note}")
        
        # Related information
        if 'related_manager' in record:
            text_parts.append(f"Related Manager: {record['related_manager']}")
        if 'related_building' in record:
            text_parts.append(f"Related Building: {record['related_building']}")
        
        # Add any remaining fields
        processed_fields = {
            'number', 'priority', 'category', 'subcategory', 'created', 'resolved',
            'reporter', 'assigned_to', 'location', 'short_description', 'description',
            'resolution', 'work_notes', 'related_manager', 'related_building'
        }
        
        remaining_fields = set(record.keys()) - processed_fields
        if remaining_fields:
            text_parts.append("Additional Information:")
            for field in sorted(remaining_fields):
                value = record[field]
                if isinstance(value, (str, int, float)):
                    text_parts.append(f"  {field}: {value}")
                elif isinstance(value, list):
                    text_parts.append(f"  {field}: {', '.join(str(v) for v in value)}")
                else:
                    text_parts.append(f"  {field}: {str(value)}")
        
        return '\n'.join(text_parts)
    
    def _format_generic_record(self, record: Dict[str, Any]) -> str:
        """Format generic JSON record as readable text"""
        text_parts = []
        
        for key, value in record.items():
            if isinstance(value, (str, int, float)):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, list):
                if value and isinstance(value[0], str):
                    text_parts.append(f"{key}: {', '.join(value)}")
                else:
                    text_parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            elif isinstance(value, dict):
                text_parts.append(f"{key}: {json.dumps(value, indent=2, ensure_ascii=False)}")
            else:
                text_parts.append(f"{key}: {str(value)}")
        
        return '\n'.join(text_parts)


def create_servicenow_processor(config: Optional[Dict[str, Any]] = None) -> ServiceNowProcessor:
    """Factory function to create ServiceNow processor"""
    return ServiceNowProcessor(config) 