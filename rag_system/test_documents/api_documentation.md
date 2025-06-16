# API Documentation - RAG System

**Document Type:** Markdown (.md)  
**Version:** 1.0  
**Last Updated:** 2025-06-07  
**Purpose:** Test document for RAG system ingestion with rich markdown formatting

---

## Table of Contents

1. [Authentication](#authentication)
2. [Query API](#query-api)
3. [Document Ingestion](#document-ingestion)
4. [System Management](#system-management)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

---

## Authentication

### API Key Authentication

All API requests require authentication using an API key in the header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Getting an API Key

1. **Admin Users**: Generate keys through the admin panel
2. **Regular Users**: Request keys from your system administrator
3. **Service Accounts**: Use dedicated service account keys

> **⚠️ Security Note:** Never expose API keys in client-side code or public repositories.

---

## Query API

### POST /api/v1/query

Submit a natural language query to the RAG system.

#### Request Format

```json
{
  "query": "How do I reset my password?",
  "max_results": 5,
  "filters": {
    "document_type": "policy",
    "department": "IT"
  },
  "include_sources": true
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Natural language question |
| `max_results` | integer | ❌ | Maximum results (default: 3) |
| `filters` | object | ❌ | Filter criteria for search |
| `include_sources` | boolean | ❌ | Include source documents (default: true) |

#### Response Format

```json
{
  "response": "To reset your password, use the self-service portal...",
  "sources": [
    {
      "document_id": "doc_123",
      "title": "Password Reset Procedures",
      "relevance_score": 0.95,
      "excerpt": "Use the self-service password reset portal..."
    }
  ],
  "query_id": "query_456",
  "processing_time_ms": 234
}
```

#### Status Codes

- **200 OK**: Query processed successfully
- **400 Bad Request**: Invalid query format
- **401 Unauthorized**: Invalid or missing API key
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: System error

---

## Document Ingestion

### POST /api/v1/ingest

Upload and process documents for inclusion in the knowledge base.

#### Supported File Types

- **Text Files**: `.txt`
- **Markdown**: `.md`
- **PDF Documents**: `.pdf`
- **Word Documents**: `.docx`

#### Request Format (Multipart Form)

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "metadata={\"title\":\"Company Policy\",\"department\":\"HR\"}" \
  http://localhost:8000/api/v1/ingest
```

#### Metadata Schema

```json
{
  "title": "Document Title",
  "description": "Brief description",
  "department": "IT|HR|Finance|Sales",
  "category": "policy|procedure|faq|technical",
  "tags": ["password", "security", "authentication"],
  "author": "John Doe",
  "version": "1.0"
}
```

#### Response Format

```json
{
  "document_id": "doc_789",
  "status": "processed",
  "chunks_created": 15,
  "processing_time_ms": 5432,
  "metadata": {
    "title": "Company Policy",
    "file_size_bytes": 102400,
    "page_count": 8
  }
}
```

---

## System Management

### GET /api/v1/health

Check system health and status.

#### Response Format

```json
{
  "status": "healthy",
  "timestamp": "2025-06-07T10:30:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12
    },
    "vector_store": {
      "status": "healthy",
      "index_size": 1024,
      "total_documents": 156
    },
    "llm_service": {
      "status": "healthy",
      "provider": "groq",
      "model": "llama-3.1-70b-versatile"
    }
  }
}
```

### GET /api/v1/stats

Retrieve system statistics and metrics.

#### Response Format

```json
{
  "documents": {
    "total": 156,
    "by_type": {
      "pdf": 89,
      "txt": 34,
      "md": 23,
      "docx": 10
    }
  },
  "queries": {
    "total_today": 1247,
    "average_response_time_ms": 345,
    "success_rate": 0.987
  },
  "storage": {
    "total_size_mb": 2048,
    "vector_count": 15678,
    "index_size_mb": 512
  }
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Query cannot be empty",
    "details": {
      "field": "query",
      "provided_value": ""
    },
    "request_id": "req_123456"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_QUERY` | Query format is invalid | 400 |
| `UNAUTHORIZED` | Invalid or missing API key | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMITED` | Too many requests | 429 |
| `INTERNAL_ERROR` | System error | 500 |

---

## Rate Limiting

### Limits by Plan

| Plan | Requests/Minute | Requests/Day |
|------|-----------------|--------------|
| **Free** | 10 | 1,000 |
| **Professional** | 100 | 10,000 |
| **Enterprise** | 1,000 | 100,000 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640995200
```

### Handling Rate Limits

When rate limited, implement exponential backoff:

```python
import time
import requests

def query_with_backoff(query, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post('/api/v1/query', json={'query': query})
        
        if response.status_code != 429:
            return response
        
        # Exponential backoff
        wait_time = 2 ** attempt
        time.sleep(wait_time)
    
    raise Exception("Max retries exceeded")
```

---

## Examples

### Basic Query Example

```python
import requests

# Simple query
response = requests.post(
    'http://localhost:8000/api/v1/query',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={'query': 'What is the password policy?'}
)

result = response.json()
print(f"Answer: {result['response']}")
```

### Document Upload Example

```python
import requests

# Upload a document
with open('policy.pdf', 'rb') as file:
    response = requests.post(
        'http://localhost:8000/api/v1/ingest',
        headers={'Authorization': 'Bearer YOUR_API_KEY'},
        files={'file': file},
        data={'metadata': '{"title": "Security Policy", "department": "IT"}'}
    )

result = response.json()
print(f"Document ID: {result['document_id']}")
```

### Advanced Query with Filters

```javascript
const response = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'How do I configure SSL certificates?',
    max_results: 10,
    filters: {
      department: 'IT',
      category: 'technical',
      tags: ['ssl', 'security']
    }
  })
});

const data = await response.json();
console.log('Answer:', data.response);
```

---

## Best Practices

### 🔍 **Query Optimization**

1. **Be Specific**: Use detailed questions for better results
2. **Use Keywords**: Include relevant technical terms
3. **Context Matters**: Provide context when asking follow-up questions

### 📄 **Document Preparation**

1. **Clear Structure**: Use headings and sections
2. **Rich Metadata**: Provide comprehensive metadata
3. **Quality Content**: Ensure documents are well-written and accurate

### 🔒 **Security**

1. **Secure API Keys**: Store keys securely, rotate regularly
2. **Input Validation**: Validate all inputs before sending
3. **HTTPS Only**: Always use HTTPS in production

### ⚡ **Performance**

1. **Batch Operations**: Group multiple operations when possible
2. **Caching**: Cache frequently accessed results
3. **Pagination**: Use pagination for large result sets

---

## Support

### Getting Help

- **Documentation**: [docs.ragSystem.com](https://docs.ragSystem.com)
- **Support Email**: support@ragSystem.com
- **Community Forum**: [forum.ragSystem.com](https://forum.ragSystem.com)
- **Status Page**: [status.ragSystem.com](https://status.ragSystem.com)

### SLA Commitments

| Metric | Target |
|--------|--------|
| **Uptime** | 99.9% |
| **Response Time** | < 500ms (95th percentile) |
| **Support Response** | < 4 hours (business days) |

---

*This documentation is automatically generated and updated. Last build: 2025-06-07 10:30:00 UTC* 