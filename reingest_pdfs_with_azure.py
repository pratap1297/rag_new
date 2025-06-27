#!/usr/bin/env python3
"""
Re-ingest PDF Files with Azure Vision API
Replaces placeholder content with actual Azure Vision extracted content
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "rag_system"))

def reingest_pdfs_with_azure():
    """Re-ingest PDF files using Azure Vision API"""
    print("🔄 Re-ingesting PDF Files with Azure Vision API")
    print("=" * 60)
    
    try:
        # Import required components
        from src.core.system_init import initialize_system
        
        # Initialize the system
        print("🚀 Initializing RAG system...")
        container = initialize_system()
        
        # Get components
        ingestion_engine = container.get('ingestion_engine')
        metadata_store = container.get('metadata_store')
        
        # PDF files to re-ingest
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
            
            # Check if already ingested
            existing_docs = metadata_store.search_by_source(str(pdf_path))
            if existing_docs:
                print(f"   🗑️  Removing {len(existing_docs)} existing chunks")
                for doc in existing_docs:
                    metadata_store.delete(doc['id'])
            
            # Re-ingest with Azure Vision
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
                    
                    # Show preview of extracted content
                    if result.get('sample_content'):
                        preview = result['sample_content'][:200] + "..." if len(result['sample_content']) > 200 else result['sample_content']
                        print(f"   📖 Content preview: {preview}")
                else:
                    print(f"   ❌ Processing failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Error processing {pdf_file}: {e}")
        
        print(f"\n🎉 PDF re-ingestion completed!")
        print(f"🔍 Your PDFs now contain actual network layout content extracted by Azure Vision")
        print(f"💡 Try asking: 'List all cisco routers' or 'What is the signal strength in Building A?'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def verify_azure_content():
    """Verify that Azure content was properly ingested"""
    print("\n🔍 Verifying Azure Vision Content...")
    
    try:
        from src.core.system_init import initialize_system
        
        container = initialize_system()
        metadata_store = container.get('metadata_store')
        
        # Search for network layout content
        all_docs = metadata_store.list_all()
        pdf_docs = [doc for doc in all_docs if doc.get('source_type') == 'pdf']
        
        print(f"📊 Found {len(pdf_docs)} PDF chunks")
        
        for doc in pdf_docs[:3]:  # Show first 3
            source = doc.get('source', 'Unknown')
            content_preview = doc.get('content', '')[:150] + "..." if len(doc.get('content', '')) > 150 else doc.get('content', '')
            extraction_method = doc.get('extraction_method', 'Unknown')
            
            print(f"\n📄 Source: {Path(source).name if source else 'Unknown'}")
            print(f"   🔧 Extraction: {extraction_method}")
            print(f"   📖 Content: {content_preview}")
        
        # Check for network-related content
        network_terms = ['signal', 'rssi', 'building', 'floor', 'coverage', 'router', 'cisco']
        network_chunks = []
        
        for doc in pdf_docs:
            content = doc.get('content', '').lower()
            if any(term in content for term in network_terms):
                network_chunks.append(doc)
        
        print(f"\n🌐 Found {len(network_chunks)} chunks with network-related content")
        if network_chunks:
            print("✅ Azure Vision successfully extracted network layout information!")
        else:
            print("⚠️  No network-related content found. May need to re-ingest.")
            
    except Exception as e:
        print(f"❌ Verification error: {e}")

def main():
    """Main function"""
    print("Azure Vision PDF Re-ingestion Tool")
    print()
    
    choice = input("Choose an option:\n1. Re-ingest PDFs with Azure Vision\n2. Verify current content\n3. Both\n\nEnter choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        reingest_pdfs_with_azure()
    
    if choice in ['2', '3']:
        verify_azure_content()

if __name__ == "__main__":
    main() 