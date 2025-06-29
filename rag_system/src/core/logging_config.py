#!/usr/bin/env python3
"""
Logging Configuration Manager
Manages logging configuration based on system config file settings
"""
import os
import json
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class LoggingConfigManager:
    """Manages logging configuration from system config"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.logging_config = {}
        self.loggers = {}
        self._load_config()
    
    def _load_config(self):
        """Load logging configuration from system config"""
        try:
            # Try to load from system config file
            config_file = Path("data/config/system_config.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    system_config = json.load(f)
                    self.logging_config = system_config.get('logging', {})
                    print(f"✅ Loaded logging config from {config_file}")
                    return
        except Exception as e:
            print(f"Warning: Could not load logging config: {e}")
        
        # Fallback to default config
        self._load_default_config()
    
    def _load_default_config(self):
        """Load default logging configuration"""
        self.logging_config = {
            "extraction_debug": {
                "enabled": True,
                "level": "INFO",
                "save_dumps": True,
                "dump_location": "data/logs/extraction_dumps",
                "max_dump_files": 50,
                "include_chunk_previews": True,
                "include_metadata_details": True,
                "include_processing_times": True
            },
            "pdf_processing": {
                "enabled": True,
                "level": "INFO",
                "log_azure_api_calls": True,
                "log_ocr_results": True,
                "log_page_details": True,
                "log_image_processing": True,
                "log_table_extraction": True,
                "save_extraction_dumps": True
            },
            "excel_processing": {
                "enabled": True,
                "level": "INFO",
                "log_sheet_analysis": True,
                "log_azure_integration": True,
                "log_cell_processing": True,
                "log_formula_extraction": True,
                "log_image_processing": True,
                "save_extraction_dumps": True
            },
            "ingestion_engine": {
                "enabled": True,
                "level": "INFO",
                "log_processor_selection": True,
                "log_chunk_creation": True,
                "log_performance_metrics": True,
                "log_error_details": True,
                "log_fallback_behavior": True
            },
            "azure_ai": {
                "enabled": True,
                "level": "INFO",
                "log_api_requests": True,
                "log_api_responses": False,
                "log_service_health": True,
                "log_rate_limiting": True,
                "mask_sensitive_data": True
            },
            "general": {
                "console_output": True,
                "file_output": True,
                "max_log_size_mb": 100,
                "backup_count": 5,
                "log_rotation": "daily",
                "timestamp_format": "%Y-%m-%d %H:%M:%S",
                "include_function_names": True,
                "include_line_numbers": True
            }
        }
    
    def is_enabled(self, component: str) -> bool:
        return self.logging_config.get(component, {}).get('enabled', False)
    
    def get_log_level(self, component: str) -> str:
        return self.logging_config.get(component, {}).get('level', 'INFO')
    
    def should_save_dumps(self, component: str) -> bool:
        """Check if component should save extraction dumps"""
        component_config = self.logging_config.get(component, {})
        return component_config.get('save_extraction_dumps', False) or \
               component_config.get('save_dumps', False)
    
    def get_dump_location(self) -> str:
        """Get location for extraction dumps"""
        extraction_config = self.logging_config.get('extraction_debug', {})
        return extraction_config.get('dump_location', 'data/logs/extraction_dumps')
    
    def configure_logger(self, logger_name: str, component: str = None) -> logging.Logger:
        """Configure a logger based on component settings"""
        
        # Determine component from logger name if not provided
        if not component:
            if 'pdf' in logger_name.lower():
                component = 'pdf_processing'
            elif 'excel' in logger_name.lower():
                component = 'excel_processing'
            elif 'ingestion' in logger_name.lower():
                component = 'ingestion_engine'
            elif 'azure' in logger_name.lower():
                component = 'azure_ai'
            else:
                component = 'extraction_debug'
        
        # Get or create logger
        logger = logging.getLogger(logger_name)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Check if logging is enabled for this component
        if not self.is_enabled(component):
            logger.setLevel(logging.CRITICAL + 1)  # Disable logging
            return logger
        
        # Set log level
        log_level = getattr(logging, self.get_log_level(component), logging.INFO)
        logger.setLevel(log_level)
        
        # Configure formatters
        general_config = self.logging_config.get('general', {})
        
        format_parts = ['%(asctime)s', '%(name)s', '%(levelname)s']
        
        if general_config.get('include_function_names', True):
            format_parts.append('%(funcName)s')
        
        if general_config.get('include_line_numbers', True):
            format_parts.append('%(lineno)d')
        
        format_parts.append('%(message)s')
        
        formatter = logging.Formatter(
            ' - '.join(format_parts),
            datefmt=general_config.get('timestamp_format', '%Y-%m-%d %H:%M:%S')
        )
        
        # Add console handler if enabled
        if general_config.get('console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Add file handler if enabled
        if general_config.get('file_output', True):
            log_dir = Path("data/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"{component}_{logger_name.replace('.', '_')}.log"
            
            # Configure rotating file handler
            max_size = general_config.get('max_log_size_mb', 100) * 1024 * 1024
            backup_count = general_config.get('backup_count', 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Store configured logger
        self.loggers[logger_name] = logger
        
        return logger
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current logging configuration"""
        summary = {}
        
        for component, config in self.logging_config.items():
            if isinstance(config, dict):
                summary[component] = {
                    'enabled': config.get('enabled', False),
                    'level': config.get('level', 'INFO'),
                    'features_enabled': sum(1 for k, v in config.items() 
                                          if k.startswith('log_') and v)
                }
        
        return summary
    
    def update_config(self, component: str, settings: Dict[str, Any]):
        """Update configuration for a component"""
        if component not in self.logging_config:
            self.logging_config[component] = {}
        
        self.logging_config[component].update(settings)
        
        # Reconfigure existing loggers for this component
        for logger_name, logger in self.loggers.items():
            if component in logger_name.lower():
                self.configure_logger(logger_name, component)
    
    def enable_component(self, component: str):
        """Enable logging for a component"""
        self.update_config(component, {'enabled': True})
    
    def disable_component(self, component: str):
        """Disable logging for a component"""
        self.update_config(component, {'enabled': False})
    
    def set_log_level(self, component: str, level: str):
        """Set log level for a component"""
        self.update_config(component, {'level': level.upper()})
    
    def create_extraction_dump_file(self, component: str, filename_prefix: str) -> Optional[Path]:
        """Create a new extraction dump file if enabled"""
        if not self.should_save_dumps(component):
            return None
        
        dump_dir = Path(self.get_dump_location())
        dump_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean up old dumps if needed
        extraction_config = self.logging_config.get('extraction_debug', {})
        max_files = extraction_config.get('max_dump_files', 50)
        self._cleanup_old_dumps(dump_dir, max_files)
        
        # Create new dump file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dump_file = dump_dir / f"{filename_prefix}_{timestamp}.json"
        
        return dump_file
    
    def _cleanup_old_dumps(self, dump_dir: Path, max_files: int):
        """Clean up old extraction dump files"""
        try:
            dump_files = list(dump_dir.glob("*.json"))
            if len(dump_files) > max_files:
                # Sort by modification time and remove oldest
                dump_files.sort(key=lambda f: f.stat().st_mtime)
                for old_file in dump_files[:-max_files]:
                    old_file.unlink()
        except Exception as e:
            print(f"Warning: Could not cleanup old dump files: {e}")

# Global logging config manager instance
_logging_config_manager = None

def get_logging_config_manager(config_manager=None) -> LoggingConfigManager:
    """Get the global logging configuration manager"""
    global _logging_config_manager
    if _logging_config_manager is None:
        _logging_config_manager = LoggingConfigManager(config_manager)
    return _logging_config_manager

def configure_extraction_logging(config_manager=None):
    """Configure extraction logging based on system config"""
    logging_manager = get_logging_config_manager(config_manager)
    
    # Configure loggers for each component
    components = {
        'EnhancedPDFProcessor': 'pdf_processing',
        'RobustExcelProcessor': 'excel_processing', 
        'IngestionEngine': 'ingestion_engine',
        'AzureAIClient': 'azure_ai',
        'RobustAzureAIClient': 'azure_ai'
    }
    
    configured_loggers = {}
    for logger_name, component in components.items():
        logger = logging_manager.configure_logger(logger_name, component)
        configured_loggers[logger_name] = logger
    
    return configured_loggers, logging_manager 