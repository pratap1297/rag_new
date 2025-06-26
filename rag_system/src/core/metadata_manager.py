"""
Metadata Management System
Comprehensive metadata handling with schema validation and normalization
"""
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path

@dataclass
class MetadataSchema:
    """Define consistent metadata schema"""
    # Required fields
    vector_id: str
    doc_id: str
    chunk_index: int
    text: str
    
    # Document identifiers
    doc_path: Optional[str] = None
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    file_path: Optional[str] = None
    
    # Content metadata
    chunk_size: int = 0
    total_chunks: int = 0
    source_type: str = "unknown"
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None
    ingested_at: Optional[str] = None
    
    # Processing metadata
    processor: Optional[str] = None
    chunking_method: Optional[str] = None
    embedding_model: Optional[str] = None
    
    # Additional metadata (no nesting)
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # System flags
    deleted: bool = False
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                # Handle list fields
                if isinstance(value, list) and not value:
                    continue  # Skip empty lists
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetadataSchema':
        """Create from dictionary with validation"""
        # Extract only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {}
        
        for key, value in data.items():
            if key in known_fields:
                # Handle special field types
                if key == 'tags' and not isinstance(value, list):
                    if isinstance(value, str):
                        filtered_data[key] = [value] if value else []
                    else:
                        filtered_data[key] = []
                else:
                    filtered_data[key] = value
        
        # Ensure required fields have defaults
        if 'vector_id' not in filtered_data:
            filtered_data['vector_id'] = 'unknown'
        if 'doc_id' not in filtered_data:
            filtered_data['doc_id'] = 'unknown'
        if 'chunk_index' not in filtered_data:
            filtered_data['chunk_index'] = 0
        if 'text' not in filtered_data:
            filtered_data['text'] = ''
            
        return cls(**filtered_data)
    
    def validate(self) -> List[str]:
        """Validate the metadata schema"""
        errors = []
        
        if not self.doc_id or self.doc_id == 'unknown':
            errors.append("doc_id is required and cannot be 'unknown'")
        
        if self.chunk_index < 0:
            errors.append("chunk_index must be non-negative")
        
        if not self.text:
            errors.append("text content is required")
        
        if self.chunk_size < 0:
            errors.append("chunk_size must be non-negative")
        
        if self.total_chunks < 0:
            errors.append("total_chunks must be non-negative")
        
        return errors


