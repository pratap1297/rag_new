#!/usr/bin/env python3
"""
Excel Query with Azure AI LLM
Complete RAG system: retrieval with Azure embeddings + generation with Azure LLM
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

def create_azure_embedder():
    """Create Azure AI Inference embeddings client"""
    try:
        from azure.ai.inference import EmbeddingsClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = "https://azurehub1910875317.services.ai.azure.com/models"
        api_key = "6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr"
        model_name = "Cohere-embed-v3-english"
        
        client = EmbeddingsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
        class AzureEmbedder:
            def __init__(self, client, model_name):
                self.client = client
                self.model_name = model_name
                self._dimension = None
                
            def embed_text(self, text: str):
                """Generate embedding for a single text"""
                return self.embed_texts([text])[0]
                
            def embed_texts(self, texts):
                """Generate embeddings for multiple texts"""
                response = self.client.embed(
                    input=texts,
                    model=self.model_name
                )
                embeddings = [item.embedding for item in response.data]
                if self._dimension is None:
                    self._dimension = len(embeddings[0]) if embeddings else 1024
                return embeddings
                
            def get_dimension(self):
                """Get embedding dimension"""
                if self._dimension is None:
                    # Test with a sample to get dimension
                    test_embedding = self.embed_text("test")
                    self._dimension = len(test_embedding)
                return self._dimension
        
        return AzureEmbedder(client, model_name)
        
    except ImportError:
        print("❌ Azure AI Inference SDK not installed. Run: pip install azure-ai-inference")
        return None
    except Exception as e:
        print(f"❌ Failed to create Azure embedder: {e}")
        return None

def create_azure_llm_client():
    """Create Azure AI Inference LLM client"""
    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.ai.inference.models import SystemMessage, UserMessage
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = "https://azurehub1910875317.services.ai.azure.com/models"
        api_key = "6EfFXXBeu1r1Jhn9n4bvkDUrfQUBBCzljLHA0p2eLS6Rn8rGnfB4JQQJ99BEACYeBjFXJ3w3AAAAACOGWvEr"
        model_name = "Llama-4-Maverick-17B-128E-Instruct-FP8"
        
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
            api_version="2024-05-01-preview"
        )
        
        class AzureLLMClient:
            def __init__(self, client, model_name):
                self.client = client
                self.model_name = model_name
                
            def generate_response(self, system_prompt: str, user_query: str, context: str = "") -> str:
                """Generate response using Azure LLM"""
                try:
                    enhanced_query = f"""Context from Excel data:
{context}

User Question: {user_query}

Please provide a helpful answer based on the context provided."""
                    
                    response = self.client.complete(
                        messages=[
                            SystemMessage(content=system_prompt),
                            UserMessage(content=enhanced_query)
                        ],
                        max_tokens=2048,
                        temperature=0.7,
                        top_p=0.9,
                        presence_penalty=0.0,
                        frequency_penalty=0.0,
                        model=self.model_name
                    )
                    
                    return response.choices[0].message.content
                    
                except Exception as e:
                    return f"Error generating response: {str(e)}"
        
        return AzureLLMClient(client, model_name)
        
    except ImportError:
        print("❌ Azure AI Inference SDK not installed. Run: pip install azure-ai-inference")
        return None
    except Exception as e:
        print(f"❌ Failed to create Azure LLM client: {e}")
        return None

def setup_rag_system():
    """Setup the complete RAG system with Azure AI services"""
    print("🔧 Setting up Azure AI RAG system...")
    
    # Create Azure embedder
    azure_embedder = create_azure_embedder()
    if not azure_embedder:
        return None, None, None
    
    # Create Azure LLM client
    azure_llm = create_azure_llm_client()
    if not azure_llm:
        return None, None, None
    
    # Initialize FAISS store
    from src.storage.faiss_store import FAISSStore
    dimension = azure_embedder.get_dimension()
    faiss_store = FAISSStore(
        index_path="data/vectors/faiss_index.bin",
        dimension=dimension
    )
    
    print("✅ Azure AI RAG system ready!")
    return azure_embedder, azure_llm, faiss_store

def retrieve_relevant_context(query: str, embedder, faiss_store, top_k: int = 3) -> str:
    """Retrieve relevant context from the vector store"""
    try:
        # Generate query embedding
        query_embedding = embedder.embed_text(query)
        
        # Search for relevant documents
        search_results = faiss_store.search(query_embedding, k=top_k)
        
        # Format context
        context_parts = []
        for i, result in enumerate(search_results, 1):
            content = result.get('content', result.get('text', 'No content'))
            source = result.get('file_name', result.get('filename', 'Unknown'))
            score = result.get('similarity_score', 0)
            
            context_parts.append(f"""
Document {i} (Similarity: {score:.3f}):
Source: {source}
Content: {content}
""")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        print(f"⚠️ Error retrieving context: {e}")
        return "No relevant context found."

def query_with_llm(query: str, embedder, llm_client, faiss_store):
    """Complete RAG query: retrieve + generate"""
    print(f"\n🔍 Processing query: '{query}'")
    
    # Step 1: Retrieve relevant context
    print("📚 Retrieving relevant context...")
    context = retrieve_relevant_context(query, embedder, faiss_store, top_k=3)
    
    print("📄 Retrieved context:")
    print("=" * 50)
    print(context)
    print("=" * 50)
    
    # Step 2: Generate response with LLM
    print("\n🤖 Generating AI response...")
    
    system_prompt = """You are a helpful assistant that answers questions about facility management data from Excel files. 
You have access to information about facility managers, their buildings, floors, areas, and contact details.
Provide accurate, helpful responses based on the context provided. If the context doesn't contain enough information to answer the question, say so clearly."""
    
    # Generate response
    response = llm_client.generate_response(system_prompt, query, context)
    
    print("\n💬 AI Response:")
    print("=" * 50)
    print(response)
    print("=" * 50)
    
    return response

def demo_queries():
    """Run some demo queries to showcase the system"""
    print("🎯 Running Demo Queries with Azure AI RAG System")
    print("=" * 60)
    
    # Setup RAG system
    embedder, llm_client, faiss_store = setup_rag_system()
    if not embedder or not llm_client or not faiss_store:
        print("❌ Failed to setup RAG system")
        return
    
    # Check if we have data
    try:
        index_info = faiss_store.get_index_info()
        total_vectors = index_info.get('ntotal', 0)
        print(f"📊 Vector store contains {total_vectors} documents")
        
        if total_vectors == 0:
            print("⚠️ No data found in vector store. Please run the ingestion script first.")
            return
            
    except Exception as e:
        print(f"⚠️ Could not check vector store: {e}")
    
    # Demo queries
    demo_queries_list = [
        "Who are the facility managers for Building A?",
        "What contact information do you have for facility managers?",
        "How many managers are there in total?",
        "Show me information about managers in different buildings"
    ]
    
    for query in demo_queries_list:
        print(f"\n{'='*80}")
        query_with_llm(query, embedder, llm_client, faiss_store)
        print(f"{'='*80}")
        
        # Pause between queries
        input("\nPress Enter to continue to next query...")

if __name__ == '__main__':
    print("🤖 Excel Query with Azure AI LLM")
    print("Running demo queries...")
    demo_queries() 