#!/usr/bin/env python3
"""
RAG System Setup Script
Initialize the project structure and default configurations
"""
import os
import json
import sys
from pathlib import Path

def create_directory_structure():
    """Create the complete directory structure"""
    directories = [
        "data/metadata/config",
        "data/vectors", 
        "data/uploads",
        "data/logs",
        "data/backups",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structure created")

def create_default_configs():
    """Create default configuration files"""
    
    # System configuration
    system_config = {
        "environment": "development",
        "debug": True,
        "data_dir": "data",
        "log_dir": "logs",
        "database": {
            "faiss_index_path": "data/vectors/index.faiss",
            "metadata_path": "data/metadata",
            "backup_path": "data/backups",
            "max_backup_count": 5
        },
        "embedding": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "dimension": 384,
            "batch_size": 32,
            "device": "cpu"
        },
        "llm": {
            "provider": "groq",
            "model_name": "mixtral-8x7b-32768",
            "api_key": None,
            "temperature": 0.1,
            "max_tokens": 1000
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 1,
            "reload": False,
            "cors_origins": ["*"]
        },
        "ingestion": {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "supported_formats": [".pdf", ".docx", ".txt", ".md"],
            "max_file_size_mb": 100,
            "batch_size": 10
        },
        "retrieval": {
            "top_k": 5,
            "similarity_threshold": 0.7,
            "rerank_top_k": 3,
            "enable_reranking": True
        },
        "monitoring": {
            "enable_metrics": True,
            "metrics_port": 9090,
            "log_level": "INFO",
            "log_format": "json"
        }
    }
    
    config_path = Path("data/config/system_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        json.dump(system_config, f, indent=2)
    
    print("✅ Default configurations created")

def create_env_template():
    """Create environment template file"""
    env_template = """# RAG System Environment Configuration

# API Keys
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# System Configuration
RAG_ENVIRONMENT=development
RAG_DEBUG=true
RAG_DATA_DIR=data
RAG_LOG_DIR=logs

# LLM Configuration
RAG_LLM_PROVIDER=groq
RAG_LLM_MODEL=mixtral-8x7b-32768
RAG_LLM_API_KEY=

# API Configuration
RAG_API_HOST=0.0.0.0
RAG_API_PORT=8000

# Monitoring
RAG_LOG_LEVEL=INFO
"""
    
    with open(".env.template", "w") as f:
        f.write(env_template)
    
    print("✅ Environment template created")

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Environment files
.env
*.env

# Data files
data/
logs/
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backup files
*.bak
*.backup

# FAISS indices
*.faiss
*.index

# Temporary files
*.tmp
*.temp
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore created")

def create_readme():
    """Create README file"""
    readme_content = """# RAG System

Enterprise RAG System with FastAPI, FAISS, and LangGraph

## Quick Start

1. **Setup Environment**
   ```bash
   python scripts/setup.py
   cp .env.template .env
   # Edit .env with your API keys
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the System**
   ```bash
   python main.py
   ```

4. **Access the API**
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## API Usage

### Query the system
```bash
curl -X POST "http://localhost:8000/query" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "What is the company policy?", "top_k": 5}'
```

### Upload a file
```bash
curl -X POST "http://localhost:8000/upload" \\
  -F "file=@document.pdf"
```

## Configuration

Edit `data/config/system_config.json` to customize system behavior.

## License

MIT License
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ README.md created")

def main():
    """Main setup function"""
    print("🚀 Setting up RAG System...")
    print()
    
    create_directory_structure()
    create_default_configs()
    create_env_template()
    create_gitignore()
    create_readme()
    
    print()
    print("✅ RAG System setup completed!")
    print()
    print("Next steps:")
    print("1. Copy .env.template to .env and configure your API keys")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the system: python main.py")
    print()

if __name__ == "__main__":
    main() 