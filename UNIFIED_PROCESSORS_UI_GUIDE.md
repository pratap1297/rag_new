# Testing Unified Processors with launch_fixed_ui.py

## 🎯 Overview

The unified processors are fully integrated with your existing `launch_fixed_ui.py` system and work seamlessly with:
- ✅ **File Upload Interface**
- ✅ **Folder Monitoring**
- ✅ **Document Management**
- ✅ **Query Interface**

## 🚀 Quick Start Guide

### Step 1: Start the API Server
```bash
# Navigate to the rag_system directory
cd rag_system

# Start the API server (this loads the unified processors)
python main.py
```

The server will start on `http://localhost:8000` and automatically load all 6 unified processors.

### Step 2: Launch the UI
```bash
# In a new terminal, from the project root
python launch_fixed_ui.py
```

The UI will open in your browser and connect to the API server.

## 📄 Testing Different Document Types

### Excel Files (.xlsx, .xls, .xlsm, .xlsb)
1. **Upload via UI**: Use the file upload interface
2. **Processor**: Automatically uses `ExcelProcessor`
3. **Features**: 
   - Multi-sheet processing
   - Embedded objects extraction
   - Hierarchical data analysis
   - Rich metadata extraction

**Test File**: `document_generator/test_data/Facility_Managers_2024.xlsx`

### PDF Files (.pdf)
1. **Upload via UI**: Drag and drop PDF files
2. **Processor**: Automatically uses `PDFProcessor`
3. **Features**:
   - Azure Computer Vision integration (when configured)
   - Text extraction
   - Page-by-page processing

### Word Documents (.docx, .doc)
1. **Upload via UI**: Standard file upload
2. **Processor**: Automatically uses `WordProcessor`
3. **Features**:
   - Text and table extraction
   - Document properties analysis

### Images (.jpg, .png, .bmp, .tiff, .gif)
1. **Upload via UI**: Image file upload
2. **Processor**: Automatically uses `ImageProcessor`
3. **Features**:
   - OCR text extraction
   - Azure Computer Vision integration

### Text Files (.txt, .md, .py, .js, .json, .csv, etc.)
1. **Upload via UI**: Any text-based file
2. **Processor**: Automatically uses `TextProcessor`
3. **Features**:
   - Language detection
   - Content type analysis
   - Smart chunking
   - Encoding detection

### ServiceNow Data
1. **Integration**: Automatic via API
2. **Processor**: Uses `ServiceNowProcessor`
3. **Features**:
   - Ticket data processing
   - Structured data extraction

## 🔄 How Automatic Processor Selection Works

The system automatically selects the right processor based on file extension:

```python
# File extension -> Processor mapping
'.xlsx' -> ExcelProcessor
'.pdf'  -> PDFProcessor
'.docx' -> WordProcessor
'.jpg'  -> ImageProcessor
'.txt'  -> TextProcessor
'servicenow' -> ServiceNowProcessor
```

## 📁 Folder Monitoring Integration

### Setup Folder Monitoring
1. **Via UI**: Use the "Folder Monitoring" section
2. **Enter Path**: Specify folder to monitor
3. **Start Monitoring**: Click "Start Monitoring"

### How It Works
1. **File Detection**: System detects new files in monitored folders
2. **Processor Selection**: Automatically selects appropriate processor
3. **Processing**: Processes file using unified processor
4. **Ingestion**: Adds processed content to vector store
5. **Notification**: Updates UI with processing status

### Supported Workflow
```
New File Added → Processor Selected → Document Processed → Vector Store Updated → UI Refreshed
```

## 🧪 Testing Workflow

### Method 1: Manual Upload Testing
```bash
# 1. Start API server
cd rag_system && python main.py

# 2. Start UI (new terminal)
python launch_fixed_ui.py

# 3. Upload different file types through UI
# 4. Check processing results in UI
# 5. Test queries against uploaded documents
```

### Method 2: Folder Monitoring Testing
```bash
# 1. Start API server
cd rag_system && python main.py

# 2. Start UI
python launch_fixed_ui.py

# 3. Set up folder monitoring in UI
# 4. Add files to monitored folder
# 5. Watch automatic processing in UI
```

### Method 3: Comprehensive Integration Testing
```bash
# Run the comprehensive integration test
python test_unified_ui_integration.py
```

## 📊 UI Features That Work with Unified Processors

### Document Management
- ✅ **Upload Status**: Shows which processor was used
- ✅ **Document Registry**: Tracks all processed documents
- ✅ **Chunk Count**: Displays chunks created by each processor
- ✅ **Metadata Display**: Shows processor-specific metadata

