#!/usr/bin/env python3
"""
Simple AI Force Intelligent Support Agent UI
A working alternative to the problematic launch_fixed_ui.py
"""

import gradio as gr
import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple

class SimpleRAGUI:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.document_registry = {}
        
    def check_api_connection(self) -> str:
        """Check if the API is accessible"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                return "✅ **API Connection Successful**\n\n🟢 Backend is running and accessible"
            else:
                return f"❌ **API Connection Failed**\n\nHTTP Status: {response.status_code}"
        except Exception as e:
            return f"❌ **API Connection Error**\n\n{str(e)}"
    
    def test_query(self, query: str, max_results: int = 5) -> Tuple[str, str, str]:
        """Test a query against the system"""
        if not query or not query.strip():
            return "❌ Please enter a valid query", "", ""
        
        try:
            payload = {
                "query": query,
                "max_results": max_results
            }
            
            response = requests.post(f"{self.api_url}/query", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle response structure
                if data.get('success') and 'data' in data:
                    response_data = data['data']
                    answer = response_data.get('response', 'No response generated')
                    sources = response_data.get('sources', [])
                    confidence = response_data.get('confidence_score', 0.0)
                else:
                    answer = data.get('response', 'No response generated')
                    sources = data.get('sources', [])
                    confidence = data.get('confidence_score', 0.0)
                
                # Format the answer
                formatted_answer = f"🤖 **AI Response:**\n{answer}\n\n"
                formatted_answer += f"🎯 **Confidence:** {confidence:.3f}\n"
                formatted_answer += f"📚 **Sources Found:** {len(sources)}"
                
                # Format sources
                sources_text = ""
                if sources:
                    sources_text = "📚 **Sources:**\n"
                    for i, source in enumerate(sources[:3], 1):
                        source_name = source.get('source_name', 'Unknown')
                        relevance = source.get('relevance_score', 0.0)
                        content = source.get('text', 'No content available')
                        
                        sources_text += f"{i}. **{source_name}** (Score: {relevance:.3f})\n"
                        sources_text += f"   {content[:200]}{'...' if len(content) > 200 else ''}\n\n"
                else:
                    sources_text = "📚 **No sources found**"
                
                # Format analysis
                analysis = f"🔍 **Query Analysis:**\n"
                analysis += f"• Query Length: {len(query)} characters\n"
                analysis += f"• Max Results: {max_results}\n"
                analysis += f"• Sources Retrieved: {len(sources)}\n"
                analysis += f"• Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                return formatted_answer, sources_text, analysis
                
            else:
                error_msg = f"❌ **Query Failed**\nHTTP Status: {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    error_msg += f"\nDetails: {error_detail}"
                except:
                    error_msg += f"\nResponse: {response.text[:200]}"
                
                return error_msg, "", ""
                
        except Exception as e:
            return f"❌ **Query Error:** {str(e)}", "", ""
    
    def upload_document(self, file) -> str:
        """Upload a document to the system"""
        if not file:
            return "❌ Please select a file to upload"
        
        try:
            files = {'file': (file.name, file.read(), 'application/octet-stream')}
            response = requests.post(f"{self.api_url}/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return f"✅ **Document Uploaded Successfully!**\n\n📄 **File:** {file.name}\n📝 **Chunks:** {data.get('chunks_created', 0)}\n📅 **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                error_msg = f"❌ **Upload Failed**\nHTTP Status: {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    error_msg += f"\nDetails: {error_detail}"
                except:
                    error_msg += f"\nResponse: {response.text[:200]}"
                return error_msg
                
        except Exception as e:
            return f"❌ **Upload Error:** {str(e)}"
    
    def get_system_status(self) -> str:
        """Get system status and statistics"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = "🟢 **System Status: Healthy**\n\n"
                status += f"📊 **Backend:** Running\n"
                status += f"🕐 **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                status += f"🔗 **API URL:** {self.api_url}"
                return status
            else:
                return f"🔴 **System Status: Unhealthy**\n\nHTTP Status: {response.status_code}"
        except Exception as e:
            return f"🔴 **System Status: Error**\n\n{str(e)}"

def create_simple_interface():
    """Create a simple Gradio interface"""
    ui = SimpleRAGUI()
    
    with gr.Blocks(title="AI Force Intelligent Support Agent", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🤖 AI Force Intelligent Support Agent")
        gr.Markdown("Simple and reliable RAG system interface")
        
        with gr.Tabs():
            # Query Tab
            with gr.TabItem("🔍 Query"):
                with gr.Row():
                    with gr.Column(scale=2):
                        query_input = gr.Textbox(
                            label="Ask a question",
                            placeholder="What is artificial intelligence?",
                            lines=3
                        )
                        max_results = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="Max Results"
                        )
                        query_btn = gr.Button("🔍 Query", variant="primary")
                    
                    with gr.Column(scale=1):
                        status_btn = gr.Button("📊 System Status")
                
                with gr.Row():
                    with gr.Column():
                        answer_output = gr.Markdown(label="🤖 AI Response")
                        sources_output = gr.Markdown(label="📚 Sources")
                        analysis_output = gr.Markdown(label="🔍 Analysis")
            
            # Upload Tab
            with gr.TabItem("📤 Upload"):
                file_input = gr.File(label="Select Document")
                upload_btn = gr.Button("📤 Upload", variant="primary")
                upload_output = gr.Markdown(label="Upload Result")
            
            # Status Tab
            with gr.TabItem("📊 Status"):
                status_output = gr.Markdown(label="System Status")
        
        # Event handlers
        query_btn.click(
            fn=ui.test_query,
            inputs=[query_input, max_results],
            outputs=[answer_output, sources_output, analysis_output]
        )
        
        upload_btn.click(
            fn=ui.upload_document,
            inputs=[file_input],
            outputs=[upload_output]
        )
        
        status_btn.click(
            fn=ui.get_system_status,
            outputs=[status_output]
        )
        
        # Auto-load status on startup
        interface.load(
            fn=ui.get_system_status,
            outputs=[status_output]
        )
    
    return interface

def main():
    """Main function to launch the interface"""
    print("🚀 Starting AI Force Intelligent Support Agent...")
    print("📡 Checking API connection...")
    
    ui = SimpleRAGUI()
    status = ui.check_api_connection()
    print(status)
    
    interface = create_simple_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main() 