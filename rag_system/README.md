# RAG System

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
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the company policy?", "top_k": 5}'
```

### Upload a file
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

## Configuration

Edit `data/config/system_config.json` to customize system behavior.

## License

MIT License
