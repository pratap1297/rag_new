"""
Configuration Management for RAG System
Handles loading, validation, and management of system configuration
"""
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class DatabaseConfig:
    """Database configuration"""
    faiss_index_path: str = "data/vectors/index.faiss"
    metadata_path: str = "data/metadata"
    backup_path: str = "data/backups"
    max_backup_count: int = 5

@dataclass
class EmbeddingConfig:
    """Embedding model configuration"""
    provider: str = "azure"  # sentence-transformers, cohere, azure
    model_name: str = "Cohere-embed-v3-english"
    dimension: int = 1024  # Cohere v3 dimension
    batch_size: int = 96
    device: str = "cpu"
    api_key: Optional[str] = None

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "azure"  # groq, openai, cohere, azure
    model_name: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 1000

@dataclass
class APIConfig:
    """API server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    cors_origins: list = None
    health_check_timeout: float = 10.0  # 10 seconds for health checks
    stats_timeout: float = 10.0  # 10 seconds for stats operations
    llm_test_timeout: float = 15.0  # 15 seconds for LLM test operations

@dataclass
class IngestionConfig:
    """Data ingestion configuration"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    supported_formats: list = None
    max_file_size_mb: int = 100
    batch_size: int = 10
    timeout: float = 300.0  # 5 minutes default for text ingestion
    file_timeout: float = 600.0  # 10 minutes default for file processing

@dataclass
class RetrievalConfig:
    """Retrieval configuration"""
    top_k: int = 5
    similarity_threshold: float = 0.7  # Good default for normalized cosine similarity (range -1 to 1)
    rerank_top_k: int = 3
    enable_reranking: bool = True

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_format: str = "json"

@dataclass
class FolderMonitoringConfig:
    """Folder monitoring configuration"""
    enabled: bool = True
    check_interval_seconds: int = 60
    monitored_folders: list = None
    supported_extensions: list = None
    max_file_size_mb: int = 100
    auto_ingest: bool = True
    recursive: bool = True
    
    def __post_init__(self):
        if self.monitored_folders is None:
            self.monitored_folders = []
        if self.supported_extensions is None:
            self.supported_extensions = [".txt", ".md", ".pdf", ".docx", ".json", ".csv"]

@dataclass
class AzureAIConfig:
    """Azure AI services configuration"""
    computer_vision_endpoint: str = ""
    computer_vision_key: str = ""
    document_intelligence_endpoint: str = ""  # Optional
    document_intelligence_key: str = ""  # Optional
    max_image_size_mb: int = 4
    ocr_language: str = "en"
    enable_handwriting: bool = True
    enable_document_intelligence: bool = False  # Optional feature

@dataclass
class SystemConfig:
    """Main system configuration"""
    environment: str = "development"
    debug: bool = False
    data_dir: str = "data"
    log_dir: str = "logs"
    
    # Component configs
    database: DatabaseConfig = None
    embedding: EmbeddingConfig = None
    llm: LLMConfig = None
    api: APIConfig = None
    ingestion: IngestionConfig = None
    retrieval: RetrievalConfig = None
    monitoring: MonitoringConfig = None
    folder_monitoring: FolderMonitoringConfig = None
    azure_ai: AzureAIConfig = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.embedding is None:
            self.embedding = EmbeddingConfig()
        if self.llm is None:
            self.llm = LLMConfig()
        if self.api is None:
            self.api = APIConfig()
            self.api.cors_origins = ["*"] if self.debug else []
        if self.ingestion is None:
            self.ingestion = IngestionConfig()
            self.ingestion.supported_formats = [".pdf", ".docx", ".txt", ".md"]
        if self.retrieval is None:
            self.retrieval = RetrievalConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()
        if self.folder_monitoring is None:
            self.folder_monitoring = FolderMonitoringConfig()
        if self.azure_ai is None:
            self.azure_ai = AzureAIConfig()

