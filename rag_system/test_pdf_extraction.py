#!/usr/bin/env python3
"""
Test script to properly extract and ingest PDF content
"""
import sys
from pathlib import Path
import PyPDF2

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyPDF2"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(f"=== Page {page_num} ===\n{page_text}")
            
            return "\n\n".join(text_content)
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None

def main():
    """Main function to extract and ingest PDF content"""
    try:
        from src.core.system_init import initialize_system
        
        print("🔧 Initializing system...")
        container = initialize_system()
        print("✅ System initialized")
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        metadata_store = container.get('metadata_store')
        
        # Test PDF files
        pdf_files = [
            "test_documents/BuildingA_Network_Layout.pdf",
            "test_documents/BuildingB_Network_Layout.pdf", 
            "test_documents/BuildingC_Network_Layout.pdf"
        ]
        
        for pdf_file in pdf_files:
            if not Path(pdf_file).exists():
                print(f"⚠️  File not found: {pdf_file}")
                continue
                
            print(f"\n📄 Processing {pdf_file}...")
            
            # Extract text content
            text_content = extract_pdf_text(pdf_file)
            if not text_content:
                print(f"❌ Failed to extract text from {pdf_file}")
                continue
                
            print(f"✅ Extracted {len(text_content)} characters")
            print(f"Preview: {text_content[:200]}...")
            
            # Create a temporary text file with the extracted content
            temp_file = pdf_file.replace('.pdf', '_extracted.txt')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Ingest the text file
            try:
                result = ingestion_engine.ingest_file(temp_file)
                if result.get('success'):
                    print(f"✅ Successfully ingested: {result.get('chunks_created', 0)} chunks")
                else:
                    print(f"❌ Ingestion failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Ingestion error: {e}")
            
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)
        
        print("\n📊 Final status:")
        files = metadata_store.get_all_files()
        chunks = metadata_store.get_all_chunks()
        print(f"Total files: {len(files)}")
        print(f"Total chunks: {len(chunks)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 