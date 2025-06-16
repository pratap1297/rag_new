# 🔧 RAG System Management

This document describes the comprehensive management system for your RAG (Retrieval-Augmented Generation) system, including APIs for cleaning, viewing, and managing vectors, chunks, and documents, plus a user-friendly Gradio web interface.

## 🚀 Quick Start

### 1. Start the RAG System Server
```bash
cd rag-system
python main.py
```

### 2. Test the Management API
```bash
python test_management_api.py
```

### 3. Launch the Web UI
```bash
python launch_ui.py
```

Then open http://localhost:7860 in your browser.

## 📋 Management API Endpoints

### Document Management

#### List Documents
```http
GET /manage/documents?limit=50&title_filter=security
```
- Lists all documents with optional filtering
- Returns document metadata, chunk counts, and creation dates

#### Get Document Details
```http
GET /manage/document/{doc_id}
```
- Returns detailed information about a specific document
- Includes all chunks and full metadata

#### Delete Documents
```http
DELETE /manage/documents
Content-Type: application/json

["doc_id_1", "doc_id_2"]
```
- Deletes entire documents (all their chunks)

### Vector Management

#### List Vectors
```http
GET /manage/vectors?limit=50&doc_id_filter=network&text_search=security
```
- Lists vectors with optional filtering by document ID or text content

#### Get Vector Details
```http
GET /manage/vector/{vector_id}
```
- Returns detailed information about a specific vector

#### Delete Vectors
```http
DELETE /manage/vectors
Content-Type: application/json

[123, 456, 789]
```
- Deletes specific vectors by ID

### Cleanup Operations

#### Clean Unknown Documents
```http
POST /manage/cleanup/unknown
```
- Removes all documents with generic IDs like "doc_unknown_0"

#### Remove Duplicates
```http
POST /manage/cleanup/duplicates
```
- Identifies and removes duplicate content based on text similarity

#### Reindex Document IDs
```http
POST /manage/reindex/doc_ids
```
- Regenerates document IDs using improved naming logic
- Uses title, filename, or description for meaningful names

### Metadata Management

#### Update Metadata
```http
PUT /manage/update
Content-Type: application/json

{
  "vector_ids": [123, 456],
  "doc_ids": ["doc_example_1"],
  "updates": {
    "title": "Updated Title",
    "category": "updated"
  }
}
```
- Updates metadata for specific vectors or all vectors in documents

### Statistics

#### Detailed Statistics
```http
GET /manage/stats/detailed
```
- Returns comprehensive statistics about the vector store
- Includes document counts, text length analysis, and more

## 🖥️ Gradio Web Interface

The Gradio UI provides a user-friendly web interface for all management operations:

### Features

1. **📊 System Overview**
   - Real-time system statistics
   - Health monitoring
   - Vector store metrics

2. **📄 Document Management**
   - Browse all documents
   - Filter by title or content
   - View detailed document information
   - See all chunks for each document

3. **🔢 Vector Management**
   - List all vectors with filtering
   - Search by document ID or text content
   - View vector metadata and content

4. **🧹 Cleanup Operations**
   - One-click cleanup of unknown documents
   - Remove duplicate content
   - Reindex document IDs for better naming
   - Manual document deletion

5. **🔍 Query Testing**
   - Test system queries directly
   - See which documents are retrieved
   - Analyze response quality

6. **📥 Data Ingestion**
   - Add new content through the web interface
   - Specify metadata (title, description, author)
   - Real-time ingestion feedback

### UI Screenshots and Usage

#### System Overview Tab
- View system health and statistics
- Monitor vector counts and storage usage
- Check component status

#### Document Management Tab
- Browse all documents in a table format
- Filter by title or other criteria
- Click on document IDs to view full details
- See chunk counts and text lengths

#### Cleanup Operations Tab
- **Clean Unknown Documents**: Removes all documents with generic IDs
- **Remove Duplicates**: Finds and removes duplicate content
- **Reindex Document IDs**: Improves document naming
- **Manual Deletion**: Delete specific documents by ID

## 🛠️ Installation and Setup

### Prerequisites
```bash
pip install -r requirements.txt
pip install -r requirements_ui.txt
```

### Environment Setup
1. Ensure your RAG system is running on port 8000
2. Install Gradio dependencies
3. Launch the UI on port 7860

### Configuration
The management system automatically connects to your RAG system API. You can customize:

- API URL: `--api-url http://localhost:8000`
- UI Port: `--port 7860`
- Host binding: `--host 0.0.0.0`

## 🔧 Advanced Usage

### Programmatic Access

```python
import requests

# List documents
response = requests.get("http://localhost:8000/manage/documents")
documents = response.json()

# Clean unknown documents
response = requests.post("http://localhost:8000/manage/cleanup/unknown")
cleanup_result = response.json()

# Update metadata
response = requests.put("http://localhost:8000/manage/update", json={
    "doc_ids": ["doc_example_1"],
    "updates": {"category": "updated"}
})
```

### Batch Operations

```python
# Delete multiple documents
doc_ids = ["doc_unknown_0", "doc_unknown_1", "doc_unknown_2"]
response = requests.delete("http://localhost:8000/manage/documents", json=doc_ids)

# Update multiple vectors
vector_ids = [1, 2, 3, 4, 5]
response = requests.put("http://localhost:8000/manage/update", json={
    "vector_ids": vector_ids,
    "updates": {"processed": True}
})
```

## 🚨 Troubleshooting

### Common Issues

1. **"doc_unknown_0" appearing in queries**
   - **Cause**: Documents ingested without proper metadata
   - **Solution**: Use the "Reindex Document IDs" feature or re-ingest with proper titles

2. **Duplicate content in results**
   - **Cause**: Same content ingested multiple times
   - **Solution**: Use the "Remove Duplicates" cleanup operation

3. **UI not connecting to API**
   - **Cause**: RAG system not running or wrong URL
   - **Solution**: Ensure main.py is running and check the API URL

4. **Slow performance**
   - **Cause**: Large number of vectors or complex queries
   - **Solution**: Use filtering options and pagination

### Performance Tips

1. **Use Filters**: When browsing large datasets, use title filters and text search
2. **Pagination**: Limit results to 20-50 items for faster loading
3. **Batch Operations**: Use the API directly for large-scale operations
4. **Regular Cleanup**: Periodically clean unknown documents and duplicates

## 📊 Monitoring and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Run duplicate cleanup
2. **Monthly**: Reindex document IDs for better organization
3. **As needed**: Clean unknown documents after bulk ingestion
4. **Monitor**: Check system statistics for growth trends

### Health Monitoring

The system provides comprehensive health monitoring:
- Vector store status
- API response times
- Memory usage
- Error rates

## 🔐 Security Considerations

1. **Access Control**: The management interface has full system access
2. **Network Security**: Bind to localhost in production environments
3. **Data Backup**: Always backup before major cleanup operations
4. **Audit Logging**: All operations are logged for audit purposes

## 📈 Future Enhancements

Planned features for future releases:
- Role-based access control
- Automated cleanup scheduling
- Advanced analytics and reporting
- Integration with external data sources
- Bulk import/export capabilities

## 🤝 Contributing

To contribute to the management system:
1. Test new features with the test script
2. Update documentation for new endpoints
3. Ensure UI components are responsive
4. Add appropriate error handling

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Run the test script to diagnose problems
3. Check system logs for detailed error messages
4. Use the health monitoring endpoints for system status 