class ConfigManager:
    """Configuration manager with environment overrides"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "data/config/system_config.json"
        self.config = self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self) -> SystemConfig:
        """Load configuration from file or create default"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                return self._dict_to_config(config_data)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
        
        return SystemConfig()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> SystemConfig:
        """Convert dictionary to SystemConfig"""
        # Extract nested configs
        database_data = data.pop('database', {})
        embedding_data = data.pop('embedding', {})
        llm_data = data.pop('llm', {})
        api_data = data.pop('api', {})
        ingestion_data = data.pop('ingestion', {})
        retrieval_data = data.pop('retrieval', {})
        monitoring_data = data.pop('monitoring', {})
        folder_monitoring_data = data.pop('folder_monitoring', {})
        azure_ai_data = data.pop('azure_ai', {})
        
        config = SystemConfig(**data)
        config.database = DatabaseConfig(**database_data)
        config.embedding = EmbeddingConfig(**embedding_data)
        config.llm = LLMConfig(**llm_data)
        config.api = APIConfig(**api_data)
        config.ingestion = IngestionConfig(**ingestion_data)
        config.retrieval = RetrievalConfig(**retrieval_data)
        config.monitoring = MonitoringConfig(**monitoring_data)
        config.folder_monitoring = FolderMonitoringConfig(**folder_monitoring_data)
        config.azure_ai = AzureAIConfig(**azure_ai_data)
        
        return config
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # System level
        self.config.environment = os.getenv('RAG_ENVIRONMENT', self.config.environment)
        self.config.debug = os.getenv('RAG_DEBUG', str(self.config.debug)).lower() == 'true'
        
        # LLM config
        if os.getenv('RAG_LLM_API_KEY'):
            self.config.llm.api_key = os.getenv('RAG_LLM_API_KEY')
        if os.getenv('RAG_LLM_PROVIDER'):
            self.config.llm.provider = os.getenv('RAG_LLM_PROVIDER')
        if os.getenv('RAG_LLM_MODEL'):
            self.config.llm.model_name = os.getenv('RAG_LLM_MODEL')
        
        # Provider-specific API keys
        if os.getenv('GROQ_API_KEY'):
            if self.config.llm.provider == 'groq':
                self.config.llm.api_key = os.getenv('GROQ_API_KEY')
        if os.getenv('OPENAI_API_KEY'):
            if self.config.llm.provider == 'openai':
                self.config.llm.api_key = os.getenv('OPENAI_API_KEY')
        if os.getenv('COHERE_API_KEY'):
            if self.config.llm.provider == 'cohere':
                self.config.llm.api_key = os.getenv('COHERE_API_KEY')
            # Also set for embedding if using Cohere
            if self.config.embedding.provider == 'cohere':
                self.config.embedding.api_key = os.getenv('COHERE_API_KEY')
        if os.getenv('AZURE_API_KEY'):
            if self.config.llm.provider == 'azure':
                self.config.llm.api_key = os.getenv('AZURE_API_KEY')
            # Also set for embedding if using Azure
            if self.config.embedding.provider == 'azure':
                self.config.embedding.api_key = os.getenv('AZURE_API_KEY')
        
        # Embedding config
        if os.getenv('RAG_EMBEDDING_PROVIDER'):
            self.config.embedding.provider = os.getenv('RAG_EMBEDDING_PROVIDER')
        if os.getenv('RAG_EMBEDDING_MODEL'):
            self.config.embedding.model_name = os.getenv('RAG_EMBEDDING_MODEL')
        
        # Dynamically calculate embedding dimension based on provider and model
        from .constants import get_embedding_dimension
        self.config.embedding.dimension = get_embedding_dimension(
            self.config.embedding.provider, 
            self.config.embedding.model_name
        )
        
        # API config
        if os.getenv('RAG_API_HOST'):
            self.config.api.host = os.getenv('RAG_API_HOST')
        if os.getenv('RAG_API_PORT'):
            self.config.api.port = int(os.getenv('RAG_API_PORT'))
        
        # Monitoring
        if os.getenv('RAG_LOG_LEVEL'):
            self.config.monitoring.log_level = os.getenv('RAG_LOG_LEVEL')
        
        # Azure AI config
        if os.getenv('AZURE_CV_ENDPOINT'):
            self.config.azure_ai.computer_vision_endpoint = os.getenv('AZURE_CV_ENDPOINT')
        if os.getenv('AZURE_CV_KEY'):
            self.config.azure_ai.computer_vision_key = os.getenv('AZURE_CV_KEY')
        if os.getenv('AZURE_DI_ENDPOINT'):
            self.config.azure_ai.document_intelligence_endpoint = os.getenv('AZURE_DI_ENDPOINT')
        if os.getenv('AZURE_DI_KEY'):
            self.config.azure_ai.document_intelligence_key = os.getenv('AZURE_DI_KEY')
    
    def get_config(self, component: Optional[str] = None) -> Any:
        """Get configuration for specific component or entire config"""
        if component is None:
            return self.config
        
        return getattr(self.config, component, None)
    
    def save_config(self):
        """Save current configuration to file"""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
    
    def update_config(self, component: str, updates: Dict[str, Any]):
        """Update specific component configuration"""
        if hasattr(self.config, component):
            component_config = getattr(self.config, component)
            for key, value in updates.items():
                if hasattr(component_config, key):
                    setattr(component_config, key, value)
            self.save_config()
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return any issues"""
        issues = {}
        
        # Validate LLM API key
        if not self.config.llm.api_key:
            issues['llm_api_key'] = "LLM API key not configured"
        
        # Validate paths
        data_dir = Path(self.config.data_dir)
        if not data_dir.exists():
            issues['data_dir'] = f"Data directory does not exist: {data_dir}"
        
        # Validate embedding model
        try:
            from sentence_transformers import SentenceTransformer
            # This will validate the model name
            model_name = self.config.embedding.model_name
            if not model_name:
                issues['embedding_model'] = "Embedding model name not specified"
        except ImportError:
            issues['sentence_transformers'] = "sentence-transformers not installed"
        
        return issues 