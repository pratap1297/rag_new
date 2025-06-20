#!/usr/bin/env python3
"""
Check all documents in the RAG system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from launch_fixed_ui import FixedRAGUI

def check_all_documents():
    """Check all documents in the system"""
    print("=" * 60)
    print("CHECKING ALL DOCUMENTS IN RAG SYSTEM")
    print("=" * 60)
    
    try:
        # Create UI instance (triggers auto-sync)
        ui = FixedRAGUI("http://localhost:8000")
        
        print(f"\n📊 Total documents found: {len(ui.document_registry)}")
        
        if ui.document_registry:
            print("\n📋 DOCUMENT DETAILS:")
            print("-" * 60)
            
            for i, (doc_path, info) in enumerate(ui.document_registry.items(), 1):
                filename = info.get('filename', 'Unknown')
                chunks = info.get('chunks', 0)
                source = info.get('source', 'unknown')
                last_updated = info.get('last_updated', 'Unknown')
                
                print(f"\n{i}. 📄 {filename}")
                print(f"   Path: {doc_path}")
                print(f"   Chunks: {chunks}")
                print(f"   Source: {source}")
                print(f"   Updated: {last_updated}")
                
                # Check for Building documents
                if 'building' in filename.lower() or 'building' in doc_path.lower():
                    print(f"   🏢 BUILDING DOCUMENT DETECTED")
                
                # Check for Excel/roster documents
                if any(ext in filename.lower() for ext in ['.xlsx', '.xls', 'excel', 'roster']):
                    print(f"   📊 EXCEL/ROSTER DOCUMENT DETECTED")
        
        print("\n" + "=" * 60)
        print("DOCUMENT CHECK COMPLETED")
        print("=" * 60)
        
        # Show dropdown options
        print(f"\n🔽 DROPDOWN OPTIONS:")
        dropdown_options = ui.get_document_paths()
        for i, option in enumerate(dropdown_options, 1):
            print(f"   {i}. {option}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_all_documents() 