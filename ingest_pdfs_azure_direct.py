#!/usr/bin/env python3
"""
Direct PDF Ingestion with Azure Vision API
Simple script to directly ingest PDFs using Azure Vision without complex metadata operations
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "rag_system"))

def ingest_pdfs_directly():
    """Directly ingest PDF files using Azure Vision API"""
    print("🔄 Direct PDF Ingestion with Azure Vision API")
    print("=" * 60)
    
    try:
        # Import required components
        from src.core.system_init import initialize_system
        
        # Initialize the system
        print("🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        
        # PDF files to ingest
        pdf_files = [
            "rag_system/test_documents/BuildingA_Network_Layout.pdf",
            "rag_system/test_documents/BuildingB_Network_Layout.pdf", 
            "rag_system/test_documents/BuildingC_Network_Layout.pdf"
        ]
        
        for pdf_file in pdf_files:
            pdf_path = Path(pdf_file)
            if not pdf_path.exists():
                print(f"⚠️  PDF not found: {pdf_file}")
                continue
            
            print(f"\n📄 Processing: {pdf_path.name}")
            
            # Directly ingest with Azure Vision
            try:
                result = ingestion_engine.ingest_file(
                    str(pdf_path),
                    metadata={
                        'title': pdf_path.stem.replace('_', ' ').replace('-', ' ').title(),
                        'source': 'pdf_network_layout',
                        'document_type': 'network_layout',
                        'building': pdf_path.stem.split('_')[0] if '_' in pdf_path.stem else 'Unknown',
                        'content_type': 'technical_diagram',
                        'extraction_method': 'azure_vision_api'
                    }
                )
                
                if result['status'] == 'success':
                    print(f"   ✅ Successfully processed!")
                    print(f"   📊 Chunks created: {result['chunks_created']}")
                    print(f"   🔧 Processor used: {result.get('processor_used', 'Unknown')}")
                    
                    # Show preview if available
                    if result.get('sample_content'):
                        preview = result['sample_content'][:200] + "..." if len(result['sample_content']) > 200 else result['sample_content']
                        print(f"   📖 Content preview: {preview}")
                else:
                    print(f"   ❌ Processing failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Error processing {pdf_file}: {e}")
        
        print(f"\n🎉 PDF ingestion completed!")
        print(f"🔍 Your PDFs should now contain actual network layout content")
        print(f"💡 Test queries:")
        print(f"   • 'What is the signal strength in Building A?'")
        print(f"   • 'List network equipment in the buildings'")
        print(f"   • 'What floors are covered in the network layouts?'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def quick_test_query():
    """Quick test to see if the content was ingested properly"""
    print("\n🧪 Quick Test Query...")
    
    try:
        from src.core.system_init import initialize_system
        
        container = initialize_system()
        query_engine = container.get('query_engine')
        
        # Test query about building network layout
        test_query = "What buildings are covered in the network layout documents?"
        print(f"🔍 Test query: {test_query}")
        
        result = query_engine.query(test_query)
        
        if result.get('answer'):
            print(f"✅ Query successful!")
            print(f"📝 Answer: {result['answer']}")
            
            if result.get('sources'):
                print(f"📚 Sources found: {len(result['sources'])}")
                for i, source in enumerate(result['sources'][:2]):
                    print(f"   {i+1}. {source.get('metadata', {}).get('source', 'Unknown')}")
        else:
            print(f"⚠️  No answer received")
            
    except Exception as e:
        print(f"❌ Test query failed: {e}")

def main():
    """Main function"""
    print("Azure Vision PDF Direct Ingestion")
    print()
    
    choice = input("Choose an option:\n1. Ingest PDFs\n2. Test query\n3. Both\n\nEnter choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        ingest_pdfs_directly()
    
    if choice in ['2', '3']:
        quick_test_query()

if __name__ == "__main__":
    main() 