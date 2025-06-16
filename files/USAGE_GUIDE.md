# RAG System Usage Guide

## 🚀 Getting Started

Your RAG system is now configured with Groq and Cohere API keys and ready to use!

### Current Status
✅ **System Configured**: API keys loaded from .env file  
✅ **Dependencies Installed**: All required packages ready  
✅ **Directory Structure**: Data directories created  
✅ **Configuration**: Environment-based config loaded  

## 🎯 How to Use the System

### 1. Start the System

```bash
# Option 1: Simple startup (recommended)
python start.py

# Option 2: Full application with advanced features
python main.py
```

### 2. Verify System is Running

Once started, you should see:
```
🌐 Starting server on http://0.0.0.0:8000
📚 API Documentation: http://0.0.0.0:8000/docs
🛑 Press Ctrl+C to stop the server
```

### 3. Test the System

In a **new terminal window**, run:
```bash
python test_api.py
```

This will test all endpoints and verify everything is working.

## 📊 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload a Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_document.pdf" \
  -F "metadata={\"category\": \"documentation\", \"department\": \"engineering\"}"
```

### Query the System
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the company policy on remote work?",
    "top_k": 5,
    "filters": {"category": "policy"}
  }'
```

### Get System Statistics
```bash
curl http://localhost:8000/stats
```

### View Configuration
```bash
curl http://localhost:8000/config
```

## 🌐 Web Interface

### API Documentation
Visit: **http://localhost:8000/docs**
- Interactive API documentation
- Test endpoints directly in browser
- View request/response schemas

### Optional Gradio UI
If you have Gradio installed, a simple web UI will be available for:
- Uploading documents
- Querying the system
- Viewing responses

## 📁 File Upload Formats

The system supports:
- **PDF files** (.pdf)
- **Word documents** (.docx, .doc)
- **Text files** (.txt)
- **Markdown files** (.md)

### Upload Examples

**Via API:**
```bash
# Upload a PDF with metadata
curl -X POST "http://localhost:8000/upload" \
  -F "file=@company_handbook.pdf" \
  -F "metadata={\"type\": \"handbook\", \"version\": \"2024\"}"

# Upload a text file
curl -X POST "http://localhost:8000/upload" \
  -F "file=@meeting_notes.txt" \
  -F "metadata={\"meeting\": \"weekly_standup\", \"date\": \"2024-01-15\"}"
```

**Via Python:**
```python
import requests

# Upload file
with open("document.pdf", "rb") as f:
    files = {"file": f}
    metadata = {"category": "research", "priority": "high"}
    data = {"metadata": json.dumps(metadata)}
    
    response = requests.post(
        "http://localhost:8000/upload", 
        files=files, 
        data=data
    )
    print(response.json())
```

## 🔍 Querying Examples

### Basic Query
```python
import requests

query_data = {
    "query": "What are the benefits of remote work?",
    "top_k": 5
}

response = requests.post(
    "http://localhost:8000/query",
    json=query_data
)

result = response.json()
print(f"Answer: {result['response']}")
print(f"Sources: {len(result['sources'])}")
```

### Filtered Query
```python
# Query with filters
query_data = {
    "query": "What is the vacation policy?",
    "top_k": 3,
    "filters": {
        "category": "policy",
        "department": "HR"
    }
}

response = requests.post(
    "http://localhost:8000/query",
    json=query_data
)
```

## 🔧 Configuration

### Environment Variables (.env file)
```bash
# LLM Provider API Keys
GROQ_API_KEY=your_groq_key_here
COHERE_API_KEY=your_cohere_key_here
OPENAI_API_KEY=your_openai_key_here

# System Configuration
RAG_ENVIRONMENT=development
RAG_DEBUG=true
RAG_LLM_PROVIDER=groq
RAG_API_PORT=8000
RAG_LOG_LEVEL=INFO
```

### System Configuration (data/config/system_config.json)
```json
{
  "llm": {
    "provider": "groq",
    "model_name": "mixtral-8x7b-32768",
    "temperature": 0.1
  },
  "embedding": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "batch_size": 32
  },
  "ingestion": {
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}
```

## 📈 Monitoring

### Logs
- **Application logs**: `logs/rag_system.log`
- **Error logs**: `logs/errors.log`
- **JSON format**: Structured logging for analysis

### Health Monitoring
```bash
# Check system health
curl http://localhost:8000/health

# Get detailed statistics
curl http://localhost:8000/stats
```

## 🛠️ Troubleshooting

### Common Issues

**1. Server won't start**
```bash
# Check if port is in use
netstat -an | findstr :8000

# Try different port
set RAG_API_PORT=8001
python start.py
```

**2. API key errors**
```bash
# Verify API keys are loaded
python check_env.py

# Check .env file exists and has correct format
```

**3. Upload failures**
```bash
# Check file size (max 100MB by default)
# Check file format is supported
# Verify disk space available
```

**4. Query errors**
```bash
# Check if documents are uploaded
curl http://localhost:8000/stats

# Verify LLM provider is working
# Check API key is valid
```

### Debug Mode
```bash
# Enable debug logging
set RAG_DEBUG=true
set RAG_LOG_LEVEL=DEBUG
python start.py
```

## 🎯 Next Steps

1. **Upload your documents** using the upload endpoint
2. **Test queries** to verify the system understands your content
3. **Integrate with your applications** using the REST API
4. **Monitor performance** through logs and health endpoints
5. **Scale as needed** by adjusting configuration

## 📞 Support

- **Logs**: Check `logs/` directory for detailed information
- **Configuration**: Review `data/config/system_config.json`
- **API Docs**: Visit http://localhost:8000/docs
- **Health Check**: Monitor http://localhost:8000/health

Your RAG system is now ready for production use! 🎉 