class MetadataValidator:
    """Validate and normalize metadata"""
    
    RESERVED_KEYS = {
        'vector_id', 'doc_id', 'chunk_index', 'text', 'deleted',
        'created_at', 'updated_at', 'version'
    }
    
    DEPRECATED_KEYS = {
        'metadata': "Nested metadata is deprecated. Use flat structure.",
        'file_name': "Use 'filename' instead of 'file_name'",
        'document_id': "Use 'doc_id' instead of 'document_id'",
        'content': "Use 'text' instead of 'content'",
        'chunk_id': "Use 'chunk_index' instead of 'chunk_id'"
    }
    
    CONFLICTING_KEYS = {
        ('filename', 'file_name'): 'filename',
        ('doc_id', 'document_id'): 'doc_id',
        ('text', 'content'): 'text',
        ('chunk_index', 'chunk_id'): 'chunk_index'
    }
    
    @classmethod
    def validate(cls, metadata: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate metadata and return issues"""
        issues = {
            'errors': [],
            'warnings': [],
            'conflicts': []
        }
        
        # Check for nested metadata (critical error)
        if 'metadata' in metadata:
            if isinstance(metadata['metadata'], dict):
                issues['errors'].append("Nested 'metadata' field detected. This causes double flattening. Use flat structure.")
            else:
                issues['warnings'].append("'metadata' field should be removed. Use flat structure.")
        
        # Check for key conflicts
        for key_pair, preferred in cls.CONFLICTING_KEYS.items():
            if all(key in metadata for key in key_pair):
                issues['conflicts'].append(f"Conflicting keys {key_pair}. Will use '{preferred}'.")
        
        # Check for deprecated keys
        for key, message in cls.DEPRECATED_KEYS.items():
            if key in metadata:
                issues['warnings'].append(f"Deprecated key '{key}': {message}")
        
        # Check required fields
        required_fields = ['text']
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                issues['errors'].append(f"Missing or empty required field: {field}")
        
        # Check data types
        type_checks = {
            'chunk_index': int,
            'chunk_size': int,
            'total_chunks': int,
            'deleted': bool,
            'version': int
        }
        
        for field, expected_type in type_checks.items():
            if field in metadata and not isinstance(metadata[field], expected_type):
                try:
                    # Try to convert
                    metadata[field] = expected_type(metadata[field])
                    issues['warnings'].append(f"Converted '{field}' to {expected_type.__name__}")
                except (ValueError, TypeError):
                    issues['errors'].append(f"'{field}' must be {expected_type.__name__}, got {type(metadata[field]).__name__}")
        
        # Check for very long text fields
        if 'text' in metadata and len(str(metadata['text'])) > 100000:  # 100KB limit
            issues['warnings'].append(f"Text field is very large ({len(str(metadata['text']))} chars). Consider chunking.")
        
        return issues
    
    @classmethod
    def normalize(cls, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize metadata to consistent format"""
        if not metadata:
            return {}
        
        normalized = {}
        
        # Handle nested metadata FIRST to prevent double flattening
        if 'metadata' in metadata and isinstance(metadata['metadata'], dict):
            logging.warning("Flattening nested metadata structure - this should be avoided in future")
            nested = metadata['metadata']
            
            # Add nested fields only if they don't conflict with top-level
            for key, value in nested.items():
                if key not in metadata or key == 'metadata':
                    normalized[key] = value
                else:
                    logging.warning(f"Skipping nested key '{key}' - conflicts with top-level key")
        
        # Copy all non-nested fields
        for key, value in metadata.items():
            if key != 'metadata':  # Skip the nested metadata key itself
                normalized[key] = value
        
        # Resolve key conflicts (use preferred keys)
        for key_pair, preferred in cls.CONFLICTING_KEYS.items():
            if all(key in normalized for key in key_pair):
                # Keep preferred key, remove others
                preferred_value = normalized[preferred]
                for key in key_pair:
                    if key != preferred and key in normalized:
                        logging.info(f"Removing conflicting key '{key}', keeping '{preferred}'")
                        del normalized[key]
                normalized[preferred] = preferred_value
        
        # Handle deprecated key mappings
        if 'file_name' in normalized and 'filename' not in normalized:
            normalized['filename'] = normalized.pop('file_name')
        
        if 'document_id' in normalized and 'doc_id' not in normalized:
            normalized['doc_id'] = normalized.pop('document_id')
        
        if 'content' in normalized and 'text' not in normalized:
            normalized['text'] = normalized.pop('content')
        
        if 'chunk_id' in normalized and 'chunk_index' not in normalized:
            try:
                normalized['chunk_index'] = int(normalized.pop('chunk_id'))
            except (ValueError, TypeError):
                normalized['chunk_index'] = 0
        
        # Ensure required fields have reasonable defaults
        if 'chunk_index' not in normalized:
            normalized['chunk_index'] = 0
        
        if 'created_at' not in normalized:
            normalized['created_at'] = datetime.now().isoformat()
        
        if 'source_type' not in normalized:
            normalized['source_type'] = 'unknown'
        
        # Normalize tags field
        if 'tags' in normalized:
            if isinstance(normalized['tags'], str):
                # Split string tags
                if ',' in normalized['tags']:
                    normalized['tags'] = [tag.strip() for tag in normalized['tags'].split(',')]
                else:
                    normalized['tags'] = [normalized['tags']] if normalized['tags'] else []
            elif not isinstance(normalized['tags'], list):
                normalized['tags'] = []
        
        # Clean up None values and empty strings
        cleaned = {}
        for key, value in normalized.items():
            if value is not None and value != '':
                # Skip empty lists except for tags
                if isinstance(value, list) and not value and key != 'tags':
                    continue
                cleaned[key] = value
        
        return cleaned


class MetadataManager:
    """Manage metadata with consistency and deduplication"""
    
    def __init__(self):
        self.validator = MetadataValidator()
        self._doc_id_cache: Dict[str, str] = {}  # Cache for consistent doc_id generation
        self._vector_id_counter = 0
    
    def generate_vector_id(self, doc_id: str, chunk_index: int) -> str:
        """Generate consistent vector ID"""
        return f"{doc_id}_chunk_{chunk_index}"
    
    def generate_doc_id(self, metadata: Dict[str, Any]) -> str:
        """Generate consistent document ID"""
        # Priority 1: Use existing doc_id if valid
        if metadata.get('doc_id') and metadata['doc_id'] not in ('unknown', '', None):
            return str(metadata['doc_id'])
        
        # Priority 2: Use doc_path
        if metadata.get('doc_path'):
            doc_path = str(metadata['doc_path'])
            cache_key = f"path:{doc_path}"
            if cache_key in self._doc_id_cache:
                return self._doc_id_cache[cache_key]
            
            # Clean up path for use as ID
            doc_id = doc_path.strip('/').replace('/', '_').replace(' ', '_').replace('\\', '_')
            # Remove file extension if present
            if '.' in doc_id:
                doc_id = doc_id.rsplit('.', 1)[0]
            doc_id = f"doc_{doc_id}"
            
            self._doc_id_cache[cache_key] = doc_id
            return doc_id
        
        # Priority 3: Use file_path
        if metadata.get('file_path'):
            file_path = str(metadata['file_path'])
            cache_key = f"filepath:{file_path}"
            if cache_key in self._doc_id_cache:
                return self._doc_id_cache[cache_key]
            
            path_obj = Path(file_path)
            doc_id = f"doc_{path_obj.stem.replace(' ', '_').replace('-', '_')}"
            
            self._doc_id_cache[cache_key] = doc_id
            return doc_id
        
        # Priority 4: Use filename
        if metadata.get('filename'):
            filename = str(metadata['filename'])
            cache_key = f"file:{filename}"
            if cache_key in self._doc_id_cache:
                return self._doc_id_cache[cache_key]
            
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            doc_id = f"doc_{base_name.replace(' ', '_').replace('-', '_')}"
            
            self._doc_id_cache[cache_key] = doc_id
            return doc_id
        
        # Priority 5: Use content hash
        if metadata.get('text'):
            text = str(metadata['text'])
            content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            doc_id = f"doc_hash_{content_hash}"
            return doc_id
        
        # Priority 6: Use title
        if metadata.get('title'):
            title = str(metadata['title'])
            doc_id = f"doc_{title.replace(' ', '_').replace('-', '_')[:50]}"
            return doc_id
        
        # Fallback: timestamp-based ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:17]  # Include microseconds
        return f"doc_{timestamp}"
    
    def merge_metadata(self, *metadata_dicts: Dict[str, Any], 
                      validate: bool = True) -> 'MetadataSchema':
        """Merge multiple metadata dictionaries with conflict resolution"""
        if not metadata_dicts:
            return MetadataSchema.from_dict({})
        
        merged = {}
        conflicts = []
        
        # Merge in order (later dicts override earlier ones)
        for i, meta_dict in enumerate(metadata_dicts):
            if not meta_dict:
                continue
            
            # Normalize each dict first
            try:
                normalized = self.validator.normalize(meta_dict)
            except Exception as e:
                logging.error(f"Failed to normalize metadata dict {i}: {e}")
                continue
            
            # Merge with conflict detection
            for key, value in normalized.items():
                if key in merged and merged[key] != value:
                    # Log conflict but don't fail
                    conflict_msg = f"Metadata conflict for key '{key}': '{merged[key]}' -> '{value}'"
                    conflicts.append(conflict_msg)
                    logging.debug(conflict_msg)
                merged[key] = value
        
        # Validate if requested
        if validate:
            issues = self.validator.validate(merged)
            if issues['errors']:
                error_msg = f"Metadata validation errors: {issues['errors']}"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            if issues['warnings']:
                for warning in issues['warnings']:
                    logging.warning(f"Metadata warning: {warning}")
            
            if issues['conflicts']:
                for conflict in issues['conflicts']:
                    logging.warning(f"Metadata conflict: {conflict}")
        
        # Generate doc_id if missing or invalid
        if not merged.get('doc_id') or merged['doc_id'] in ('unknown', '', None):
            merged['doc_id'] = self.generate_doc_id(merged)
        
        # Generate vector_id if missing
        if not merged.get('vector_id'):
            chunk_index = merged.get('chunk_index', 0)
            merged['vector_id'] = self.generate_vector_id(merged['doc_id'], chunk_index)
        
        # Create schema object
        try:
            schema = MetadataSchema.from_dict(merged)
            
            # Validate the schema
            schema_errors = schema.validate()
            if schema_errors:
                logging.error(f"Schema validation errors: {schema_errors}")
                # Don't raise, but log the issues
            
            return schema
        except Exception as e:
            logging.error(f"Failed to create MetadataSchema: {e}")
            # Return a minimal valid schema
            return MetadataSchema(
                vector_id=merged.get('vector_id', 'unknown'),
                doc_id=merged.get('doc_id', 'unknown'),
                chunk_index=merged.get('chunk_index', 0),
                text=merged.get('text', '')
            )
    
    def prepare_for_storage(self, metadata: MetadataSchema) -> Dict[str, Any]:
        """Prepare metadata for storage in FAISS"""
        # Convert to dict and ensure all required fields
        data = metadata.to_dict()
        
        # Add storage-specific fields
        data['_schema_version'] = 1
        data['_stored_at'] = datetime.now().isoformat()
        
        # Ensure critical fields are present
        if 'text' not in data or not data['text']:
            logging.warning("Storing metadata without text content")
            data['text'] = ''
        
        if 'doc_id' not in data or not data['doc_id']:
            data['doc_id'] = 'unknown'
        
        # Ensure serializable types
        for key, value in data.items():
            if isinstance(value, (datetime,)):
                data[key] = value.isoformat()
            elif isinstance(value, Path):
                data[key] = str(value)
        
        return data
    
    def recover_from_storage(self, stored_data: Dict[str, Any]) -> MetadataSchema:
        """Recover metadata from storage with migration support"""
        if not stored_data:
            return MetadataSchema.from_dict({})
        
        # Handle different schema versions
        schema_version = stored_data.get('_schema_version', 0)
        
        if schema_version == 0:
            # Legacy format - needs migration
            stored_data = self._migrate_legacy_metadata(stored_data)
        
        # Remove storage-specific fields
        storage_fields = {'_schema_version', '_stored_at'}
        cleaned_data = {k: v for k, v in stored_data.items() 
                       if k not in storage_fields}
        
        # Normalize and create schema
        try:
            normalized = self.validator.normalize(cleaned_data)
            return MetadataSchema.from_dict(normalized)
        except Exception as e:
            logging.error(f"Failed to recover metadata from storage: {e}")
            # Return minimal valid schema
            return MetadataSchema(
                vector_id=cleaned_data.get('vector_id', 'unknown'),
                doc_id=cleaned_data.get('doc_id', 'unknown'),
                chunk_index=cleaned_data.get('chunk_index', 0),
                text=cleaned_data.get('text', '')
            )
    
    def _migrate_legacy_metadata(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy metadata format"""
        migrated = {}
        
        # Handle nested metadata (the main source of double flattening)
        if 'metadata' in legacy_data and isinstance(legacy_data['metadata'], dict):
            logging.info("Migrating legacy nested metadata structure")
            nested = legacy_data['metadata']
            
            # Flatten nested structure carefully
            for key, value in nested.items():
                if key not in legacy_data:  # Only add if not already present
                    migrated[key] = value
                else:
                    logging.warning(f"Skipping nested key '{key}' - already exists at top level")
            
            # Copy non-metadata fields
            for key, value in legacy_data.items():
                if key != 'metadata':
                    migrated[key] = value
        else:
            migrated = legacy_data.copy()
        
        # Fix common legacy field mappings
        legacy_mappings = {
            'file_name': 'filename',
            'document_id': 'doc_id',
            'content': 'text',
            'chunk_id': 'chunk_index'
        }
        
        for old_key, new_key in legacy_mappings.items():
            if old_key in migrated and new_key not in migrated:
                migrated[new_key] = migrated.pop(old_key)
                logging.debug(f"Migrated '{old_key}' to '{new_key}'")
        
        # Handle special cases
        if 'chunk_index' in migrated:
            try:
                migrated['chunk_index'] = int(migrated['chunk_index'])
            except (ValueError, TypeError):
                migrated['chunk_index'] = 0
        
        # Mark as migrated
        migrated['_migrated_from_legacy'] = True
        
        return migrated
    
    def get_metadata_stats(self) -> Dict[str, Any]:
        """Get statistics about metadata management"""
        return {
            'doc_id_cache_size': len(self._doc_id_cache),
            'cached_doc_ids': list(self._doc_id_cache.values()),
            'validator_deprecated_keys': len(self.validator.DEPRECATED_KEYS),
            'validator_conflicting_keys': len(self.validator.CONFLICTING_KEYS)
        }
    
    def clear_cache(self):
        """Clear the doc_id cache"""
        self._doc_id_cache.clear()
        logging.info("Metadata manager cache cleared")


# Global metadata manager instance
_global_metadata_manager = None

def get_metadata_manager() -> MetadataManager:
    """Get or create global metadata manager"""
    global _global_metadata_manager
    if _global_metadata_manager is None:
        _global_metadata_manager = MetadataManager()
    return _global_metadata_manager 