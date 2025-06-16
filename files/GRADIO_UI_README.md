# 🎨 RAG System Gradio UI

A user-friendly web interface for testing and interacting with the RAG (Retrieval-Augmented Generation) system.

## 🚀 Quick Start

### Option 1: Launch Everything (Recommended)
```bash
# Install Gradio if not already installed
pip install gradio>=4.0.0

# Launch both API and UI
python launch_ui.py
```

### Option 2: Manual Launch
```bash
# Terminal 1: Start the API server
python main.py

# Terminal 2: Start the Gradio UI
python gradio_ui.py
```

### Option 3: UI Only (if API is already running)
```bash
python launch_ui.py --mode ui-only
```

## 🌐 Access the Interface

Once launched, the interface will be available at:
- **Gradio UI**: http://localhost:7860
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Features

### 🔍 Query System Tab
- **Natural Language Queries**: Ask questions in plain English
- **AI-Powered Responses**: Get intelligent answers based on your knowledge base
- **Source Citations**: See exactly which documents were used to generate answers
- **Adjustable Results**: Control how many source documents to consider
- **Real-time API Status**: Monitor system health

### 📝 Add Content Tab
- **Text Input**: Paste text directly into the system
- **File Upload**: Support for PDF, DOCX, TXT, and Markdown files
- **Metadata Management**: Add titles and descriptions to your content
- **Instant Processing**: Content becomes searchable immediately

### 📊 System Status Tab
- **System Statistics**: View document and vector counts
- **Session History**: Track your activity during the session
- **Performance Monitoring**: Monitor system health and performance

### ❓ Help Tab
- **Complete Documentation**: Step-by-step usage instructions
- **Troubleshooting Guide**: Common issues and solutions
- **Tips & Best Practices**: Get the most out of the system

## 🛠️ Advanced Usage

### Command Line Options
```bash
# Launch with custom ports
python launch_ui.py --api-port 8080 --ui-port 7870

# Launch API only
python launch_ui.py --mode api-only

# Launch UI only (API must be running separately)
python launch_ui.py --mode ui-only

# Launch without opening browser
python launch_ui.py --no-browser
```

### Environment Configuration
The UI automatically detects and connects to the API server. Default settings:
- API URL: `http://localhost:8000`
- UI Port: `7860`
- Auto-refresh: Enabled

## 🔧 Troubleshooting

### Common Issues

**❌ "Connection Error" in UI**
- Ensure the API server is running (`python main.py`)
- Check if port 8000 is available
- Verify the API health at http://localhost:8000/health

**❌ "Port already in use"**
- Use different ports: `python launch_ui.py --ui-port 7861`
- Kill existing processes using the ports

**❌ "File upload failed"**
- Check file format (PDF, DOCX, TXT, MD supported)
- Ensure file is not corrupted
- Try with a smaller file first

**❌ "No results found"**
- Add content to the knowledge base first
- Try different query phrasing
- Check if content was successfully ingested

### Debug Mode
```bash
# Run with verbose logging
python gradio_ui.py --debug

# Check API logs
python main.py --log-level DEBUG
```

## 📱 Interface Overview

### Query System
1. **Enter your question** in the text box
2. **Adjust max results** if needed (1-10)
3. **Click "Ask Question"** to get AI response
4. **Review sources** to understand the answer basis
5. **Check API status** to ensure system health

### Content Addition
1. **Choose input method**: Text input or file upload
2. **Add your content**: Paste text or select file
3. **Add metadata**: Title and description (optional)
4. **Submit**: Content is processed and indexed automatically

### System Monitoring
1. **View statistics**: Document and vector counts
2. **Check session history**: See your recent activity
3. **Monitor performance**: System health indicators

## 🎯 Best Practices

### For Better Query Results
- **Be specific**: Ask detailed questions rather than vague ones
- **Use context**: Reference specific topics or documents
- **Check sources**: Review citations to understand answer quality
- **Iterate**: Refine questions based on initial results

### For Content Management
- **Use descriptive titles**: Help with content organization
- **Add context**: Include relevant metadata
- **Chunk appropriately**: Break large documents into sections
- **Verify ingestion**: Check that content was processed successfully

### For System Performance
- **Monitor regularly**: Check system statistics
- **Clean sessions**: Clear history periodically
- **Batch uploads**: Process multiple files efficiently
- **Check health**: Monitor API status regularly

## 🔗 Integration

The Gradio UI communicates with the RAG system through REST API endpoints:
- `POST /query` - Process queries
- `POST /ingest` - Add text content
- `POST /upload` - Upload files
- `GET /health` - System health
- `GET /stats` - System statistics

## 📞 Support

If you encounter issues:
1. Check the **Help tab** in the UI
2. Review the **troubleshooting section** above
3. Check **API logs** for detailed error messages
4. Verify **system requirements** are met

## 🎉 Getting Started Workflow

1. **Launch the system**: `python launch_ui.py`
2. **Verify connection**: Check API status shows "✅ HEALTHY"
3. **Add content**: Upload a document or paste some text
4. **Test queries**: Ask questions about your content
5. **Explore features**: Try different tabs and options
6. **Monitor system**: Check statistics and session history

The interface is designed to be intuitive and self-explanatory. Start with the Help tab if you need guidance! 