### Query Interface
- ✅ **Multi-format Search**: Queries across all document types
- ✅ **Source Attribution**: Shows which document type provided answers
- ✅ **Relevance Scoring**: Unified scoring across all processors

### Monitoring Dashboard
- ✅ **Processing Status**: Real-time processor activity
- ✅ **Vector Store Stats**: Unified statistics across all document types
- ✅ **Error Handling**: Processor-specific error reporting

## 🔧 Configuration

### Environment Variables (rag_system/.env)
```bash
# Azure Computer Vision (for PDF/Image processing)
COMPUTER_VISION_ENDPOINT=your_endpoint
COMPUTER_VISION_KEY=your_key

# Azure AI Services (for embeddings/LLM)
AZURE_API_KEY=your_api_key
AZURE_CHAT_ENDPOINT=your_chat_endpoint
AZURE_EMBEDDINGS_ENDPOINT=your_embeddings_endpoint

# ServiceNow (optional)
SERVICENOW_INSTANCE_URL=your_instance
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
```

### Processor Settings
The processors use these default settings (configurable via API):
```python
{
    'chunk_size': 1000,
    'chunk_overlap': 200,
    'use_azure_cv': True,
    'extract_images': True,
    'extract_tables': True,
    'confidence_threshold': 0.7
}
```

## 🎯 Expected Results

### Upload Success Indicators
- ✅ **Status Message**: "Document Uploaded Successfully!"
- ✅ **Processor Used**: Shows which unified processor was selected
- ✅ **Chunks Created**: Number of chunks generated
- ✅ **Vector Store Update**: Confirmation of vector storage

### Query Success Indicators
- ✅ **Multi-format Results**: Answers from different document types
- ✅ **Source Attribution**: Clear indication of source document type
- ✅ **Relevance Scores**: Consistent scoring across all processors

### Folder Monitoring Success
- ✅ **Auto-detection**: New files automatically detected
- ✅ **Processor Selection**: Correct processor chosen automatically
- ✅ **Processing Status**: Real-time processing updates
- ✅ **UI Updates**: Document registry automatically updated

## 🐛 Troubleshooting

### Common Issues

#### 1. API Server Not Starting
```bash
# Check if port 8000 is available
netstat -an | findstr :8000

# Check rag_system/.env file exists
ls rag_system/.env

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 2. Processor Not Found
- **Cause**: File extension not recognized
- **Solution**: Check supported extensions in processor registry
- **Debug**: Check API logs for processor selection

#### 3. Upload Fails
- **Cause**: File too large or unsupported format
- **Solution**: Check file size limits and supported formats
- **Debug**: Check API response for specific error

#### 4. Folder Monitoring Not Working
- **Cause**: Folder path incorrect or permissions issue
- **Solution**: Use absolute paths and check folder permissions
- **Debug**: Check monitoring status in UI

## 📈 Performance Expectations

### Processing Times (Approximate)
- **Text Files**: < 1 second
- **Excel Files**: 1-5 seconds (depending on size/complexity)
- **PDF Files**: 2-10 seconds (depending on pages/content)
- **Word Documents**: 1-3 seconds
- **Images**: 3-15 seconds (depending on OCR complexity)

### Scalability
- **Concurrent Uploads**: Supports multiple simultaneous uploads
- **Folder Monitoring**: Can monitor multiple folders simultaneously
- **Vector Storage**: Scales with document volume
- **Query Performance**: Consistent across all document types

## 🎉 Success Verification

### Complete Success Indicators
1. ✅ API server starts without errors
2. ✅ UI connects to API successfully
3. ✅ All 6 processors load correctly
4. ✅ File uploads work for all supported formats
5. ✅ Folder monitoring detects and processes files
6. ✅ Queries return results from all document types
7. ✅ UI shows processing status and statistics

### Test Commands
```bash
# Quick verification
curl http://localhost:8000/health

# Check processor status
curl http://localhost:8000/processors/status

# Test upload (replace with actual file)
curl -X POST -F "file=@test.txt" http://localhost:8000/upload

# Test query
curl -X POST -H "Content-Type: application/json" \
     -d '{"query":"test query","top_k":3}' \
     http://localhost:8000/query
```

## 🚀 Production Deployment

The unified processors are **production-ready** and provide:
- **Enterprise-grade processing** for 6 document types
- **Seamless UI integration** with existing interface
- **Automatic folder monitoring** for hands-free operation
- **Scalable architecture** for growing document volumes
- **Azure AI integration** for enhanced processing capabilities

Your existing `launch_fixed_ui.py` now has **supercharged document processing capabilities** with the unified processor architecture! 