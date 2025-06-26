"""
Gradio UI Application
Enhanced web interface for the RAG system with conversation support and progress tracking
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
import uuid
import time
import threading
from datetime import datetime

def create_gradio_app(container) -> Optional[object]:
    """Create Gradio application with conversation support and progress tracking"""
    try:
        # Optional Gradio interface - only if gradio is installed
        import gradio as gr
        
        # Import progress tracking components
        try:
            from ..core.progress_tracker import ProgressTracker, ProgressStage, ProgressStatus
            from ..ui.progress_monitor import ProgressMonitor
            PROGRESS_TRACKING_AVAILABLE = True
        except ImportError:
            PROGRESS_TRACKING_AVAILABLE = False
            logging.warning("Progress tracking components not available")
        
        query_engine = container.get('query_engine')
        ingestion_engine = container.get('ingestion_engine')
        conversation_manager = container.get('conversation_manager')
        
        # Initialize progress tracker if available
        progress_tracker = None
        progress_monitor = None
        if PROGRESS_TRACKING_AVAILABLE:
            try:
                progress_tracker = ProgressTracker(persistence_path="data/progress/ingestion_progress.json")
                progress_monitor = ProgressMonitor(progress_tracker)
                
                # Update ingestion engine with progress tracker
                if hasattr(ingestion_engine, 'progress_tracker'):
                    ingestion_engine.progress_tracker = progress_tracker
                    ingestion_engine.progress_helper = getattr(ingestion_engine, 'progress_helper', None) or None
                
                logging.info("Progress tracker initialized for Gradio UI")
            except Exception as e:
                logging.error(f"Failed to initialize progress tracker: {e}")
                PROGRESS_TRACKING_AVAILABLE = False
        
        # Conversation state management
        current_session = {"session_id": None, "conversation_history": []}
        
        # Progress tracking state
        progress_state = {
            "last_update": datetime.now(),
            "active_files": set(),
            "batch_id": None
        }
        
        def process_query(query: str, top_k: int = 5):
            """Process a query through the RAG system"""
            try:
                result = query_engine.process_query(query=query, top_k=top_k)
                return result['response'], str(result['sources'])
            except Exception as e:
                return f"Error: {str(e)}", ""
        
        def upload_file(file):
            """Upload and ingest a file with progress tracking"""
            try:
                if file is None:
                    return "No file uploaded"
                
                if PROGRESS_TRACKING_AVAILABLE and progress_tracker:
                    # Generate batch ID for this upload
                    batch_id = str(uuid.uuid4())
                    progress_state["batch_id"] = batch_id
                    progress_state["active_files"].add(file.name)
                    
                    # Start progress tracking
                    progress_tracker.start_file(file.name)
                    
                    # Ingest with progress tracking
                    result = ingestion_engine.ingest_file(file.name)
                    
                    # Update progress state
                    progress_state["active_files"].discard(file.name)
                    progress_state["last_update"] = datetime.now()
                    
                    return f"File ingested successfully: {result['chunks_created']} chunks created\nBatch ID: {batch_id}"
                else:
                    # Fallback without progress tracking
                    result = ingestion_engine.ingest_file(file.name)
                    return f"File ingested successfully: {result['chunks_created']} chunks created"
                    
            except Exception as e:
                if PROGRESS_TRACKING_AVAILABLE and progress_tracker:
                    progress_state["active_files"].discard(file.name if file else "unknown")
                return f"Error: {str(e)}"
        
        def get_progress_data():
            """Get current progress data for UI display"""
            if not PROGRESS_TRACKING_AVAILABLE or not progress_tracker:
                return "Progress tracking not available", "", ""
            
            try:
                # Get all progress
                all_progress = progress_tracker.get_all_progress()
                system_metrics = progress_tracker.get_system_metrics()
                
                # Format file progress
                file_progress_text = ""
                for file_path, progress in all_progress.items():
                    if progress.status in [ProgressStatus.RUNNING, ProgressStatus.COMPLETED, ProgressStatus.FAILED]:
                        file_progress_text += f"📄 {Path(file_path).name}\n"
                        file_progress_text += f"   Status: {progress.status.value}\n"
                        file_progress_text += f"   Stage: {progress.current_stage.value}\n"
                        file_progress_text += f"   Progress: {progress.overall_progress * 100:.1f}%\n"
                        if progress.chunks_created > 0:
                            file_progress_text += f"   Chunks: {progress.chunks_created}\n"
                        if progress.vectors_created > 0:
                            file_progress_text += f"   Vectors: {progress.vectors_created}\n"
                        if progress.estimated_time_remaining:
                            file_progress_text += f"   ETA: {progress.estimated_time_remaining}\n"
                        file_progress_text += "\n"
                
                # Format system metrics
                metrics_text = f"📊 System Metrics\n"
                metrics_text += f"Files Processed: {system_metrics.get('total_files_processed', 0)}\n"
                metrics_text += f"Total Chunks: {system_metrics.get('total_chunks_created', 0)}\n"
                metrics_text += f"Total Vectors: {system_metrics.get('total_vectors_created', 0)}\n"
                metrics_text += f"Errors: {system_metrics.get('total_errors', 0)}\n"
                if 'files_per_minute' in system_metrics:
                    metrics_text += f"Rate: {system_metrics['files_per_minute']:.2f} files/min\n"
                if 'mb_per_minute' in system_metrics:
                    metrics_text += f"Data Rate: {system_metrics['mb_per_minute']:.2f} MB/min\n"
                metrics_text += f"CPU: {system_metrics.get('cpu_percent', 0):.1f}%\n"
                metrics_text += f"Memory: {system_metrics.get('memory_percent', 0):.1f}%\n"
                
                # Format batch progress if available
                batch_text = ""
                if progress_state["batch_id"]:
                    batch_progress = progress_tracker.get_batch_progress(progress_state["batch_id"])
                    if batch_progress:
                        batch_text = f"📦 Batch Progress (ID: {progress_state['batch_id'][:8]}...)\n"
                        batch_text += f"Total Files: {batch_progress.get('total_files', 0)}\n"
                        batch_text += f"Completed: {batch_progress.get('completed_files', 0)}\n"
                        batch_text += f"Failed: {batch_progress.get('failed_files', 0)}\n"
                        batch_text += f"Running: {batch_progress.get('running_files', 0)}\n"
                        batch_text += f"Overall Progress: {batch_progress.get('overall_progress', 0) * 100:.1f}%\n"
                
                return file_progress_text, metrics_text, batch_text
                
            except Exception as e:
                return f"Error getting progress: {str(e)}", "", ""
        
        def refresh_progress():
            """Refresh progress data"""
            return get_progress_data()
        
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
            title="AI Force Intelligent Support Agent",
            theme=gr.themes.Soft(),
            css="""
            .conversation-container { max-height: 500px; overflow-y: auto; }
            .chat-message { margin: 5px 0; padding: 10px; border-radius: 10px; }
            .user-message { background-color: #e3f2fd; text-align: right; }
            .assistant-message { background-color: #f3e5f5; text-align: left; }
            .progress-container { max-height: 400px; overflow-y: auto; }
            """
        ) as app:
            gr.Markdown("# 🤖 AI Force Intelligent Support Agent")
            gr.Markdown("Enhanced RAG system with LangGraph-powered conversations and progress tracking")
            
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
            
            # Add Progress Monitor Tab
            with gr.Tab("📊 Progress Monitor"):
                gr.Markdown("### Real-time Ingestion Progress")
                gr.Markdown("Monitor document ingestion progress in real-time")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("#### 📄 File Progress")
                        file_progress_display = gr.Textbox(
                            label="Active Files",
                            lines=10,
                            interactive=False,
                            value="No active files"
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📦 Batch Progress")
                        batch_progress_display = gr.Textbox(
                            label="Current Batch",
                            lines=6,
                            interactive=False,
                            value="No active batch"
                        )
                
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("#### 📊 System Metrics")
                        system_metrics_display = gr.Textbox(
                            label="Performance Metrics",
                            lines=8,
                            interactive=False,
                            value="No metrics available"
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🔄 Controls")
                        refresh_progress_btn = gr.Button("🔄 Refresh Progress", variant="primary")
                        auto_refresh_toggle = gr.Checkbox(label="Auto-refresh (5s)", value=False)
                
                # Initialize progress display
                initial_progress = get_progress_data()
                file_progress_display.value = initial_progress[0] or "No active files"
                system_metrics_display.value = initial_progress[1] or "No metrics available"
                batch_progress_display.value = initial_progress[2] or "No active batch"
                
                # Event handlers for progress monitoring
                refresh_progress_btn.click(
                    fn=refresh_progress,
                    outputs=[file_progress_display, system_metrics_display, batch_progress_display]
                )
                
                # Auto-refresh functionality
                def auto_refresh_progress():
                    """Auto-refresh progress every 5 seconds"""
                    while True:
                        time.sleep(5)
                        try:
                            progress_data = get_progress_data()
                            yield progress_data[0], progress_data[1], progress_data[2]
                        except Exception as e:
                            logging.error(f"Auto-refresh error: {e}")
                            yield "Auto-refresh error", "Auto-refresh error", "Auto-refresh error"
                
                # Set up auto-refresh
                auto_refresh_toggle.change(
                    fn=auto_refresh_progress,
                    outputs=[file_progress_display, system_metrics_display, batch_progress_display],
                    every=5
                )
        
        logging.info("Enhanced Gradio app with conversation support and progress tracking created")
        return app
        
    except ImportError:
        logging.info("Gradio not installed, skipping UI creation")
        return None
    except Exception as e:
        logging.error(f"Failed to create Gradio app: {e}")
        return None 