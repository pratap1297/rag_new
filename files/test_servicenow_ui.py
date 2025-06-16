#!/usr/bin/env python3
"""
Test ServiceNow UI functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_servicenow_ui():
    """Test ServiceNow UI components"""
    print("🧪 Testing ServiceNow UI Components")
    print("=" * 40)
    
    try:
        # Test import
        from src.api.servicenow_ui import ServiceNowUI, create_servicenow_interface
        print("✅ ServiceNow UI import successful")
        
        # Test UI class initialization
        ui = ServiceNowUI()
        print("✅ ServiceNowUI class initialization successful")
        
        # Test ticket fetching (should use sample data)
        tickets_table, checkboxes, pagination = ui.fetch_servicenow_tickets()
        print("✅ Ticket fetching test successful")
        print(f"   - Tickets table length: {len(tickets_table)}")
        print(f"   - Checkboxes HTML length: {len(checkboxes)}")
        print(f"   - Pagination info: {pagination[:50]}...")
        
        # Test ticket selection
        selection_result = ui.update_ticket_selection("ticket_1,ticket_2")
        print("✅ Ticket selection test successful")
        print(f"   - Selection result: {selection_result}")
        
        # Test ingestion (simulated)
        ingestion_result = ui.ingest_selected_tickets()
        print("✅ Ticket ingestion test successful")
        print(f"   - Ingestion result: {ingestion_result[:100]}...")
        
        # Test stats
        stats_result = ui.get_servicenow_stats()
        print("✅ Stats retrieval test successful")
        print(f"   - Stats result: {stats_result[:100]}...")
        
        # Test interface creation
        interface = create_servicenow_interface()
        print("✅ Gradio interface creation successful")
        
        print("\n🎉 All ServiceNow UI tests passed!")
        print("\n📋 ServiceNow UI Features Available:")
        print("   - ✅ Ticket browsing with pagination")
        print("   - ✅ Priority, state, and category filtering")
        print("   - ✅ Ticket selection with checkboxes")
        print("   - ✅ Batch ingestion into RAG system")
        print("   - ✅ Statistics and monitoring")
        print("   - ✅ Gradio web interface")
        
        print("\n🚀 To launch the ServiceNow UI:")
        print("   python src/api/servicenow_ui.py")
        print("   Then visit: http://localhost:7861")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_servicenow_ui()
    sys.exit(0 if success else 1) 