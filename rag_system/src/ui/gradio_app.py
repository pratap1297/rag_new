"""
Gradio UI Application
Enhanced web interface for the RAG system with conversation support
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
import uuid
import time

def create_gradio_app(container) -> Optional[object]:
    """Create Gradio application with conversation support"""
    try:
        # Optional Gradio interface - only if gradio is installed
        import gradio as gr
        
        query_engine = container.get('query_engine')
        ingestion_engine = container.get('ingestion_engine')
        conversation_manager = container.get('conversation_manager')
        
        # Conversation state management
        current_session = {"session_id": None, "conversation_history": []}
        
        def process_query(query: str, top_k: int = 5):
            """Process a query through the RAG system"""
            try:
                result = query_engine.process_query(query=query, top_k=top_k)
                return result['response'], str(result['sources'])
            except Exception as e:
                return f"Error: {str(e)}", ""
        
        def upload_file(file):
            """Upload and ingest a file"""
            try:
                if file is None:
                    return "No file uploaded"
                
                result = ingestion_engine.ingest_file(file.name)
                return f"File ingested successfully: {result['chunks_created']} chunks created"
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Conversation functions
        def start_new_conversation():
            """Start a new conversation session"""
            if conversation_manager is None:
                return "Conversation feature not available", "", "No session"
            
            try:
                state = conversation_manager.start_conversation()
                current_session["session_id"] = state.session_id
                current_session["conversation_history"] = []
                
                # Get initial greeting
                assistant_messages = [msg for msg in state.messages if msg.type.value == "assistant"]
                initial_response = assistant_messages[-1].content if assistant_messages else "Hello! How can I help you?"
                
                # Update conversation history
                current_session["conversation_history"] = [
                    {"role": "assistant", "content": initial_response}
                ]
                
                return current_session["conversation_history"], "", state.session_id
                
            except Exception as e:
                logging.error(f"Error starting conversation: {e}")
                return [{"role": "assistant", "content": f"Error starting conversation: {str(e)}"}], "", "Error"
        
        def send_message(message: str, history: List[Dict[str, str]], session_id: str):
            """Send message in conversation"""
            if not message.strip():
                return history, ""
            
            if conversation_manager is None:
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": "Conversation feature not available"})
                return history, ""
            
            if not session_id or session_id == "No session":
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": "Please start a new conversation first"})
                return history, ""
            
            try:
                # Process message
                response = conversation_manager.process_user_message(session_id, message)
                
                # Add to history
                assistant_response = response.get('response', 'No response generated')
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": assistant_response})
                
                # Update stored history
                current_session["conversation_history"] = history
                
                return history, ""
                
            except Exception as e:
                logging.error(f"Error in conversation: {e}")
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": f"Error: {str(e)}"})
                return history, ""
        
        def get_conversation_info(session_id: str):
            """Get conversation information"""
            if not conversation_manager or not session_id or session_id == "No session":
                return "No active conversation"
            
            try:
                history = conversation_manager.get_conversation_history(session_id)
                return f"Session: {session_id}\nTurns: {history['turn_count']}\nPhase: {history['current_phase']}\nTopics: {', '.join(history['topics_discussed'][-3:])}"
            except Exception as e:
                return f"Error getting info: {str(e)}"
        
        def end_conversation(session_id: str):
            """End current conversation"""
            if not conversation_manager or not session_id or session_id == "No session":
                return "No active conversation to end", ""
            
            try:
                result = conversation_manager.end_conversation(session_id)
                current_session["session_id"] = None
                current_session["conversation_history"] = []
                return f"Conversation ended. {result.get('summary', '')}", "No session"
            except Exception as e:
                return f"Error ending conversation: {str(e)}", session_id
        
        # Create Gradio interface
        with gr.Blocks(
            title="RAG System with Conversational AI",
            theme=gr.themes.Soft(),
            css="""
            .conversation-container { max-height: 500px; overflow-y: auto; }
            .chat-message { margin: 5px 0; padding: 10px; border-radius: 10px; }
            .user-message { background-color: #e3f2fd; text-align: right; }
            .assistant-message { background-color: #f3e5f5; text-align: left; }
            """
        ) as app:
            gr.Markdown("# 🤖 RAG System with Conversational AI")
            gr.Markdown("Enhanced RAG system with LangGraph-powered conversations")
            
            with gr.Tab("💬 Conversation Chat"):
                gr.Markdown("### Intelligent Conversational Interface")
                gr.Markdown("Have natural conversations with your AI assistant powered by LangGraph")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        # Chat interface
                        chatbot = gr.Chatbot(
                            label="Conversation",
                            height=400,
                            show_label=True,
                            container=True,
                            type="messages"
                        )
                        
                        with gr.Row():
                            msg_input = gr.Textbox(
                                placeholder="Type your message here... Press Enter to send",
                                label="Your Message",
                                lines=2,
                                scale=4
                            )
                            send_btn = gr.Button("📤 Send", variant="primary", scale=1)
                        
                        with gr.Row():
                            start_btn = gr.Button("🆕 New Conversation", variant="secondary")
                            end_btn = gr.Button("🔚 End Conversation", variant="stop")
                    
                    with gr.Column(scale=1):
                        # Session info
                        gr.Markdown("### Session Info")
                        session_display = gr.Textbox(
                            label="Session ID",
                            value="No session",
                            interactive=False
                        )
                        
                        session_info = gr.Textbox(
                            label="Conversation Details",
                            lines=4,
                            interactive=False
                        )
                        
                        refresh_btn = gr.Button("🔄 Refresh Info")
                
                # Event handlers for conversation
                start_btn.click(
                    fn=start_new_conversation,
                    outputs=[chatbot, msg_input, session_display]
                )
                
                send_btn.click(
                    fn=send_message,
                    inputs=[msg_input, chatbot, session_display],
                    outputs=[chatbot, msg_input]
                )
                
                msg_input.submit(
                    fn=send_message,
                    inputs=[msg_input, chatbot, session_display],
                    outputs=[chatbot, msg_input]
                )
                
                end_btn.click(
                    fn=end_conversation,
                    inputs=[session_display],
                    outputs=[session_info, session_display]
                )
                
                refresh_btn.click(
                    fn=get_conversation_info,
                    inputs=[session_display],
                    outputs=[session_info]
                )
            
            with gr.Tab("🔍 Query"):
                gr.Markdown("### Direct Query Interface")
                gr.Markdown("Ask direct questions and get immediate responses")
                
                query_input = gr.Textbox(label="Enter your query", lines=2)
                top_k_input = gr.Slider(minimum=1, maximum=10, value=5, step=1, label="Number of results")
                query_button = gr.Button("Submit Query")
                
                response_output = gr.Textbox(label="Response", lines=5)
                sources_output = gr.Textbox(label="Sources", lines=3)
                
                query_button.click(
                    process_query,
                    inputs=[query_input, top_k_input],
                    outputs=[response_output, sources_output]
                )
            
            with gr.Tab("📁 Upload"):
                gr.Markdown("### Document Upload")
                gr.Markdown("Upload documents to expand the knowledge base")
                
                file_input = gr.File(label="Upload Document")
                upload_button = gr.Button("Upload and Ingest")
                upload_output = gr.Textbox(label="Upload Result")
                
                upload_button.click(
                    upload_file,
                    inputs=[file_input],
                    outputs=[upload_output]
                )
        
        logging.info("Enhanced Gradio app with conversation support created")
        return app
        
    except ImportError:
        logging.info("Gradio not installed, skipping UI creation")
        return None
    except Exception as e:
        logging.error(f"Failed to create Gradio app: {e}")
        return None 