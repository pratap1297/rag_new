#!/usr/bin/env python3
"""
Fixed RAG System UI - Improved Document Lifecycle Management
===========================================================
Fixes the confusing upload/update flow with better UX
"""

import sys
import os
import time
import requests
import gradio as gr
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List
import uuid
import re

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class FixedRAGUI:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.document_registry = {}  # Track documents for lifecycle management
        
        print(f"DEBUG: FixedRAGUI initialized with API URL: {api_url}")
        
    def check_api_connection(self) -> str:
        """Check if the API is accessible"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                timestamp = data.get('timestamp', 'unknown')
                components = data.get('components', {})
                
                status_text = f"✅ **API Status: {status.upper()}**\n"
                status_text += f"🕐 Last Check: {timestamp}\n"
                status_text += f"🔧 Components: {len(components)} active\n"
                status_text += f"🌐 Backend URL: {self.api_url}"
                
                return status_text
            else:
                return f"❌ **API Error: HTTP {response.status_code}**"
        except Exception as e:
            return f"❌ **Connection Error:** {str(e)}"

    def upload_and_refresh(self, file, doc_path) -> Tuple[str, str, List[str]]:
        """Upload file and refresh dropdowns"""
        print(f"DEBUG: upload_and_refresh called with file: {file}, doc_path: {doc_path}")
        
        if file is None:
            registry_display = self._format_document_registry()
            return "Please select a file to upload.", registry_display, []
        
        try:
            # Use doc_path if provided, otherwise generate from filename
            if not doc_path or not doc_path.strip():
                filename = os.path.basename(file.name) if hasattr(file, 'name') else str(file)
                doc_path = f"/docs/{os.path.splitext(filename)[0]}"
            
            # Ensure doc_path starts with /
            if not doc_path.startswith('/'):
                doc_path = f"/{doc_path}"
            
            # Read file content
            with open(file.name, 'rb') as f:
                file_content = f.read()
            
            # Prepare metadata with doc_path
            metadata = {
                "doc_path": doc_path,
                "operation": "upload",
                "source": "fixed_ui",
                "upload_timestamp": datetime.now().isoformat(),
                "original_filename": os.path.basename(file.name)
            }
            
            # Upload via text ingestion endpoint (which properly handles doc_path)
            try:
                # Try to decode as text first
                text_content = file_content.decode('utf-8')
                
                # Use text ingestion endpoint
                payload = {
                    "text": text_content,
                    "metadata": metadata
                }
                
                response = requests.post(f"{self.api_url}/ingest", json=payload, timeout=30)
                
            except UnicodeDecodeError:
                # If not text, use file upload endpoint
                files = {'file': (os.path.basename(file.name), file_content, 'application/octet-stream')}
                data = {'metadata': json.dumps(metadata)}
                
                response = requests.post(f"{self.api_url}/upload", files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Add to registry
                self.document_registry[doc_path] = {
                    'status': 'active',
                    'upload_count': self.document_registry.get(doc_path, {}).get('upload_count', 0) + 1,
                    'last_updated': datetime.now().isoformat(),
                    'filename': os.path.basename(file.name),
                    'chunks': result.get('chunks_created', 0),
                    'is_update': result.get('is_update', False),
                    'old_vectors_deleted': result.get('old_vectors_deleted', 0)
                }
                
                print(f"DEBUG: Added document in registry: {doc_path}")
                print(f"DEBUG: Registry now has {len(self.document_registry)} documents")
                
                # Get active documents for dropdown
                active_docs = [path for path, info in self.document_registry.items() 
                              if info['status'] == 'active']
                print(f"DEBUG: Registry has {len(self.document_registry)} total documents, {len(active_docs)} active: {active_docs}")
                
                # Create result message
                status_icon = "🔄" if result.get('is_update', False) else "✅"
                result_msg = f"{status_icon} **Document Uploaded Successfully!**\n"
                result_msg += f"📄 **Document Path:** `{doc_path}`\n"
                result_msg += f"📁 **File:** `{os.path.basename(file.name)}`\n"
                result_msg += f"📝 **Chunks Created:** {result.get('chunks_created', 0)}\n"
                
                if result.get('is_update', False):
                    result_msg += f"🗑️ **Old Vectors Replaced:** {result.get('old_vectors_deleted', 0)}\n"
                    result_msg += f"🔄 **Update Count:** {self.document_registry[doc_path]['upload_count']}\n"
                
                result_msg += f"📅 **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                print(f"DEBUG: Upload result: {result_msg[:100]}...")
                print(f"DEBUG: Dropdown choices: {active_docs}")
                
                # Get registry display
                registry_display = self._format_document_registry()
                
                return result_msg, registry_display, active_docs
            else:
                error_msg = f"❌ **Upload Failed**\n"
                error_msg += f"HTTP Status: {response.status_code}\n"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    error_msg += f"Details: {error_detail}"
                except:
                    error_msg += f"Response: {response.text[:200]}"
                
                registry_display = self._format_document_registry()
                return error_msg, registry_display, []
                
        except Exception as e:
            error_msg = f"❌ **Upload Error**\n{str(e)}"
            registry_display = self._format_document_registry()
            return error_msg, registry_display, []

    def delete_document(self, doc_path: str) -> Tuple[str, str, List[str]]:
        """Delete a document from the system"""
        if not doc_path or not doc_path.strip():
            return "❌ Please select a document from the dropdown to delete", "", []
        
        if doc_path == "No documents uploaded" or doc_path == "(No documents uploaded yet)":
            return "❌ No documents available to delete. Please upload a document first.", "", []
        
        if doc_path not in self.document_registry:
            available_docs = list(self.document_registry.keys())
            if available_docs:
                return f"❌ Document '{doc_path}' not found in registry.\n\nAvailable documents: {', '.join(available_docs)}", "", []
            else:
                return f"❌ No documents in registry. Please upload a document first.", "", []
        
        try:
            doc_info = self.document_registry[doc_path]
            doc_id = doc_info.get("doc_id", f"doc_{doc_path.replace('/', '_')}")
            
            # Call the proper delete endpoint to actually remove vectors
            try:
                # URL encode the doc_path for the API call
                import urllib.parse
                encoded_doc_path = urllib.parse.quote(doc_path, safe='')
                
                response = requests.delete(
                    f"{self.api_url}/documents/{encoded_doc_path}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    delete_result = response.json()
                    vectors_deleted = delete_result.get('vectors_deleted', 0)
                    deletion_success = True
                    
                    # Mark as deleted in registry only after successful API deletion
                    self.document_registry[doc_path]["status"] = "deleted"
                    self.document_registry[doc_path]["deleted_at"] = datetime.now().isoformat()
                    self.document_registry[doc_path]["vectors_deleted"] = vectors_deleted
                else:
                    deletion_success = False
                    vectors_deleted = 0
            except Exception as e:
                deletion_success = False
                vectors_deleted = 0
                print(f"Delete API call failed: {e}")
            
            result = f"✅ **Document Deletion Processed**\n\n"
            result += f"📄 **Document Path:** `{doc_path}`\n"
            result += f"📁 **Original File:** `{doc_info.get('filename', doc_info.get('original_filename', 'Unknown'))}`\n"
            result += f"🆔 **Document ID:** `{doc_id}`\n"
            result += f"🗑️ **Deleted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if deletion_success:
                result += f"✅ **Vectors successfully deleted from FAISS store**\n"
                result += f"🔢 **Vectors deleted:** {vectors_deleted}\n"
                result += f"🔍 **Testing:** Query for this content should return no results\n\n"
            else:
                result += f"⚠️ **Vector deletion failed** (registry updated only)\n"
                result += f"🔍 **Testing:** Document marked as deleted in registry but vectors may persist\n\n"
            
            result += f"**How to test deletion:**\n"
            result += f"1. Go to Query Testing tab\n"
            result += f"2. Search for content from this file\n"
            result += f"3. Verify no results are returned\n"
            result += f"4. Check vector count in system stats"
            
            # Update registry display and dropdown choices
            registry_display = self._format_document_registry()
            dropdown_choices = self.get_document_paths()
            
            return result, registry_display, dropdown_choices
            
        except Exception as e:
            return f"❌ **Error:** {str(e)}", "", []

    def get_document_paths(self) -> List[str]:
        """Get list of document paths for dropdown"""
        # Only return active and updated documents (not deleted ones)
        paths = [str(path) for path, info in self.document_registry.items() 
                if info.get("status") != "deleted"]
        print(f"DEBUG: Registry has {len(self.document_registry)} total documents, {len(paths)} active: {paths}")
        
        # Ensure we always return a list of strings
        if not paths:
            return ["(No documents uploaded yet)"]
        
        # Filter out any None or empty values and ensure all are strings
        valid_paths = [str(path) for path in paths if path and str(path).strip()]
        return valid_paths if valid_paths else ["(No documents uploaded yet)"]

    def _format_document_registry(self) -> str:
        """Format the document registry for display"""
        if not self.document_registry:
            return "📋 **No documents in registry**"
        
        registry_text = f"📋 **Document Registry** ({len(self.document_registry)} documents)\n\n"
        
        for doc_path, info in self.document_registry.items():
            status_emoji = {
                "active": "✅",
                "updated": "🔄", 
                "deleted": "🗑️"
            }.get(info.get("status", "unknown"), "❓")
            
            registry_text += f"{status_emoji} **{doc_path}**\n"
            registry_text += f"   📁 File: {info.get('filename', info.get('original_filename', 'Unknown'))}\n"
            registry_text += f"   📝 Chunks: {info.get('chunks', info.get('chunks_created', 0))}\n"
            registry_text += f"   📅 Last Updated: {info.get('last_updated', 'Unknown')}\n"
            registry_text += f"   📊 Status: {info.get('status', 'unknown').upper()}\n"
            registry_text += f"   📈 Upload Count: {info.get('upload_count', 1)}\n"
            
            # Optional fields
            if info.get('is_update'):
                registry_text += f"   🔄 Is Update: Yes\n"
            if info.get('old_vectors_deleted', 0) > 0:
                registry_text += f"   🗑️ Old Vectors Deleted: {info['old_vectors_deleted']}\n"
            
            if info.get("status") == "deleted" and "deleted_at" in info:
                registry_text += f"   🗑️ Deleted: {info['deleted_at']}\n"
            
            registry_text += "\n"
        
        return registry_text

    def test_query(self, query: str, max_results: int = 5) -> Tuple[str, str, str]:
        """Test a query against the system"""
        if not query.strip():
            return "❌ Please enter a query to test", "", ""
        
        try:
            payload = {
                "query": query,
                "max_results": max_results,
                "include_metadata": True
            }
            
            print(f"DEBUG: Query request - URL: {self.api_url}/query")
            print(f"DEBUG: Query request - Payload: {payload}")
            
            response = requests.post(f"{self.api_url}/query", json=payload, timeout=30)
            
            print(f"DEBUG: Query response - Status: {response.status_code}")
            if response.status_code == 200:
                response_data = response.json()
                print(f"DEBUG: Query response - Keys: {list(response_data.keys())}")
                print(f"DEBUG: Query response - Response length: {len(response_data.get('response', ''))}")
                print(f"DEBUG: Query response - Sources count: {len(response_data.get('sources', []))}")
            else:
                print(f"DEBUG: Query response - Error: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                raw_answer = data.get('response', '')  # Fixed: API returns 'response', not 'answer'
                sources = data.get('sources', [])
                
                # Store response data for feedback
                response_id = data.get('response_id', '')
                
                # Add confidence information to the answer
                confidence_score = data.get('confidence_score', 0.0)
                confidence_level = data.get('confidence_level', 'unknown')
                
                # Confidence level emoji mapping
                confidence_emoji = {
                    'high': '🟢',
                    'medium': '🟡', 
                    'low': '🔴',
                    'unknown': '⚪'
                }
                
                # Format answer with confidence header and feedback prompt
                if confidence_score > 0:
                    confidence_header = f"{confidence_emoji.get(confidence_level, '⚪')} **Confidence: {confidence_score} ({confidence_level.upper()})**\n\n"
                    answer = confidence_header + raw_answer
                else:
                    answer = raw_answer
                
                # Add feedback prompt
                if response_id:
                    feedback_prompt = f"\n\n---\n**Was this response helpful?** Please use the feedback buttons below to help us improve!\n*Response ID: {response_id[:8]}...*"
                    answer += feedback_prompt
                
                # Store response data for feedback functionality
                self.last_response_data = {
                    'query': query,
                    'response_id': response_id,
                    'response_text': raw_answer,
                    'confidence_score': confidence_score,
                    'confidence_level': confidence_level,
                    'sources_count': len(sources)
                }
                
                # Format sources
                if sources:
                    sources_text = "📚 **Sources Found:**\n\n"
                    lifecycle_analysis = "🔍 **Document Lifecycle Analysis:**\n\n"
                    
                    for i, source in enumerate(sources, 1):
                        score = source.get('score', 0)
                        doc_id = source.get('doc_id', 'Unknown')
                        text_preview = source.get('text', '')[:150] + "..."
                        
                        # Check if this is a deletion marker
                        is_deletion_marker = "[DELETED]" in text_preview or source.get('metadata', {}).get('deletion_marker', False)
                        
                        # Check if this source matches any document in our registry
                        registry_match = None
                        for doc_path, info in self.document_registry.items():
                            info_doc_id = info.get("doc_id", "")
                            if doc_id.startswith(doc_path) or info_doc_id == doc_id or doc_id.startswith(info_doc_id):
                                registry_match = (doc_path, info)
                                break
                        
                        sources_text += f"**Source {i}** (Score: {score:.3f})\n"
                        sources_text += f"Document ID: `{doc_id}`\n"
                        
                        if is_deletion_marker:
                            sources_text += f"🗑️ **DELETION MARKER** - This document was deleted\n"
                            sources_text += f"Preview: {text_preview}\n"
                        else:
                            sources_text += f"Preview: {text_preview}\n"
                        
                        if registry_match:
                            doc_path, info = registry_match
                            status_emoji = {
                                "active": "✅",
                                "updated": "🔄",
                                "deleted": "🗑️"
                            }.get(info["status"], "❓")
                            
                            sources_text += f"Registry Match: {status_emoji} `{doc_path}` ({info['status']})\n"
                            sources_text += f"Original File: `{info.get('filename', info.get('original_filename', 'Unknown'))}`\n"
                            
                            lifecycle_analysis += f"**Source {i}:** {status_emoji} Document `{doc_path}`\n"
                            lifecycle_analysis += f"   File: {info.get('filename', info.get('original_filename', 'Unknown'))}\n"
                            lifecycle_analysis += f"   Status: {info['status'].upper()}\n"
                            lifecycle_analysis += f"   Upload Count: {info.get('upload_count', 1)}\n"
                            lifecycle_analysis += f"   Last Updated: {info['last_updated']}\n"
                            
                            if is_deletion_marker:
                                lifecycle_analysis += f"   🗑️ DELETION MARKER - This confirms the document was deleted\n"
                            elif info["status"] == "deleted":
                                lifecycle_analysis += f"   ⚠️ This document was marked as deleted but still appears in results\n"
                            elif info["status"] == "updated":
                                lifecycle_analysis += f"   ✅ This shows the updated file content\n"
                            else:
                                lifecycle_analysis += f"   ✅ This is the original uploaded file\n"
                            
                            lifecycle_analysis += "\n"
                        else:
                            if is_deletion_marker:
                                lifecycle_analysis += f"**Source {i}:** 🗑️ DELETION MARKER (document was deleted)\n\n"
                            else:
                                lifecycle_analysis += f"**Source {i}:** ❓ Not tracked in registry\n\n"
                        
                        sources_text += "\n"
                else:
                    sources_text = "❌ **No sources found for this query**"
                    lifecycle_analysis = "🔍 **No documents matched this query**"
                
                # Format metadata with confidence scores
                context_used = data.get('context_used', 0)
                confidence_score = data.get('confidence_score', 0.0)
                confidence_level = data.get('confidence_level', 'unknown')
                
                # Confidence level emoji mapping
                confidence_emoji = {
                    'high': '🟢',
                    'medium': '🟡', 
                    'low': '🔴',
                    'unknown': '⚪'
                }
                
                metadata = f"**Query Results Metadata:**\n"
                metadata += f"- Query: `{query}`\n"
                metadata += f"- {confidence_emoji.get(confidence_level, '⚪')} **Confidence Score:** {confidence_score} ({confidence_level.upper()})\n"
                metadata += f"- Context chunks used: {context_used}\n"
                metadata += f"- Max results requested: {max_results}\n"
                metadata += f"- Sources found: {len(sources)}\n"
                metadata += f"- Registry documents: {len(self.document_registry)}\n"
                metadata += f"- Query timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                # Add confidence interpretation
                if confidence_score > 0:
                    metadata += f"\n**Confidence Interpretation:**\n"
                    if confidence_level == 'high':
                        metadata += f"🟢 **High Confidence:** Very reliable answer with strong source support\n"
                    elif confidence_level == 'medium':
                        metadata += f"🟡 **Medium Confidence:** Good answer but may need verification\n"
                    elif confidence_level == 'low':
                        metadata += f"🔴 **Low Confidence:** Uncertain answer, consider rephrasing query\n"
                
                return answer, sources_text, lifecycle_analysis
                
            else:
                error_msg = f"❌ **Query Failed:** HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    error_msg += f"\nDetails: {error_detail}"
                except:
                    error_msg += f"\nResponse: {response.text[:200]}"
                
                return error_msg, "", ""
                
        except Exception as e:
            return f"❌ **Query Error:** {str(e)}", "", ""
    
    def submit_feedback(self, helpful: bool, feedback_text: str = "") -> str:
        """Submit feedback for the last query response"""
        if not hasattr(self, 'last_response_data') or not self.last_response_data:
            return "❌ No recent query to provide feedback for. Please run a query first."
        
        try:
            feedback_payload = {
                **self.last_response_data,
                'helpful': helpful,
                'feedback_text': feedback_text,
                'user_id': 'ui_user',
                'session_id': f"ui_session_{datetime.now().strftime('%Y%m%d')}"
            }
            
            response = requests.post(f"{self.api_url}/feedback", json=feedback_payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                feedback_id = result.get('feedback_id', 'unknown')
                
                emoji = "👍" if helpful else "👎"
                result_msg = f"{emoji} **Feedback Submitted Successfully!**\n"
                result_msg += f"📝 **Feedback ID:** `{feedback_id[:8]}...`\n"
                result_msg += f"🎯 **Rating:** {'Helpful' if helpful else 'Not Helpful'}\n"
                
                if feedback_text:
                    result_msg += f"💬 **Comment:** {feedback_text}\n"
                
                result_msg += f"📅 **Submitted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                result_msg += f"\n✨ Thank you for helping us improve the system!"
                
                return result_msg
            else:
                return f"❌ **Feedback submission failed:** HTTP {response.status_code}"
                
        except Exception as e:
            return f"❌ **Feedback Error:** {str(e)}"
    
    def get_feedback_stats(self) -> str:
        """Get feedback statistics from the system"""
        try:
            response = requests.get(f"{self.api_url}/feedback/stats?days=30", timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                
                total_feedback = stats.get('total_feedback', 0)
                helpful_count = stats.get('helpful_count', 0)
                unhelpful_count = stats.get('unhelpful_count', 0)
                helpfulness_rate = stats.get('helpfulness_rate', 0)
                avg_confidence = stats.get('avg_confidence', 0)
                
                result_msg = "📊 **Feedback Statistics (Last 30 Days)**\n\n"
                result_msg += f"📝 **Total Feedback:** {total_feedback}\n"
                result_msg += f"👍 **Helpful:** {helpful_count}\n"
                result_msg += f"👎 **Not Helpful:** {unhelpful_count}\n"
                result_msg += f"📈 **Helpfulness Rate:** {helpfulness_rate:.1%}\n"
                result_msg += f"🎯 **Average Confidence:** {avg_confidence:.3f}\n"
                
                # Confidence breakdown
                confidence_breakdown = stats.get('confidence_breakdown', [])
                if confidence_breakdown:
                    result_msg += f"\n**Confidence Level Breakdown:**\n"
                    for level_stats in confidence_breakdown:
                        level = level_stats.get('confidence_level', 'unknown')
                        count = level_stats.get('count', 0)
                        rate = level_stats.get('helpfulness_rate', 0)
                        emoji = {'high': '🟢', 'medium': '🟡', 'low': '🔴'}.get(level, '⚪')
                        result_msg += f"   {emoji} **{level.title()}:** {count} responses ({rate:.1%} helpful)\n"
                
                return result_msg
            else:
                return f"❌ **Failed to get feedback stats:** HTTP {response.status_code}"
                
        except Exception as e:
            return f"❌ **Feedback Stats Error:** {str(e)}"

    def clear_vector_store(self) -> str:
        """Clear the entire vector store and index"""
        try:
            # Call the clear endpoint
            response = requests.post(f"{self.api_url}/clear", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Clear the local document registry
                self.document_registry.clear()
                
                # Create result message
                result_msg = "🧹 **Vector Store Cleared Successfully!**\n"
                result_msg += f"🗑️ **Vectors Deleted:** {result.get('vectors_deleted', 0)}\n"
                result_msg += f"📄 **Documents Removed:** {result.get('documents_deleted', 0)}\n"
                result_msg += f"📝 **Chunks Removed:** {result.get('chunks_deleted', 0)}\n"
                result_msg += f"📅 **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                result_msg += "\n⚠️ **Note:** All documents and vectors have been permanently removed from the system."
                
                return result_msg
            else:
                error_msg = f"❌ **Clear Failed**\n"
                error_msg += f"HTTP Status: {response.status_code}\n"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    error_msg += f"Details: {error_detail}"
                except:
                    error_msg += f"Response: {response.text[:200]}"
                
                return error_msg
                
        except Exception as e:
            return f"❌ **Clear Error:** {str(e)}"

    def start_folder_monitoring(self, folder_path: str) -> str:
        """Start monitoring a folder for file changes using backend API"""
        if not folder_path or not folder_path.strip():
            return "❌ Please provide a valid folder path"
        
        folder_path = folder_path.strip()
        
        # Validate folder exists
        if not os.path.exists(folder_path):
            return f"❌ Folder does not exist: {folder_path}"
        
        if not os.path.isdir(folder_path):
            return f"❌ Path is not a directory: {folder_path}"
        
        try:
            # First, check current monitoring status to see if folder is already being monitored
            status_response = requests.get(f"{self.api_url}/folder-monitor/status", timeout=10)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('success'):
                    monitored_folders = status_data.get('status', {}).get('monitored_folders', [])
                    
                    # Check if folder is already being monitored (normalize paths for comparison)
                    normalized_input = os.path.normpath(folder_path).lower()
                    already_monitored = False
                    
                    for monitored_folder in monitored_folders:
                        normalized_monitored = os.path.normpath(str(monitored_folder)).lower()
                        if normalized_input == normalized_monitored:
                            already_monitored = True
                            break
                    
                    if already_monitored:
                        # Folder is already being monitored, just ensure monitoring is started
                        start_response = requests.post(f"{self.api_url}/folder-monitor/start", timeout=10)
                        
                        result = f"ℹ️ **Folder Already Being Monitored**\n\n"
                        result += f"📁 **Folder Path:** `{folder_path}`\n"
                        result += f"📅 **Status Check:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        
                        if start_response.status_code == 200:
                            start_data = start_response.json()
                            if start_data.get('success'):
                                result += f"🟢 **Monitoring Status:** Active\n"
                                result += f"📁 **Total Folders Monitored:** {len(monitored_folders)}\n"
                            else:
                                result += f"⚠️ **Monitoring Status:** {start_data.get('error', 'Unknown status')}\n"
                        else:
                            result += f"⚠️ **Monitoring Status:** Could not verify (HTTP {start_response.status_code})\n"
                        
                        result += f"\n💡 **Note:** This folder is already in the monitoring list. Backend will continue to monitor it automatically."
                        
                        return result
            
            # Folder is not being monitored, proceed to add it
            response = requests.post(
                f"{self.api_url}/folder-monitor/add",
                json={"folder_path": folder_path},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Start monitoring if not already running
                    start_response = requests.post(f"{self.api_url}/folder-monitor/start", timeout=10)
                    
                    result = f"✅ **Folder Added to Backend Monitoring!**\n\n"
                    result += f"📁 **Folder Path:** `{folder_path}`\n"
                    result += f"📄 **Files Found:** {data.get('files_found', 0)}\n"
                    result += f"📅 **Added At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    
                    if start_response.status_code == 200:
                        start_data = start_response.json()
                        if start_data.get('success'):
                            result += f"🟢 **Monitoring Status:** Started\n"
                            result += f"📁 **Total Folders Monitored:** {len(start_data.get('folders', []))}\n"
                        else:
                            result += f"⚠️ **Monitoring Status:** {start_data.get('error', 'Already running')}\n"
                    
                    # Check for immediate scan results
                    if data.get('immediate_scan'):
                        result += f"\n🔍 **Immediate Scan Results:**\n"
                        result += f"- Changes Detected: {data.get('changes_detected', 0)}\n"
                        result += f"- Files Tracked: {data.get('files_tracked', 0)}\n"
                    
                    result += f"\n💡 **Note:** Backend will automatically detect new files and changes."
                    
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    
                    # Handle specific error cases
                    if "already being monitored" in error_msg.lower():
                        return f"ℹ️ **Folder Already Being Monitored**\n\n📁 **Path:** `{folder_path}`\n\n💡 This folder is already in the monitoring list. No action needed."
                    else:
                        return f"❌ Failed to add folder: {error_msg}"
            else:
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    
                    # Handle HTTP 400 specifically for already monitored folders
                    if response.status_code == 400 and "already being monitored" in error_detail.lower():
                        return f"ℹ️ **Folder Already Being Monitored**\n\n📁 **Path:** `{folder_path}`\n\n💡 This folder is already in the monitoring list. Monitoring will continue automatically."
                    else:
                        return f"❌ HTTP {response.status_code}: {error_detail}"
                except:
                    return f"❌ HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def stop_folder_monitoring(self) -> str:
        """Stop folder monitoring using backend API"""
        try:
            response = requests.post(f"{self.api_url}/folder-monitor/stop", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = f"🛑 **Backend Folder Monitoring Stopped**\n\n"
                    result += f"📅 **Stopped At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    result += f"💡 **Note:** Files will no longer be automatically monitored for changes."
                    return result
                else:
                    return f"❌ Failed to stop monitoring: {data.get('error', 'Unknown error')}"
            else:
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    return f"❌ HTTP {response.status_code}: {error_detail}"
                except:
                    return f"❌ HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def get_monitoring_status(self) -> str:
        """Get current monitoring status from backend API"""
        try:
            response = requests.get(f"{self.api_url}/folder-monitor/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    status_data = data.get('status', {})
                    
                    # Format status display
                    status_text = "## 📁 Backend Folder Monitoring Status\n\n"
                    
                    is_running = status_data.get('is_running', False)
                    status_text += f"**🔄 Status:** {'🟢 Running' if is_running else '🔴 Stopped'}\n"
                    status_text += f"**📁 Monitored Folders:** {len(status_data.get('monitored_folders', []))}\n"
                    status_text += f"**📄 Files Tracked:** {status_data.get('total_files_tracked', 0)}\n"
                    status_text += f"**✅ Files Ingested:** {status_data.get('files_ingested', 0)}\n"
                    status_text += f"**❌ Files Failed:** {status_data.get('files_failed', 0)}\n"
                    status_text += f"**⏳ Files Pending:** {status_data.get('files_pending', 0)}\n"
                    status_text += f"**📊 Total Scans:** {status_data.get('scan_count', 0)}\n"
                    status_text += f"**⏱️ Check Interval:** {status_data.get('check_interval', 0)} seconds\n"
                    
                    last_scan = status_data.get('last_scan_time')
                    if last_scan:
                        status_text += f"**🕐 Last Scan:** {last_scan}\n"
                    else:
                        status_text += f"**🕐 Last Scan:** Never\n"
                    
                    status_text += f"**🔄 Auto-Ingest:** {'✅ Enabled' if status_data.get('auto_ingest', False) else '❌ Disabled'}\n"
                    
                    # Add folder list with more detail
                    folders = status_data.get('monitored_folders', [])
                    if folders:
                        status_text += f"\n## 📋 Currently Monitored Folders\n\n"
                        for i, folder in enumerate(folders, 1):
                            # Normalize path display
                            display_path = os.path.normpath(str(folder))
                            status_text += f"{i}. `{display_path}`\n"
                            
                            # Add existence check
                            if os.path.exists(display_path):
                                status_text += f"   ✅ Folder exists and accessible\n"
                            else:
                                status_text += f"   ❌ Folder not found or inaccessible\n"
                    else:
                        status_text += f"\n## 📋 Monitored Folders\n\n❌ No folders are currently being monitored\n"
                        status_text += f"💡 Add a folder using the input field above."
                    
                    return status_text
                else:
                    return f"❌ Error: {data.get('error', 'Unknown error')}"
            else:
                return f"❌ HTTP Error: {response.status_code}"
        except Exception as e:
            return f"❌ Connection Error: {str(e)}"

    def get_vector_store_stats(self) -> str:
        """Get detailed statistics about the vector store contents"""
        try:
            # Get system stats
            response = requests.get(f"{self.api_url}/stats", timeout=30)
            
            if response.status_code == 200:
                stats = response.json()
                
                result = "📊 **Vector Store Statistics**\n\n"
                result += f"🔢 **Total Vectors:** {stats.get('total_vectors', 'Unknown')}\n"
                result += f"📄 **Total Documents:** {stats.get('total_documents', 'Unknown')}\n"
                result += f"📝 **Total Chunks:** {stats.get('total_chunks', 'Unknown')}\n"
                result += f"🧠 **Embedding Model:** {stats.get('embedding_model', 'Unknown')}\n"
                result += f"📐 **Vector Dimensions:** {stats.get('vector_dimensions', 'Unknown')}\n"
                result += f"💾 **Index Type:** {stats.get('index_type', 'Unknown')}\n"
                
                if 'documents' in stats and stats['documents']:
                    result += f"\n📋 **Documents in Vector Store:**\n"
                    for i, doc in enumerate(stats['documents'][:10], 1):  # Show first 10
                        result += f"{i}. `{doc}`\n"
                    
                    if len(stats['documents']) > 10:
                        result += f"... and {len(stats['documents']) - 10} more documents\n"
                else:
                    result += f"\n❌ **No documents found in vector store**\n"
                
                return result
            else:
                return f"❌ **Failed to get stats:** HTTP {response.status_code}\n{response.text[:200]}"
                
        except Exception as e:
            return f"❌ **Error getting vector store stats:** {str(e)}"

    def search_vector_store(self, search_term: str = "", limit: int = 20) -> str:
        """Search and list documents in the vector store"""
        try:
            # Get all document IDs from the vector store
            response = requests.get(f"{self.api_url}/documents", timeout=30)
            
            if response.status_code == 200:
                documents = response.json().get('documents', [])
                
                if not documents:
                    return "📭 **No documents found in vector store**\n\nThe vector store appears to be empty."
                
                # Filter documents if search term provided
                if search_term:
                    filtered_docs = [doc for doc in documents if search_term.lower() in doc.lower()]
                    result = f"🔍 **Search Results for '{search_term}'** ({len(filtered_docs)} found)\n\n"
                    documents = filtered_docs
                else:
                    result = f"📋 **All Documents in Vector Store** ({len(documents)} total)\n\n"
                
                # Limit results
                display_docs = documents[:limit]
                
                for i, doc_id in enumerate(display_docs, 1):
                    result += f"{i}. `{doc_id}`\n"
                    
                    # Check if this document is in our registry
                    registry_match = None
                    for reg_path, reg_info in self.document_registry.items():
                        if doc_id.startswith(reg_path) or reg_path in doc_id:
                            registry_match = reg_info
                            break
                    
                    if registry_match:
                        status_emoji = {
                            "active": "✅",
                            "updated": "🔄",
                            "deleted": "🗑️"
                        }.get(registry_match.get("status", "unknown"), "❓")
                        result += f"   {status_emoji} Registry: {registry_match.get('status', 'unknown')}\n"
                        result += f"   📁 File: {registry_match.get('filename', 'Unknown')}\n"
                    else:
                        result += f"   ❓ Not in UI registry (uploaded externally?)\n"
                    
                    result += "\n"
                
                if len(documents) > limit:
                    result += f"... and {len(documents) - limit} more documents\n"
                
                result += f"\n💡 **Registry vs Vector Store:**\n"
                result += f"📊 UI Registry: {len(self.document_registry)} documents\n"
                result += f"🗄️ Vector Store: {len(documents)} documents\n"
                
                if len(self.document_registry) != len(documents):
                    result += f"⚠️ **Mismatch detected!** Registry and vector store are out of sync.\n"
                
                return result
            else:
                return f"❌ **Failed to get documents:** HTTP {response.status_code}\n{response.text[:200]}"
                
        except Exception as e:
            return f"❌ **Error searching vector store:** {str(e)}"

    def sync_registry_with_vector_store(self) -> str:
        """Sync the UI registry with actual vector store contents"""
        try:
            # Get documents from vector store
            response = requests.get(f"{self.api_url}/documents", timeout=30)
            
            if response.status_code != 200:
                return f"❌ **Failed to get vector store documents:** HTTP {response.status_code}"
            
            vector_docs = response.json().get('documents', [])
            
            # Get stats for additional info
            stats_response = requests.get(f"{self.api_url}/stats", timeout=30)
            stats = stats_response.json() if stats_response.status_code == 200 else {}
            
            result = "🔄 **Syncing Registry with Vector Store**\n\n"
            
            # Clear current registry
            old_registry_count = len(self.document_registry)
            self.document_registry.clear()
            
            # Rebuild registry from vector store
            for doc_id in vector_docs:
                # Try to extract meaningful document path
                if doc_id.startswith('/'):
                    doc_path = doc_id
                else:
                    # Try to create a reasonable path
                    doc_path = f"/{doc_id}" if not doc_id.startswith('/') else doc_id
                
                # Add to registry with minimal info
                self.document_registry[doc_path] = {
                    'status': 'active',
                    'upload_count': 1,
                    'last_updated': datetime.now().isoformat(),
                    'filename': os.path.basename(doc_path) or 'Unknown',
                    'chunks': 'Unknown',
                    'source': 'vector_store_sync',
                    'doc_id': doc_id
                }
            
            result += f"📊 **Sync Results:**\n"
            result += f"🗑️ Cleared old registry: {old_registry_count} documents\n"
            result += f"📥 Added from vector store: {len(vector_docs)} documents\n"
            result += f"✅ Registry now has: {len(self.document_registry)} documents\n\n"
            
            result += f"📋 **Synced Documents:**\n"
            for i, (doc_path, info) in enumerate(self.document_registry.items(), 1):
                result += f"{i}. `{doc_path}` (ID: `{info.get('doc_id', 'Unknown')}`)\n"
            
            if not vector_docs:
                result += "❌ **Vector store is empty** - no documents to sync\n"
            
            return result
            
        except Exception as e:
            return f"❌ **Error syncing registry:** {str(e)}"

    def get_heartbeat_status(self) -> str:
        """Get heartbeat monitoring status"""
        try:
            response = requests.get(f"{self.api_url}/heartbeat/status", timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                
                enabled = status_data.get('enabled', False)
                status = status_data.get('status', 'unknown')
                interval = status_data.get('interval_seconds', 30)
                total_checks = status_data.get('total_checks', 0)
                last_check = status_data.get('last_check')
                
                result = f"💓 **Heartbeat Status**\n\n"
                
                if enabled:
                    result += f"🟢 **Status:** Active\n"
                else:
                    result += f"🔴 **Status:** Inactive\n"
                
                result += f"⏰ **Interval:** {interval} seconds\n"
                result += f"📊 **Total Checks:** {total_checks}\n"
                
                if last_check:
                    result += f"🕐 **Last Check:** {last_check}\n"
                
                result += f"📅 **Updated:** {datetime.now().strftime('%H:%M:%S')}\n"
                
                return result
            else:
                return f"❌ **Failed to get heartbeat status:** HTTP {response.status_code}"
                
        except Exception as e:
            return f"❌ **Error getting heartbeat status:** {str(e)}"

    def start_heartbeat(self) -> str:
        """Start heartbeat monitoring"""
        try:
            response = requests.post(f"{self.api_url}/heartbeat/start", timeout=10)
            
            if response.status_code == 200:
                result_data = response.json()
                return f"✅ **Heartbeat Started**\n📅 {result_data.get('message', 'Monitoring started')}"
            else:
                return f"❌ **Failed to start heartbeat:** HTTP {response.status_code}\n{response.text[:200]}"
                
        except Exception as e:
            return f"❌ **Error starting heartbeat:** {str(e)}"

    def stop_heartbeat(self) -> str:
        """Stop heartbeat monitoring"""
        try:
            response = requests.post(f"{self.api_url}/heartbeat/stop", timeout=10)
            
            if response.status_code == 200:
                result_data = response.json()
                return f"🛑 **Heartbeat Stopped**\n📅 {result_data.get('message', 'Monitoring stopped')}"
            else:
                return f"❌ **Failed to stop heartbeat:** HTTP {response.status_code}\n{response.text[:200]}"
                
        except Exception as e:
            return f"❌ **Error stopping heartbeat:** {str(e)}"

    def get_heartbeat_logs(self, limit: int = 20) -> str:
        """Get recent heartbeat logs"""
        try:
            response = requests.get(f"{self.api_url}/heartbeat/logs", 
                                  params={"limit": limit}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    logs = data.get('logs', [])
                    
                    if not logs:
                        return "📝 **No heartbeat logs available**"
                    
                    log_text = f"📝 **Recent Heartbeat Logs** (Last {len(logs)} entries)\n\n"
                    
                    for log in logs:
                        timestamp = log.get('timestamp', 'Unknown')
                        level = log.get('level', 'INFO')
                        message = log.get('message', 'No message')
                        
                        # Format timestamp
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            formatted_time = timestamp
                        
                        # Add emoji based on level
                        level_emoji = {
                            'INFO': 'ℹ️',
                            'WARNING': '⚠️',
                            'ERROR': '❌',
                            'DEBUG': '🔍'
                        }.get(level, '📝')
                        
                        log_text += f"{level_emoji} **{formatted_time}** [{level}] {message}\n"
                    
                    return log_text
                else:
                    return f"❌ **Error getting logs:** {data.get('error', 'Unknown error')}"
            else:
                return f"❌ **HTTP Error {response.status_code}** getting heartbeat logs"
                
        except Exception as e:
            return f"❌ **Error getting heartbeat logs:** {str(e)}"

    def get_documents_in_vector_store(self) -> str:
        """Get all documents in the vector store with their chunk counts"""
        try:
            # Get vector store statistics
            try:
                response = requests.get(f"{self.api_url}/stats", timeout=10)
                
                if response.status_code != 200:
                    return f"❌ **Error getting stats:** HTTP {response.status_code}"
                
                stats = response.json()
            except Exception as e:
                return f"❌ **Error getting stats:** {str(e)}"
            
            # Get detailed vector information
            try:
                health_response = requests.get(f"{self.api_url}/health", timeout=10)
                
                if health_response.status_code != 200:
                    return f"❌ **Error getting health info:** HTTP {health_response.status_code}"
                
                health_data = health_response.json()
                components = health_data.get('components', {})
                faiss_store = components.get('faiss_store', {})
            except Exception as e:
                return f"❌ **Error getting health info:** {str(e)}"
            
            # Try to get vectors from management API first
            try:
                vectors_response = requests.get(f"{self.api_url}/manage/vectors", 
                                            params={"limit": 1000}, timeout=15)
                
                if vectors_response.status_code == 200:
                    vectors_data = vectors_response.json()
                    vectors = vectors_data if isinstance(vectors_data, list) else []
                    
                    if not vectors:
                        return "📄 **No documents found in vector store**\n\n💡 Upload some documents to see them here!"
                    
                    # Group vectors by document
                    documents = {}
                    
                    for i, vector in enumerate(vectors):
                        try:
                            # Add safety check for None vector
                            if vector is None:
                                print(f"DEBUG: Vector {i} is None, skipping")
                                continue
                            
                            # Ensure vector is a dict
                            if not isinstance(vector, dict):
                                print(f"DEBUG: Vector {i} is not a dict: {type(vector)}, skipping")
                                continue
                            
                            metadata = vector.get('metadata', {})
                            
                            # Add safety check for None metadata
                            if metadata is None:
                                print(f"DEBUG: Metadata for vector {i} is None, using empty dict")
                                metadata = {}
                            
                            # Try different ways to get document identifier
                            doc_path = None
                            doc_name = None
                            
                            # Priority 1: doc_path from metadata
                            if isinstance(metadata, dict) and 'doc_path' in metadata:
                                doc_path = metadata['doc_path']
                                if doc_path and '/' in str(doc_path):
                                    doc_name = str(doc_path).split('/')[-1]
                                else:
                                    doc_name = str(doc_path)
                            
                            # Priority 2: doc_id from vector
                            elif isinstance(vector, dict) and 'doc_id' in vector:
                                doc_path = vector['doc_id']
                                if doc_path and '/' in str(doc_path):
                                    doc_name = str(doc_path).split('/')[-1]
                                else:
                                    doc_name = str(doc_path)
                            
                            # Priority 3: nested metadata
                            elif isinstance(metadata, dict) and 'metadata' in metadata:
                                nested_meta = metadata.get('metadata')
                                if isinstance(nested_meta, dict):
                                    if 'doc_path' in nested_meta:
                                        doc_path = nested_meta['doc_path']
                                        if doc_path and '/' in str(doc_path):
                                            doc_name = str(doc_path).split('/')[-1]
                                        else:
                                            doc_name = str(doc_path)
                                    elif 'filename' in nested_meta:
                                        doc_name = nested_meta['filename']
                                        doc_path = f"/docs/{doc_name}"
                            
                            # Priority 4: filename from metadata
                            elif isinstance(metadata, dict) and 'filename' in metadata:
                                doc_name = metadata['filename']
                                doc_path = f"/docs/{doc_name}"
                            
                            # Priority 5: file_path
                            elif isinstance(metadata, dict) and 'file_path' in metadata:
                                file_path = metadata['file_path']
                                doc_name = os.path.basename(str(file_path))
                                doc_path = f"/docs/{doc_name}"
                            
                            # Fallback
                            else:
                                vector_id = vector.get('vector_id', 'unknown') if isinstance(vector, dict) else 'unknown'
                                doc_path = f"/unknown/vector_{vector_id}"
                                doc_name = f"Unknown Document {vector_id}"
                            
                            # Ensure doc_path is not None
                            if doc_path is None:
                                doc_path = f"/unknown/vector_{i}"
                                doc_name = f"Unknown Document {i}"
                            
                            if doc_path not in documents:
                                documents[doc_path] = {
                                    'name': doc_name,
                                    'path': doc_path,
                                    'chunks': 0,
                                    'source': metadata.get('source', 'unknown') if isinstance(metadata, dict) else 'unknown',
                                    'last_updated': None,
                                    'file_size': None,
                                    'original_filename': None
                                }
                            
                            documents[doc_path]['chunks'] += 1
                            
                            # Update metadata if available (with safety checks)
                            if isinstance(metadata, dict):
                                if 'ingestion_time' in metadata:
                                    documents[doc_path]['last_updated'] = metadata['ingestion_time']
                                elif 'added_at' in metadata:
                                    documents[doc_path]['last_updated'] = metadata['added_at']
                                elif 'metadata' in metadata and isinstance(metadata['metadata'], dict):
                                    nested = metadata['metadata']
                                    if 'ingestion_time' in nested:
                                        documents[doc_path]['last_updated'] = nested['ingestion_time']
                                
                                if 'file_size' in metadata:
                                    documents[doc_path]['file_size'] = metadata['file_size']
                                elif 'metadata' in metadata and isinstance(metadata['metadata'], dict):
                                    nested = metadata['metadata']
                                    if 'file_size' in nested:
                                        documents[doc_path]['file_size'] = nested['file_size']
                                
                                if 'original_filename' in metadata:
                                    documents[doc_path]['original_filename'] = metadata['original_filename']
                                elif 'metadata' in metadata and isinstance(metadata['metadata'], dict):
                                    nested = metadata['metadata']
                                    if 'original_filename' in nested:
                                        documents[doc_path]['original_filename'] = nested['original_filename']
                        
                        except Exception as e:
                            print(f"DEBUG: Error processing vector {i}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                else:
                    # Fallback: try to get document info from folder monitor
                    try:
                        folder_response = requests.get(f"{self.api_url}/folder-monitor/files", timeout=10)
                        if folder_response.status_code == 200:
                            folder_data = folder_response.json()
                            if folder_data.get('success'):
                                files = folder_data.get('files', {})
                                
                                if not files:
                                    return "📄 **No documents found in folder monitoring**\n\n💡 Upload some documents to see them here!"
                                
                                doc_text = f"📄 **Documents from Folder Monitor** ({len(files)} files)\n\n"
                                
                                for file_path, file_info in files.items():
                                    if file_info is None:
                                        continue
                                    filename = os.path.basename(str(file_path))
                                    status = file_info.get('ingestion_status', 'unknown') if isinstance(file_info, dict) else 'unknown'
                                    size = file_info.get('size', 0) if isinstance(file_info, dict) else 0
                                    
                                    status_emoji = {
                                        'success': '✅',
                                        'pending': '⏳',
                                        'failed': '❌'
                                    }.get(status, '❓')
                                    
                                    doc_text += f"{status_emoji} **{filename}**\n"
                                    doc_text += f"   📁 Path: `{file_path}`\n"
                                    doc_text += f"   📊 Status: {status}\n"
                                    doc_text += f"   📏 Size: {size:,} bytes\n"
                                    
                                    if isinstance(file_info, dict) and file_info.get('last_ingested'):
                                        doc_text += f"   🕐 Last Ingested: {file_info['last_ingested']}\n"
                                    
                                    doc_text += "\n"
                                
                                return doc_text
                    except Exception as e:
                        print(f"DEBUG: Error in folder monitor fallback: {str(e)}")
                    
                    return f"❌ **Error getting vectors:** HTTP {vectors_response.status_code}\n\n💡 Try uploading some documents first!"
            
            except Exception as e:
                print(f"DEBUG: Error getting vectors: {str(e)}")
                import traceback
                traceback.print_exc()
                return f"❌ **Error getting vectors:** {str(e)}"
            
            # Format the output
            if not documents:
                return "📄 **No documents found in vector store**\n\n💡 Upload some documents to see them here!"
                
            total_docs = len(documents)
            total_chunks = sum(doc['chunks'] for doc in documents.values())
            
            doc_text = f"📄 **Documents in Vector Store** ({total_docs} documents, {total_chunks} chunks)\n\n"
            
            # Sort documents by chunk count (descending)
            sorted_docs = sorted(documents.items(), key=lambda x: x[1]['chunks'], reverse=True)
            
            for doc_path, doc_info in sorted_docs:
                doc_text += f"📄 **{doc_info['name']}**\n"
                doc_text += f"   📁 Path: `{doc_path}`\n"
                doc_text += f"   📝 Chunks: **{doc_info['chunks']}**\n"
                doc_text += f"   🔧 Source: {doc_info['source']}\n"
                
                if doc_info['original_filename'] and doc_info['original_filename'] != doc_info['name']:
                    doc_text += f"   📁 Original File: {doc_info['original_filename']}\n"
                
                if doc_info['file_size']:
                    size_mb = doc_info['file_size'] / (1024 * 1024)
                    if size_mb >= 1:
                        doc_text += f"   📏 Size: {size_mb:.2f} MB\n"
                    else:
                        size_kb = doc_info['file_size'] / 1024
                        doc_text += f"   📏 Size: {size_kb:.1f} KB\n"
                
                if doc_info['last_updated']:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(doc_info['last_updated'].replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        doc_text += f"   🕐 Last Updated: {formatted_time}\n"
                    except:
                        doc_text += f"   🕐 Last Updated: {doc_info['last_updated']}\n"
                
                doc_text += "\n"
            
            # Add summary statistics
            doc_text += "📊 **Vector Store Statistics:**\n"
            doc_text += f"   📄 Total Documents: {total_docs}\n"
            doc_text += f"   📝 Total Chunks: {total_chunks}\n"
            doc_text += f"   📊 Total Vectors: {stats.get('total_vectors', 0):,}\n"
            doc_text += f"   📈 Average Chunks per Document: {total_chunks / total_docs if total_docs > 0 else 0:.1f}\n"
            
            return doc_text
            
        except Exception as e:
            print(f"DEBUG: Top-level error in get_documents_in_vector_store: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"❌ **Error getting documents:** {str(e)}"

    def delete_document_from_overview(self, document_selection: str) -> str:
        """Delete a document selected from the Document Overview"""
        if not document_selection or not document_selection.strip():
            return "❌ Please select a document to delete"
        
        if document_selection == "No documents available":
            return "❌ No documents available to delete"
        
        try:
            # Extract document path from the selection
            # Format is typically: "📄 document_path (X chunks)"
            
            # Try to extract document path from various formats
            doc_path = None
            
            # Pattern 1: "📄 path/to/doc (X chunks)"
            match = re.search(r'📄\s*([^\(]+?)\s*\(\d+\s*chunks?\)', document_selection)
            if match:
                doc_path = match.group(1).strip()
            
            # Pattern 2: Just the path itself
            if not doc_path and not document_selection.startswith('📄'):
                doc_path = document_selection.strip()
            
            # Pattern 3: Extract from markdown-style format
            if not doc_path:
                # Look for patterns like "**document_path**" or "`document_path`"
                match = re.search(r'(?:\*\*|`)([^*`]+)(?:\*\*|`)', document_selection)
                if match:
                    doc_path = match.group(1).strip()
            
            if not doc_path:
                return f"❌ Could not extract document path from selection: {document_selection}"
            
            # Call the backend API to delete the document
            try:
                import urllib.parse
                encoded_doc_path = urllib.parse.quote(doc_path, safe='')
                
                response = requests.delete(
                    f"{self.api_url}/documents/{encoded_doc_path}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    delete_result = response.json()
                    vectors_deleted = delete_result.get('vectors_deleted', 0)
                    
                    result = f"✅ **Document Deleted Successfully**\n\n"
                    result += f"📄 **Document Path:** `{doc_path}`\n"
                    result += f"🗑️ **Vectors Deleted:** {vectors_deleted}\n"
                    result += f"🕐 **Deleted At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    result += f"**Next Steps:**\n"
                    result += f"1. Click 'Refresh Documents' to update the list\n"
                    result += f"2. Test queries to verify content is no longer found\n"
                    result += f"3. Check vector store stats for updated counts"
                    
                    # Update local registry if it exists
                    if hasattr(self, 'document_registry') and doc_path in self.document_registry:
                        self.document_registry[doc_path]["status"] = "deleted"
                        self.document_registry[doc_path]["deleted_at"] = datetime.now().isoformat()
                        self.document_registry[doc_path]["vectors_deleted"] = vectors_deleted
                    
                    return result
                    
                elif response.status_code == 404:
                    return f"❌ Document not found: `{doc_path}`\n\nThe document may have already been deleted or the path is incorrect."
                    
                else:
                    error_msg = response.text if response.text else f"HTTP {response.status_code}"
                    return f"❌ **Failed to delete document**\n\nDocument: `{doc_path}`\nError: {error_msg}"
                    
            except requests.exceptions.RequestException as e:
                return f"❌ **Network error while deleting document**\n\nDocument: `{doc_path}`\nError: {str(e)}"
                
        except Exception as e:
            return f"❌ **Error processing deletion**\n\nSelection: {document_selection}\nError: {str(e)}"

    def get_document_paths_from_overview(self) -> List[str]:
        """Extract document paths from the overview display for the delete dropdown"""
        try:
            # Get the current documents from the vector store
            response = requests.get(f"{self.api_url}/manage/vectors", params={"limit": 1000}, timeout=30)
            
            if response.status_code != 200:
                return ["No documents available"]
            
            # The API returns a list of vectors directly, not a dict with 'vectors' key
            vectors = response.json()
            
            if not vectors or not isinstance(vectors, list):
                return ["No documents available"]
            
            # Group vectors by document to get unique document paths
            documents = {}
            
            for vector in vectors:
                metadata = vector.get('metadata', {})
                
                # Skip deleted vectors
                if metadata.get('deleted', False):
                    continue
                
                # Try to identify the document using various metadata fields
                doc_path = None
                
                # Priority order based on test results:
                # 1. file_path (most common)
                # 2. filename (common)
                # 3. file_name (backup)
                # 4. doc_path (legacy)
                # 5. doc_id from vector level (fallback)
                
                for field in ['file_path', 'filename', 'file_name', 'doc_path']:
                    if field in metadata and metadata[field]:
                        doc_path = metadata[field]
                        break
                
                # Try doc_id from vector level as fallback
                if not doc_path:
                    doc_id = vector.get('doc_id', '')
                    if doc_id and doc_id != 'unknown':
                        doc_path = doc_id
                
                # Handle nested metadata
                if not doc_path and 'metadata' in metadata:
                    nested = metadata['metadata']
                    for field in ['file_path', 'filename', 'file_name', 'doc_path']:
                        if field in nested and nested[field]:
                            doc_path = nested[field]
                            break
                
                if doc_path:
                    # Clean up the document path for display
                    display_path = doc_path
                    
                    # Clean up common prefixes
                    if display_path.startswith('doc_'):
                        display_path = display_path[4:].replace('_', '/')
                    
                    # For file paths, show a cleaner version
                    if '\\' in display_path or '/' in display_path:
                        # For temp files, show just the filename
                        if 'Temp' in display_path or 'tmp' in display_path:
                            import os
                            display_path = f"temp/{os.path.basename(display_path)}"
                        # For folder monitor paths, keep the relative path
                        elif 'folder_monitor' in display_path:
                            display_path = display_path
                        # For other paths, show relative path from docs
                        elif display_path.startswith('/docs/'):
                            display_path = display_path
                        else:
                            # Show just the filename for other absolute paths
                            import os
                            filename = os.path.basename(display_path)
                            display_path = f"docs/{filename}"
                    
                    if display_path not in documents:
                        documents[display_path] = 0
                    documents[display_path] += 1
            
            if not documents:
                return ["No documents available"]
            
            # Sort by chunk count (descending) and return as formatted options
            sorted_docs = sorted(documents.items(), key=lambda x: x[1], reverse=True)
            
            # Format as "📄 document_path (X chunks)"
            formatted_docs = []
            for doc_path, chunk_count in sorted_docs:
                formatted_docs.append(f"📄 {doc_path} ({chunk_count} chunks)")
            
            return formatted_docs
            
        except Exception as e:
            print(f"Error getting document paths from overview: {e}")
            return ["Error loading documents"]

    def get_monitored_folders(self) -> tuple[str, list]:
        """Get list of currently monitored folders"""
        try:
            response = requests.get(f"{self.api_url}/folder-monitor/folders", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    folders = data.get('folders', [])
                    if folders:
                        folder_list = "\n".join([f"📁 {folder}" for folder in folders])
                        return f"## 📁 Currently Monitored Folders ({len(folders)})\n\n{folder_list}", folders
                    else:
                        return "## 📁 Currently Monitored Folders (0)\n\n*No folders are currently being monitored*", []
                else:
                    return f"❌ Error: {data.get('error', 'Unknown error')}", []
            else:
                return f"❌ HTTP {response.status_code}: {response.text}", []
        except Exception as e:
            return f"❌ Failed to get monitored folders: {str(e)}", []

    def remove_folder_monitoring(self, folder_path: str) -> str:
        """Remove a specific folder from monitoring"""
        if not folder_path or not folder_path.strip():
            return "❌ Please select a folder to remove"
        
        folder_path = folder_path.strip()
        
        try:
            response = requests.post(
                f"{self.api_url}/folder-monitor/remove",
                json={"folder_path": folder_path},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    files_removed = data.get('files_removed', 0)
                    return f"✅ Successfully removed folder from monitoring: {folder_path}\n📄 Files removed from tracking: {files_removed}"
                else:
                    return f"❌ Failed to remove folder: {data.get('error', 'Unknown error')}"
            else:
                return f"❌ HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"❌ Failed to remove folder from monitoring: {str(e)}"
    
    # =================== CONVERSATION METHODS ===================
    
    def start_new_conversation(self) -> Tuple[List[Dict[str, str]], str, str]:
        """Start a new conversation session using the new thread-based API"""
        try:
            response = requests.post(f"{self.api_url}/api/conversation/start", json={})
            
            if response.status_code == 200:
                data = response.json()
                thread_id = data.get("thread_id", "")
                initial_response = data.get("response", "Hello! I'm ready to help you with questions about your documents. What would you like to know?")
                
                # Return conversation history, thread ID, and status
                conversation_history = [
                    {"role": "assistant", "content": initial_response}
                ]
                
                return conversation_history, thread_id, "✅ New conversation started with LangGraph state persistence!"
            elif response.status_code == 404:
                # Conversation API not available
                error_msg = """🚧 **Conversation Feature Not Available**

The LangGraph conversation system is not currently available. This could be due to:

• **Missing LangGraph dependencies** - Run: `pip install langgraph langgraph-checkpoint`
• **Server configuration issue** - Check server logs
• **API routes not registered** - Restart the RAG server

**To enable conversations:**
1. Ensure LangGraph is installed: `pip install langgraph>=0.0.40 langgraph-checkpoint>=1.0.0`
2. Restart the RAG server: `python main.py`
3. Check server logs for any errors

**Alternative:** You can still use the regular Query Testing tab for Q&A functionality."""
                
                error_history = [{"role": "assistant", "content": error_msg}]
                return error_history, "", "❌ Conversation API not available (404)"
            else:
                error_history = [{"role": "assistant", "content": f"Error starting conversation: HTTP {response.status_code}"}]
                return error_history, "", f"❌ Failed to start conversation: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            error_history = [{"role": "assistant", "content": f"Connection error: {str(e)}"}]
            return error_history, "", f"❌ Connection error: {str(e)}"
        except Exception as e:
            error_history = [{"role": "assistant", "content": f"Error: {str(e)}"}]
            return error_history, "", f"❌ Error starting conversation: {str(e)}"

    def send_conversation_message(self, message: str, thread_id: str, history: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]], str, Dict[str, Any]]:
        """Send a message in the conversation with enhanced suggestions using thread_id"""
        if not message.strip():
            return "", history, "Please enter a message", {}
        
        if not thread_id or thread_id == "No thread":
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": "Please start a new conversation first"})
            return "", history, "No active thread", {}
        
        try:
            # Add user message to history
            history.append({"role": "user", "content": message})
            
            # Send to API using thread_id
            response = requests.post(
                f"{self.api_url}/api/conversation/message",
                json={"message": message, "thread_id": thread_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_response = data.get('response', 'No response generated')
                
                # Add assistant response to history
                history.append({"role": "assistant", "content": assistant_response})
                
                # Format additional info
                info_parts = []
                if data.get('turn_count'):
                    info_parts.append(f"Turn: {data['turn_count']}")
                if data.get('current_phase'):
                    info_parts.append(f"Phase: {data['current_phase']}")
                if data.get('confidence_score'):
                    info_parts.append(f"Confidence: {data['confidence_score']:.2f}")
                
                thread_info = " | ".join(info_parts) if info_parts else "Active conversation"
                
                # Extract enhanced response data for UI
                enhanced_data = self._extract_enhanced_response_data(data)
                
                return "", history, f"✅ {thread_info}", enhanced_data
            elif response.status_code == 404:
                error_msg = "🚧 Conversation API not available. Please use the Query Testing tab for Q&A functionality."
                history.append({"role": "assistant", "content": error_msg})
                return "", history, "❌ Conversation API not available (404)", {}
            else:
                history.append({"role": "assistant", "content": f"Error: {response.status_code}"})
                return "", history, f"❌ API Error: {response.status_code}", {}
                
        except requests.exceptions.RequestException as e:
            history.append({"role": "assistant", "content": f"Connection error: {str(e)}"})
            return "", history, f"❌ Connection error: {str(e)}", {}
        except Exception as e:
            history.append({"role": "assistant", "content": f"Error: {str(e)}"})
            return "", history, f"❌ Error: {str(e)}", {}
    
    def _extract_enhanced_response_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enhanced response data for UI elements"""
        enhanced = {
            'suggestions': [],
            'topics': [],
            'entities': [],
            'technical_terms': [],
            'insights': {},
            'hints': []
        }
        
        # Handle case where response_data is None or empty
        if not response_data:
            return enhanced
        
        # Extract suggestions with fallback
        suggested_questions = response_data.get('suggested_questions', [])
        if suggested_questions:
            # Handle both list of dicts and list of strings
            processed_suggestions = []
            for suggestion in suggested_questions[:4]:
                if isinstance(suggestion, dict):
                    processed_suggestions.append(suggestion)
                elif isinstance(suggestion, str):
                    # Convert string to dict format
                    processed_suggestions.append({
                        'question': suggestion,
                        'icon': '💬',
                        'priority': 0.5,
                        'has_quick_answer': False
                    })
            enhanced['suggestions'] = processed_suggestions
        
        # Extract exploration data with fallback
        explore_more = response_data.get('explore_more', {})
        if explore_more:
            # Handle topics
            topics = explore_more.get('topics', [])
            processed_topics = []
            for topic in topics[:6]:
                if isinstance(topic, dict):
                    processed_topics.append(topic.get('name', str(topic)))
                else:
                    processed_topics.append(str(topic))
            enhanced['topics'] = processed_topics
            
            # Handle entities
            entities = explore_more.get('entities', [])
            enhanced['entities'] = entities[:4]
            
            # Handle technical terms
            technical_terms = explore_more.get('technical_terms', [])
            enhanced['technical_terms'] = technical_terms[:3]
        
        # Extract conversation insights with fallback
        conversation_insights = response_data.get('conversation_insights', {})
        if conversation_insights:
            enhanced['insights'] = {
                'topic_continuity': conversation_insights.get('topic_continuity', 0),
                'information_coverage': conversation_insights.get('information_coverage', 'unknown'),
                'exploration_path': conversation_insights.get('suggested_exploration_path', [])
            }
        
        # Generate interaction hints
        enhanced['hints'] = self._generate_interaction_hints(response_data)
        
        return enhanced
    
    def _generate_interaction_hints(self, response_data: Dict[str, Any]) -> List[str]:
        """Generate helpful interaction hints based on response"""
        hints = []
        
        # Based on suggestions available
        if response_data.get('suggested_questions'):
            hints.append("💡 Click the suggestion buttons below for quick follow-up questions")
        
        # Based on sources found
        sources_count = response_data.get('total_sources', 0)
        if sources_count > 0:
            hints.append(f"📚 Found {sources_count} relevant sources - ask for more details or examples")
        
        # Based on exploration topics
        if response_data.get('explore_more', {}).get('topics'):
            hints.append("🔍 Click topic chips to explore related areas in depth")
        
        # Based on confidence
        confidence = response_data.get('confidence_score', 0)
        if confidence < 0.6:
            hints.append("🎯 Try rephrasing your question or asking for clarification")
        elif confidence > 0.8:
            hints.append("✅ High confidence response - consider exploring related topics")
        
        return hints[:3]  # Limit to 3 hints
    
    def end_conversation(self, thread_id: str) -> Tuple[List[Dict[str, str]], str, str]:
        """End the current conversation using thread_id"""
        if not thread_id or thread_id == "No thread":
            return [], "", "No active conversation to end"
        
        try:
            response = requests.post(f"{self.api_url}/api/conversation/end/{thread_id}")
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get('summary', 'Conversation ended')
                total_turns = data.get('total_turns', 0)
                
                end_history = [{
                    "role": "assistant", 
                    "content": f"🎯 Conversation ended.\n\nSummary: {summary}\nTotal turns: {total_turns}\n\nThank you for the conversation!"
                }]
                
                return end_history, "", f"✅ Conversation ended - {total_turns} turns"
            else:
                return [], thread_id, f"❌ Failed to end conversation: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return [], thread_id, f"❌ Connection error: {str(e)}"
        except Exception as e:
            return [], thread_id, f"❌ Error ending conversation: {str(e)}"
    
    def get_conversation_status(self, thread_id: str) -> str:
        """Get current conversation status using thread_id"""
        if not thread_id or thread_id == "No thread":
            return "No active conversation"
        
        try:
            response = requests.get(f"{self.api_url}/api/conversation/history/{thread_id}")
            
            if response.status_code == 200:
                data = response.json()
                return f"Thread: {thread_id[:8]}... | Turns: {data.get('turn_count', 0)} | Phase: {data.get('current_phase', 'unknown')}"
            else:
                return f"Error getting status: {response.status_code}"
                
        except Exception as e:
            return f"Status unavailable: {str(e)}"

def create_fixed_interface():
    """Create the fixed document lifecycle management interface"""
    
    print("DEBUG: Creating FixedRAGUI instance")
    ui = FixedRAGUI()
    print("DEBUG: FixedRAGUI instance created")
    
    # Custom CSS
    css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .lifecycle-section {
        border: 2px solid #e1e5e9;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .status-success { color: #28a745; font-weight: bold; }
    .status-error { color: #dc3545; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    
    /* Enhanced conversation styles */
    .conversation-suggestions {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #dee2e6;
    }
    
    .suggestion-button {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        border: none;
        border-radius: 8px;
        color: white;
        padding: 8px 16px;
        margin: 4px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,123,255,0.2);
        white-space: normal;
        word-wrap: break-word;
        text-align: left;
        line-height: 1.3;
        min-height: 40px;
        display: flex;
        align-items: center;
    }
    
    .suggestion-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,123,255,0.3);
    }
    
    .topic-chip {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        border: none;
        border-radius: 20px;
        color: white;
        padding: 6px 12px;
        margin: 3px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(40,167,69,0.2);
    }
    
    .topic-chip:hover {
        transform: scale(1.05);
        box-shadow: 0 3px 6px rgba(40,167,69,0.3);
    }
    
    .conversation-insights {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #ffc107;
    }
    
    .entity-card {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-radius: 8px;
        padding: 10px;
        margin: 6px 0;
        border-left: 3px solid #17a2b8;
    }
    
    .technical-term {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-radius: 6px;
        padding: 8px;
        margin: 4px 0;
        border-left: 3px solid #dc3545;
        font-family: 'Courier New', monospace;
    }
    
    .interaction-hint {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
        border-left: 3px solid #28a745;
        font-size: 14px;
    }
    
    .debug-panel {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 10px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        max-height: 300px;
        overflow-y: auto;
    }
    
    /* Animation for suggestion updates */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .suggestion-container {
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .suggestion-button {
            font-size: 12px;
            padding: 6px 12px;
            min-height: 35px;
            line-height: 1.2;
        }
        
        .topic-chip {
            font-size: 10px;
            padding: 4px 8px;
        }
    }
    """
    
    with gr.Blocks(css=css, title="RAG System - Fixed Document Lifecycle") as interface:
        
        gr.Markdown("""
        # 📁 Network Knowledge Management
        """)
        
        # Connection Status
        with gr.Row():
            connection_status = gr.Markdown(
                value="🔍 Checking API connection...",
                label="API Connection Status"
            )
            refresh_connection_btn = gr.Button("🔄 Refresh Connection", size="sm")
        
        with gr.Tabs():
            
            # Document Management Tab
            with gr.Tab("📁 Document Management"):
                gr.Markdown("### 🔧 Improved Document Management Flow")
                
                with gr.Row():
                    # Left Column: Document Operations
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📝 Upload or Update Document")
                        gr.Markdown("""
                        **How it works:**
                        - 📁 **First time**: Upload creates a new document
                        - 🔄 **Same path**: Automatically updates existing document
                        - ✅ **Auto-refresh**: Dropdowns update immediately
                        """)
                        
                        # Main Upload/Update Section
                        file_input = gr.File(
                            label="📁 Select File to Upload/Update",
                            file_types=[".txt", ".pdf", ".docx", ".doc", ".md", ".json", ".csv", ".xlsx", ".xls", ".xlsm", ".xlsb"],
                            type="filepath"
                        )
                        
                        doc_path_input = gr.Textbox(
                            label="📄 Document Path (Optional)",
                            placeholder="e.g., /docs/my-document (auto-generated if empty)",
                            info="If path exists, document will be updated. If new, document will be created."
                        )
                        
                        upload_btn = gr.Button("📤 Upload/Update Document", variant="primary", size="lg")
                        
                        gr.Markdown("---")
                        
                        # Delete Section
                        gr.Markdown("#### 🗑️ Delete Document")
                        delete_doc_path_input = gr.Dropdown(
                            label="📄 Select Document to Delete",
                            choices=["(No documents uploaded yet)"],
                            allow_custom_value=False,
                            info="Choose from uploaded documents"
                        )
                        
                        delete_doc_btn = gr.Button("🗑️ Delete Document", variant="stop")
                        
                        gr.Markdown("---")
                        
                        # Clear Vector Store Section
                        gr.Markdown("#### 🧹 Clear Vector Store")
                        gr.Markdown("""
                        **⚠️ DANGER ZONE**: This will permanently delete ALL documents and vectors from the system.
                        Use this to completely reset the vector store for testing or cleanup.
                        """)
                        
                        clear_vector_store_btn = gr.Button(
                            "🧹 Clear All Vectors & Documents", 
                            variant="stop",
                            size="sm"
                        )
                        
                        gr.Markdown("---")
                        
                        operation_result = gr.Markdown(
                            label="Operation Result",
                            value="Ready for document operations..."
                        )
                    
                    # Right Column: Document Registry
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📋 Document Registry")
                        
                        document_registry_display = gr.Markdown(
                            label="Active Documents",
                            value="📋 No documents in registry",
                            height=600
                        )
                        
                        refresh_registry_btn = gr.Button("🔄 Refresh Registry")
            
            # Query Testing Tab
            with gr.Tab("🔍 Query Testing"):
                gr.Markdown("### Test Queries to See Document Lifecycle Effects")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        test_query_input = gr.Textbox(
                            label="🔍 Test Query",
                            placeholder="Enter a query to test document lifecycle effects...",
                            lines=2
                        )
                        
                        max_results_slider = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="Maximum Results"
                        )
                        
                        test_query_btn = gr.Button("🔍 Test Query", variant="primary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 💡 Improved Testing Flow")
                        gr.Markdown("""
                        **Simple Workflow:**
                        1. 📁 Upload a document file
                        2. 🔍 Query for content → should appear
                        3. 📁 Upload different file with same path
                        4. 🔍 Query again → should show updated content
                        5. 🗑️ Delete the document
                        6. 🔍 Query again → should show deletion marker
                        
                        **No more confusion:**
                        - ✅ Same interface for upload and update
                        - ✅ Automatic dropdown refresh
                        - ✅ Clear status messages
                        - ✅ Upload count tracking
                        """)
                
                # Query Results
                with gr.Row():
                    with gr.Column():
                        query_answer = gr.Textbox(
                            label="🤖 AI Response",
                            lines=6,
                            interactive=False
                        )
                    
                    with gr.Column():
                        query_sources = gr.Markdown(
                            label="📚 Sources & Citations"
                        )
                
                query_lifecycle_analysis = gr.Markdown(
                    label="🔍 Document Lifecycle Analysis"
                )
                
                # Feedback Section
                gr.Markdown("---")
                gr.Markdown("### 👍👎 Response Feedback")
                gr.Markdown("**Help us improve by rating the response quality:**")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        feedback_helpful_btn = gr.Button("👍 Helpful", variant="primary", size="sm")
                        feedback_not_helpful_btn = gr.Button("👎 Not Helpful", variant="stop", size="sm")
                    
                    with gr.Column(scale=2):
                        feedback_text_input = gr.Textbox(
                            label="💬 Additional Comments (Optional)",
                            placeholder="Tell us what was good or what could be improved...",
                            lines=2,
                            max_lines=3
                        )
                
                feedback_result = gr.Markdown(
                    label="Feedback Status",
                    value="",
                    visible=False
                )
                
                # Feedback Statistics Section
                gr.Markdown("---")
                gr.Markdown("### 📊 Feedback Statistics")
                
                with gr.Row():
                    get_feedback_stats_btn = gr.Button("📊 View Feedback Stats", variant="secondary", size="sm")
                
                feedback_stats_display = gr.Markdown(
                    label="System Feedback Statistics",
                    value="Click 'View Feedback Stats' to see system performance metrics...",
                    visible=True
                )
            
            # Document Overview Tab
            with gr.Tab("📄 Document Overview"):
                gr.Markdown("### 📄 Documents in Vector Store")
                gr.Markdown("""
                **View and manage all documents currently stored in the vector database:**
                - 📊 **Document List**: See all documents with chunk counts
                - 📏 **File Sizes**: View original file sizes
                - 🕐 **Last Updated**: When each document was last modified
                - 🔧 **Source**: How each document was ingested (UI, folder monitor, etc.)
                - 📈 **Statistics**: Total vectors, active vs deleted
                - 🗑️ **Delete Documents**: Remove documents and their vectors
                """)
                
                with gr.Row():
                    with gr.Column(scale=3):
                        # Document list display
                        documents_display = gr.Markdown(
                            label="Documents in Vector Store",
                            value="🔍 Click 'Refresh Documents' to load document information...",
                            height=500
                        )
                        
                        # Delete result display
                        delete_result_display = gr.Markdown(
                            label="Delete Operation Result",
                            value="",
                            visible=True
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🔄 Controls")
                        
                        refresh_documents_btn = gr.Button(
                            "🔄 Refresh Documents", 
                            variant="primary",
                            size="lg"
                        )
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### 🗑️ Delete Document")
                        
                        document_selection_dropdown = gr.Dropdown(
                            label="Select Document to Delete",
                            choices=["No documents available"],
                            value=None,
                            interactive=True,
                            info="Choose a document to permanently delete"
                        )
                        
                        delete_document_btn = gr.Button(
                            "🗑️ Delete Selected Document",
                            variant="stop",
                            size="lg"
                        )
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### 💡 What You'll See")
                        gr.Markdown("""
                        **For each document:**
                        - 📄 **Document name** and path
                        - 📝 **Number of chunks** created
                        - 🔧 **Source** (UI upload, folder monitor, etc.)
                        - 📏 **File size** (if available)
                        - 🕐 **Last updated** timestamp
                        
                        **Summary statistics:**
                        - ✅ **Active vectors** (searchable)
                        - 🗑️ **Deleted vectors** (soft-deleted)
                        - 📏 **Vector dimension**
                        - 💾 **Index file size**
                        
                        **Sorted by chunk count** (largest first)
                        """)
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### ⚠️ Delete Warning")
                        gr.Markdown("""
                        **Deleting a document will:**
                        - ❌ Remove all vectors from the vector store
                        - ❌ Make the content unsearchable
                        - ❌ Cannot be undone easily
                        
                        **Before deleting:**
                        - Make sure you have backups if needed
                        - Consider if the document is still useful
                        - Test queries to verify deletion worked
                        """)
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### 🔍 Troubleshooting")
                        gr.Markdown("""
                        **If no documents appear:**
                        - Check if backend is running
                        - Verify documents were uploaded
                        - Try uploading a test document
                        
                        **If chunk counts seem wrong:**
                        - Different file types create different chunk counts
                        - Large files create more chunks
                        - Text chunking depends on content structure
                        """)
            
            # Folder Monitoring Tab
            with gr.Tab("📁 Folder Monitor"):
                gr.Markdown("### 🔍 Automatic Folder Monitoring")
                gr.Markdown("""
                **Monitor a folder for file changes and automatically sync with RAG system:**
                - 📁 **New files** → Automatically uploaded
                - 🔄 **Modified files** → Automatically updated
                - 🗑️ **Deleted files** → Automatically removed from vector store
                - ⏰ **Check interval**: Every 60 seconds
                """)
                
                with gr.Row():
                    with gr.Column(scale=2):
                        # Folder monitoring controls
                        monitor_folder_input = gr.Textbox(
                            label="📁 Folder Path to Monitor",
                            placeholder="e.g., C:\\Documents\\MyDocs or /home/user/documents",
                            info="Enter the full path to the folder you want to monitor. If already monitored, status will be confirmed."
                        )
                        
                        with gr.Row():
                            start_monitor_btn = gr.Button("🟢 Start/Resume Monitoring", variant="primary")
                            stop_monitor_btn = gr.Button("🛑 Stop Monitoring", variant="stop")
                            status_refresh_btn = gr.Button("🔄 Refresh Status", variant="secondary")
                        
                        gr.Markdown("""
                        **💡 How to use:**
                        1. **Enter folder path** (must exist and be accessible)
                        2. **Click "Start/Resume Monitoring"** (safe to click even if already monitored)
                        3. **Check status** to see if monitoring is active
                        4. **Add/modify files** in the folder to test auto-ingestion
                        """)
                        
                        monitor_result = gr.Markdown(
                            label="Monitoring Result",
                            value="📴 **Monitoring Status:** Ready to start monitoring. Enter a folder path above."
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📊 Monitoring Status")
                        
                        monitor_status_display = gr.Markdown(
                            label="Current Status",
                            value="📴 **Monitoring Status:** Inactive"
                        )
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### 🗂️ Manage Individual Folders")
                        
                        monitored_folders_display = gr.Markdown(
                            value="*Click 'Refresh Folders' to see monitored folders*",
                            visible=True
                        )
                        
                        with gr.Row():
                            refresh_folders_btn = gr.Button("🔄 Refresh Folders", variant="secondary", size="sm")
                            
                        folder_selector = gr.Dropdown(
                            label="Select Folder to Remove",
                            choices=[],
                            value=None,
                            interactive=True,
                            visible=False
                        )
                        
                        remove_folder_result = gr.Markdown(
                            value="",
                            visible=False
                        )
                        
                        with gr.Row():
                            remove_folder_btn = gr.Button("🗑️ Remove Selected Folder", variant="stop", size="sm", visible=False)
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### 📋 Supported File Types")
                        gr.Markdown("""
                        - 📄 **Text files**: .txt, .md
                        - 📊 **Data files**: .json, .csv
                        - 📖 **Documents**: .pdf, .docx, .doc
                        - 📊 **Excel files**: .xlsx, .xls, .xlsm, .xlsb
                        
                        #### 🔄 How It Works
                        1. **Start monitoring** a folder
                        2. **Add/modify/delete** files in that folder
                        3. **System automatically syncs** changes
                        4. **Check console** for real-time updates
                        5. **Query testing** to verify changes
                        
                        #### ⚠️ Important Notes
                        - Multiple folders can be monitored simultaneously
                        - Files are checked every 60 seconds
                        - Large files may take time to process
                        - Use "Manage Individual Folders" to remove specific folders
                        - Monitor console output for detailed logs
                         """)
            
            # Vector Store Diagnostics Tab
            with gr.Tab("🔍 Vector Diagnostics"):
                gr.Markdown("### 🔍 Vector Store Inspection & Diagnostics")
                gr.Markdown("""
                **Debug what's actually stored in your vector database:**
                - 📊 **Get Statistics**: See total vectors, documents, and chunks
                - 🔍 **Search Documents**: Find specific documents in vector store
                - 🔄 **Sync Registry**: Fix mismatches between UI and vector store
                - 🎯 **Troubleshoot**: Identify why queries return unexpected results
                """)
                
                with gr.Row():
                    with gr.Column(scale=2):
                        # Diagnostics controls
                        gr.Markdown("#### 📊 Vector Store Statistics")
                        get_stats_btn = gr.Button("📊 Get Vector Store Stats", variant="primary")
                        
                        gr.Markdown("#### 🔍 Search Documents")
                        with gr.Row():
                            search_term_input = gr.Textbox(
                                label="🔍 Search Term (Optional)",
                                placeholder="Enter search term to filter documents, or leave empty to see all",
                                scale=3
                            )
                            search_limit_slider = gr.Slider(
                                minimum=5,
                                maximum=50,
                                value=20,
                                step=5,
                                label="Max Results",
                                scale=1
                            )
                        
                        search_docs_btn = gr.Button("🔍 Search Vector Store", variant="secondary")
                        
                        gr.Markdown("#### 🔄 Registry Sync")
                        gr.Markdown("""
                        **⚠️ Use this if UI registry doesn't match vector store:**
                        - Clears UI registry and rebuilds from vector store
                        - Useful when documents were uploaded externally
                        - Fixes dropdown and registry display issues
                        """)
                        sync_registry_btn = gr.Button("🔄 Sync Registry with Vector Store", variant="stop")
                        
                        diagnostics_result = gr.Markdown(
                            label="Diagnostics Result",
                            value="Ready to inspect vector store..."
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🎯 Common Issues")
                        gr.Markdown("""
                        **🔍 Query returns results but UI shows no documents:**
                        - Documents uploaded externally (not via UI)
                        - Use "Sync Registry" to fix
                        
                        **📁 Folder monitoring not working:**
                        - Check console logs for errors
                        - Verify folder path is correct
                        - Ensure files are supported types
                        
                        **🗑️ Deleted documents still appear in queries:**
                        - Vector store deletion may have failed
                        - Use "Get Stats" to verify actual content
                        - Use "Clear Vector Store" if needed
                        
                        **📊 Registry count ≠ Vector store count:**
                        - UI registry out of sync
                        - Use "Sync Registry" to fix
                        
                        #### 🛠️ Troubleshooting Steps
                        1. **Get Stats** → See what's actually stored
                        2. **Search Documents** → Find specific content
                        3. **Sync Registry** → Fix UI display issues
                        4. **Test Query** → Verify results match expectations
                        """)
            
            # Heartbeat Monitor Tab
            with gr.Tab("💓 Heartbeat Monitor"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Heartbeat Control")
                        heartbeat_status_btn = gr.Button("📊 Get Status", variant="primary")
                        heartbeat_start_btn = gr.Button("▶️ Start Monitoring", variant="secondary")
                        heartbeat_stop_btn = gr.Button("⏹️ Stop Monitoring", variant="stop")

                        gr.Markdown("### Logs")
                        log_limit = gr.Slider(
                            minimum=5,
                            maximum=100,
                            value=20,
                            step=5,
                            label="Number of logs to show"
                        )
                        heartbeat_logs_btn = gr.Button("📋 View Logs", variant="secondary")

                    with gr.Column(scale=2):
                        heartbeat_output = gr.Markdown("Click 'Get Status' to see heartbeat monitoring status...")

            # ServiceNow Integration Tab
            with gr.Tab("🎫 ServiceNow"):
                gr.Markdown("## 🎫 ServiceNow Ticket Management")
                gr.Markdown("Browse, filter, and selectively ingest ServiceNow tickets into your RAG system")
                
                # Import ServiceNow UI components
                try:
                    import sys
                    import os
                    
                    # Get the current working directory and build paths
                    current_dir = os.getcwd()
                    rag_system_path = os.path.join(current_dir, 'rag_system')
                    rag_system_src = os.path.join(current_dir, 'rag_system', 'src')
                    
                    # Add paths to sys.path if not already there
                    if rag_system_path not in sys.path:
                        sys.path.insert(0, rag_system_path)
                    if rag_system_src not in sys.path:
                        sys.path.insert(0, rag_system_src)
                    
                    # Import the ServiceNow UI module
                    from src.api.servicenow_ui import ServiceNowUI
                    servicenow_ui = ServiceNowUI()
                    servicenow_available = True
                    print("[OK] ServiceNow UI imported and initialized successfully!")
                    
                except ImportError as e:
                    print(f"[ERROR] ServiceNow UI import failed: {e}")
                    print(f"   Current working directory: {os.getcwd()}")
                    print(f"   Looking for module at: {os.path.join(os.getcwd(), 'rag_system', 'src', 'api', 'servicenow_ui.py')}")
                    print(f"   File exists: {os.path.exists(os.path.join(os.getcwd(), 'rag_system', 'src', 'api', 'servicenow_ui.py'))}")
                    servicenow_available = False
                except Exception as e:
                    print(f"[ERROR] ServiceNow UI initialization failed: {e}")
                    servicenow_available = False
                
                if servicenow_available:
                    with gr.Tabs():
                        # Browse Tickets Tab
                        with gr.TabItem("📋 Browse Tickets"):
                            with gr.Row():
                                with gr.Column(scale=2):
                                    gr.Markdown("### 🔍 Filters")
                                    priority_filter = gr.Dropdown(
                                        choices=["All", "1", "2", "3", "4", "5"],
                                        value="All",
                                        label="Priority Filter",
                                        info="1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning"
                                    )
                                    state_filter = gr.Dropdown(
                                        choices=["All", "1", "2", "3", "6", "7"],
                                        value="All", 
                                        label="State Filter",
                                        info="1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed"
                                    )
                                    category_filter = gr.Dropdown(
                                        choices=["All", "network", "hardware", "software", "inquiry"],
                                        value="All",
                                        label="Category Filter"
                                    )
                                    
                                with gr.Column(scale=1):
                                    gr.Markdown("### 📄 Pagination")
                                    current_page = gr.Number(value=1, label="Page", precision=0, minimum=1)
                                    page_size = gr.Number(value=10, label="Items per page", precision=0, minimum=1, maximum=50)
                                    
                            fetch_btn = gr.Button("🔄 Fetch Tickets", variant="primary", size="lg")
                            
                            with gr.Row():
                                with gr.Column(scale=2):
                                    tickets_table = gr.Textbox(
                                        label="📋 ServiceNow Tickets",
                                        lines=15,
                                        max_lines=20,
                                        interactive=False,
                                        show_copy_button=True
                                    )
                                    
                                with gr.Column(scale=1):
                                    pagination_info = gr.Markdown("📄 Pagination info will appear here")
                        
                        # Select & Ingest Tab
                        with gr.TabItem("✅ Select & Ingest"):
                            gr.Markdown("### 🎯 Ticket Selection")
                            gr.Markdown("Select tickets from the list below or enter ticket IDs manually")
                            
                            ticket_checkboxes = gr.HTML(label="Select Tickets")
                            
                            with gr.Row():
                                selected_ids = gr.Textbox(
                                    label="Selected Ticket IDs (comma-separated)",
                                    placeholder="Enter ticket IDs manually or use checkboxes above",
                                    lines=2,
                                    info="Example: ticket_1,ticket_2,ticket_3"
                                )
                                
                            with gr.Row():
                                update_selection_btn = gr.Button("🔄 Update Selection", variant="secondary")
                                ingest_btn = gr.Button("🚀 Ingest Selected Tickets", variant="primary")
                            
                            selection_status = gr.Textbox(
                                label="Selection Status",
                                lines=2,
                                interactive=False
                            )
                            
                            ingestion_results = gr.Markdown("### 📊 Ingestion results will appear here")
                        
                        # Statistics Tab
                        with gr.TabItem("📊 Statistics"):
                            stats_btn = gr.Button("🔄 Refresh Stats", variant="secondary")
                            stats_display = gr.Markdown("### 📈 Statistics will appear here")
                    
                    # Event handlers for ServiceNow
                    if servicenow_available:
                        fetch_btn.click(
                            fn=servicenow_ui.fetch_servicenow_tickets,
                            inputs=[current_page, page_size, priority_filter, state_filter, category_filter],
                            outputs=[tickets_table, ticket_checkboxes, pagination_info]
                        )
                        
                        update_selection_btn.click(
                            fn=servicenow_ui.update_ticket_selection,
                            inputs=[selected_ids],
                            outputs=[selection_status]
                        )
                        
                        ingest_btn.click(
                            fn=servicenow_ui.ingest_selected_tickets,
                            inputs=[],
                            outputs=[ingestion_results]
                        )
                        
                        stats_btn.click(
                            fn=servicenow_ui.get_servicenow_stats,
                            inputs=[],
                            outputs=[stats_display]
                        )
                else:
                    gr.Markdown("## ServiceNow Integration Not Available")
                    gr.Markdown("""
                    The ServiceNow integration module is not available. This could be due to:
                    
                    - Missing ServiceNow UI module
                    - Import errors in the ServiceNow components
                    - Missing dependencies
                    
                    To enable ServiceNow integration:
                    1. Ensure the ServiceNow UI module is properly installed in rag_system/src/api/
                    2. Check that all dependencies are available
                    3. Restart the application
                                        """)

            # Conversation Chat Tab
            with gr.Tab("💬 Conversation Chat"):
                gr.Markdown("### 🤖 Enhanced Conversational Chat with Smart Suggestions")
                gr.Markdown("""
                **Engage in intelligent conversations with your RAG system:**
                - 🧠 **Multi-turn conversations** with context retention
                - 🔍 **Knowledge-based responses** using your document database
                - 💡 **Smart follow-up suggestions** with one-click responses
                - 🎯 **Topic exploration** with interactive chips
                - 📊 **Conversation analytics** and session management
                - ⚡ **Quick actions** and contextual hints
                """)
                
                with gr.Row():
                    with gr.Column(scale=2):
                        # Main conversation area
                        chatbot = gr.Chatbot(
                            label="💬 Conversation",
                            height=400,
                            show_label=True,
                            container=True,
                            type="messages",
                            show_copy_button=True
                        )
                        
                        # Message input area
                        with gr.Row():
                            message_input = gr.Textbox(
                                placeholder="Type your message here... Press Enter to send",
                                label="Your Message",
                                lines=2,
                                scale=4,
                                show_copy_button=False
                            )
                            send_button = gr.Button("📤 Send", variant="primary", scale=1)
                        
                        # Enhanced suggestion area
                        with gr.Group():
                            gr.Markdown("### 💡 Smart Suggestions")
                            
                            # Quick suggestion buttons
                            with gr.Row():
                                suggestion_btn_1 = gr.Button("", variant="secondary", visible=False, scale=1)
                                suggestion_btn_2 = gr.Button("", variant="secondary", visible=False, scale=1)
                                suggestion_btn_3 = gr.Button("", variant="secondary", visible=False, scale=1)
                                suggestion_btn_4 = gr.Button("", variant="secondary", visible=False, scale=1)
                            
                            # Topic exploration chips
                            with gr.Row():
                                gr.Markdown("**🔍 Explore Topics:**")
                            
                            with gr.Row():
                                topic_chip_1 = gr.Button("", variant="outline", visible=False, size="sm")
                                topic_chip_2 = gr.Button("", variant="outline", visible=False, size="sm")
                                topic_chip_3 = gr.Button("", variant="outline", visible=False, size="sm")
                                topic_chip_4 = gr.Button("", variant="outline", visible=False, size="sm")
                                topic_chip_5 = gr.Button("", variant="outline", visible=False, size="sm")
                                topic_chip_6 = gr.Button("", variant="outline", visible=False, size="sm")
                        
                        # Conversation controls
                        with gr.Row():
                            start_conversation_btn = gr.Button("🆕 Start New Conversation", variant="primary")
                            end_conversation_btn = gr.Button("🔚 End Conversation", variant="stop")
                            clear_suggestions_btn = gr.Button("🧹 Clear Suggestions", variant="secondary", size="sm")
                    
                    with gr.Column(scale=1):
                        # Enhanced session information
                        with gr.Group():
                            gr.Markdown("#### ℹ️ Thread Info")
                            
                            thread_id_display = gr.Textbox(
                                label="Thread ID",
                                value="No thread",
                                interactive=False,
                                max_lines=1
                            )
                            
                            conversation_status = gr.Markdown(
                                label="Conversation Status",
                                value="No active conversation"
                            )
                            
                            # Conversation insights
                            conversation_insights = gr.Markdown(
                                label="💡 Conversation Insights",
                                value="",
                                visible=False
                            )
                        
                        # Interactive hints and guidance
                        with gr.Group():
                            gr.Markdown("#### 🎯 Interactive Hints")
                            
                            interaction_hints = gr.Markdown(
                                label="Current Hints",
                                value="💡 Start a conversation to see personalized hints and suggestions!"
                            )
                            
                            # Entity exploration
                            entity_exploration = gr.Markdown(
                                label="👥 Entities to Explore",
                                value="",
                                visible=False
                            )
                            
                            # Technical terms
                            technical_terms = gr.Markdown(
                                label="🔧 Technical Terms",
                                value="",
                                visible=False
                            )
                        
                        # Enhanced how-to guide
                        with gr.Group():
                            gr.Markdown("#### 🚀 Enhanced Features")
                            gr.Markdown("""
                                **Smart Suggestions:**
                                - 💡 **One-click questions**: Generated based on context
                                - ⚡ **Quick responses**: Pre-computed answers for common follow-ups
                                - 🎯 **Prioritized suggestions**: Most relevant questions first
                                - 🔍 **Context-aware**: Suggestions adapt to conversation flow
                                
                                **Topic Exploration:**
                                - 🏷️ **Topic chips**: Click to explore related areas
                                - 👥 **Entity cards**: Discover people, places, products
                                - 🔧 **Technical terms**: Get definitions and explanations
                                - 📊 **Related areas**: Find connected topics
                                
                                **Conversation Intelligence:**
                                - 📈 **Conversation health**: Real-time quality assessment
                                - 🎯 **Exploration paths**: Suggested conversation directions
                                - 💬 **Context retention**: Maintains conversation memory
                                - 📊 **Turn analytics**: Track conversation depth and coverage
                                """)
                        
                        # Advanced tips
                        with gr.Group():
                            gr.Markdown("#### 💡 Pro Tips")
                            gr.Markdown("""
                                **Getting Better Suggestions:**
                                - Ask specific questions about your documents
                                - Use natural, conversational language
                                - Build on previous responses for deeper insights
                                - Click suggestion buttons for instant follow-ups
                                
                                **Topic Exploration:**
                                - Click topic chips to dive deeper
                                - Explore entities mentioned in responses
                                - Ask about technical terms for definitions
                                - Follow suggested exploration paths
                                
                                **Conversation Flow:**
                                - Start with broad questions, then get specific
                                - Use clarification suggestions when confused
                                - Explore related topics for comprehensive understanding
                                - End conversations when you have what you need
                                """)
                        
                        # Debug information (collapsible)
                        with gr.Accordion("🔧 Debug Info", open=False):
                            debug_info = gr.JSON(
                                label="Last Response Data",
                                value={},
                                visible=True
                            )

            # Help Tab
            with gr.Tab("❓ Help"):
                gr.Markdown("""
                # 📖 Fixed Document Lifecycle Guide

                ## 🔧 What's Fixed

                ### ❌ **Old Problems:**
                - Confusing two-step process (upload then update)
                - Dropdowns not refreshing automatically
                - Unclear when document was updated vs new
                - Manual refresh required

                ### ✅ **New Solutions:**
                - **Single Interface**: Upload and update use the same form
                - **Smart Detection**: System automatically detects if path exists
                - **Auto-Refresh**: Dropdowns update immediately after operations
                - **Clear Status**: Shows exactly what happened (new vs update)
                - **Upload Counter**: Track how many times document was updated

                ## 🚀 Improved Workflow

                ### 1. **Upload/Update Document**
                ```
                📝 Select File: my-document.txt
                📄 Document Path: /docs/my-guide (optional)
                📤 Click "Upload/Update Document"

                Result:
                - First time: "Document Uploaded Successfully!"
                - Same path: "Document Updated Successfully!"
                ```

                ### 2. **Test Query**
                ```
                🔍 Query: "content from my document"
                Result: Should show content from uploaded file
                ```

                ### 3. **Update Same Document**
                ```
                📝 Select File: my-updated-document.txt
                📄 Document Path: /docs/my-guide (same path)
                📤 Click "Upload/Update Document"

                Result: "Document Updated Successfully!"
                Upload Count: 2
                ```

                ### 4. **Test Query Again**
                ```
                🔍 Query: "content from my document"
                Result: Should show NEW content from updated file
                ```

                ### 5. **Delete Document (Two Ways)**
                ```
                Method 1 - Document Management Tab:
                🗑️ Select from dropdown: /docs/my-guide
                🗑️ Click "Delete Document"

                Method 2 - Document Overview Tab:
                📄 Click "Refresh Documents" to see all documents
                🗑️ Select document from "Select Document to Delete" dropdown
                🗑️ Click "Delete Selected Document"

                Result: Document vectors permanently deleted from vector store
                ```

                ### 6. **ServiceNow Integration (NEW!)**
                ```
                🎫 Go to "ServiceNow" tab
                📋 Browse Tickets: View and filter ServiceNow tickets
                ✅ Select & Ingest: Choose specific tickets to add to RAG system
                📊 Statistics: Monitor ServiceNow integration health

                Features:
                - Pagination support (1-50 tickets per page)
                - Priority filtering (1=Critical to 5=Planning)
                - State filtering (New, In Progress, Resolved, etc.)
                - Category filtering (network, hardware, software, inquiry)
                - Batch ingestion of selected tickets
                - Integration with existing RAG system
                ```

                ### 7. **View Document Overview**
                ```
                📄 Go to "Document Overview" tab
                📄 Click "Refresh Documents"

                Result: See all documents with:
                - Document paths and chunk counts
                - File sizes and last updated timestamps
                - Source information (UI upload, folder monitor, ServiceNow, etc.)
                - Vector store statistics
                ```

                ### 8. **Clear Vector Store (DANGER ZONE)**
                ```
                🧹 Click "Clear All Vectors & Documents"

                Result: ALL documents and vectors permanently deleted
                Registry cleared, system reset to empty state
                ```

                ## 🎯 Key Features

                ### **Smart Upload/Update**
                - Same interface handles both operations
                - Automatically detects if document path exists
                - Clear messaging about what happened

                ### **Auto-Refresh Dropdowns**
                - Delete dropdown updates immediately after upload
                - No manual refresh needed
                - Only shows active documents (not deleted)

                ### **ServiceNow Integration**
                - Browse and filter ServiceNow tickets
                - Selective ingestion into RAG system
                - Maintains ticket metadata for searchability
                - Works with sample data when ServiceNow unavailable

                ### **Upload Counter**
                - Track how many times document was updated
                - Helps understand document history
                - Shows in registry and operation results

                ### **Better Status Messages**
                - Clear indication of new vs update
                - Shows old vectors deleted count
                - Explains what "No old vectors found" means

                ### **Clear Vector Store**
                - **⚠️ DANGER ZONE**: Permanently deletes ALL data
                - Removes all documents, chunks, and vectors
                - Resets system to completely empty state
                - Useful for testing and cleanup
                - Cannot be undone - use with caution

                ## 🔍 Testing the Lifecycle

                ### **Test Document Updates**
                1. Upload file with content "Version 1"
                2. Query for that content → should find it
                3. Upload different file with same path, content "Version 2"
                4. Query again → should find "Version 2", not "Version 1"

                ### **Test Document Deletion**
                1. Upload a document
                2. Query for its content → should find it
                3. Delete the document
                4. Query again → should not find it or show deletion marker

                ### **Test ServiceNow Integration**
                1. Go to "🎫 ServiceNow" tab
                2. Click "🔄 Fetch Tickets" to see available tickets
                3. Use filters to narrow down tickets
                4. Go to "✅ Select & Ingest" tab
                5. Select tickets using checkboxes or manual entry
                6. Click "🚀 Ingest Selected Tickets"
                7. Test queries to find ServiceNow ticket content

                ### **Test Vector Store Clear**
                1. Upload multiple documents
                2. Query to verify they exist
                3. Click "Clear All Vectors & Documents"
                4. Check registry → should be empty
                5. Query again → should find no results

                ### **Test Folder Monitoring**
                1. Go to "📁 Folder Monitor" tab
                2. Enter a folder path (e.g., C:\\Documents\\TestFolder)
                3. Click "🟢 Start Monitoring"
                4. Add a .txt file to that folder → should auto-upload
                5. Modify the file → should auto-update
                6. Delete the file → should auto-delete from vector store

                ### **Test Conversation System**
                1. Go to "💬 Conversation Chat" tab
                2. Click "🆕 Start New Conversation"
                3. Type a message and press Enter or click Send
                4. Have a multi-turn conversation with context retention
                5. Click "🔚 End Conversation" when finished
                7. Check console output for real-time monitoring logs

                ## 💡 Pro Tips

                1. **Use Descriptive Paths**: `/docs/ai-guide`, `/manuals/setup`, `/servicenow/incidents`, etc.
                2. **Test Immediately**: Query after each operation to see effects
                3. **Watch Upload Count**: See how many times document was updated
                4. **Check Registry**: Monitor document status and file sizes
                5. **Use Different Content**: Make files easily distinguishable for testing
                6. **ServiceNow Integration**: Use filters to find relevant tickets before ingesting
                7. **Folder Monitoring**: Use absolute paths, monitor console for real-time logs
                                        8. **File Types**: Stick to supported formats (.txt, .md, .pdf, .docx, .doc, .json, .csv, .xlsx, .xls, .xlsm, .xlsb)

                ---

                **🎯 This fixed interface provides a much better user experience for document lifecycle management with ServiceNow integration!**
                """)

        # Event Handlers
        
        # Connection status
        refresh_connection_btn.click(
            fn=ui.check_api_connection,
            outputs=[connection_status]
        )
        
        # Main upload/update operation
        def upload_and_refresh(file, doc_path):
            print(f"DEBUG: upload_and_refresh called with file: {file}, doc_path: {doc_path}")
            result, registry, dropdown_choices = ui.upload_and_refresh(file, doc_path)
            print(f"DEBUG: Upload result: {result[:100]}...")
            print(f"DEBUG: Dropdown choices: {dropdown_choices}")
            print(f"DEBUG: Dropdown choices type: {type(dropdown_choices)}")
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            # Ensure all choices are strings
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            print(f"DEBUG: Safe dropdown choices: {safe_choices}")
            return result, registry, gr.update(choices=safe_choices, value=None)
        
        upload_btn.click(
            fn=upload_and_refresh,
            inputs=[file_input, doc_path_input],
            outputs=[operation_result, document_registry_display, delete_doc_path_input]
        )
        
        # Delete operation
        def delete_and_refresh(doc_path):
            print(f"DEBUG: delete_and_refresh called with doc_path: {doc_path}")
            result, registry, dropdown_choices = ui.delete_document(doc_path)
            print(f"DEBUG: Delete result: {result[:100]}...")
            print(f"DEBUG: Dropdown choices after delete: {dropdown_choices}")
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            # Ensure all choices are strings
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            print(f"DEBUG: Safe dropdown choices after delete: {safe_choices}")
            return result, registry, gr.update(choices=safe_choices, value=None)
        
        delete_doc_btn.click(
            fn=delete_and_refresh,
            inputs=[delete_doc_path_input],
            outputs=[operation_result, document_registry_display, delete_doc_path_input]
        )
        
        # Registry refresh
        def refresh_registry_and_dropdown():
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            # Ensure all choices are strings
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return registry, gr.update(choices=safe_choices, value=None)
        
        refresh_registry_btn.click(
            fn=refresh_registry_and_dropdown,
            outputs=[document_registry_display, delete_doc_path_input]
        )
        
        # Clear vector store operation
        def clear_vector_store_and_refresh():
            result = ui.clear_vector_store()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            # Ensure all choices are strings
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return result, registry, gr.update(choices=safe_choices, value=None)
        
        clear_vector_store_btn.click(
            fn=clear_vector_store_and_refresh,
            outputs=[operation_result, document_registry_display, delete_doc_path_input]
        )
        
        # Query testing
        test_query_btn.click(
            fn=ui.test_query,
            inputs=[test_query_input, max_results_slider],
            outputs=[query_answer, query_sources, query_lifecycle_analysis]
        )
        
        # Feedback event handlers
        def submit_helpful_feedback(feedback_text):
            result = ui.submit_feedback(helpful=True, feedback_text=feedback_text)
            return gr.update(visible=True, value=result), ""  # Clear feedback text after submission
        
        def submit_not_helpful_feedback(feedback_text):
            result = ui.submit_feedback(helpful=False, feedback_text=feedback_text)
            return gr.update(visible=True, value=result), ""  # Clear feedback text after submission
        
        feedback_helpful_btn.click(
            fn=submit_helpful_feedback,
            inputs=[feedback_text_input],
            outputs=[feedback_result, feedback_text_input]
        )
        
        feedback_not_helpful_btn.click(
            fn=submit_not_helpful_feedback,
            inputs=[feedback_text_input],
            outputs=[feedback_result, feedback_text_input]
        )
        
        get_feedback_stats_btn.click(
            fn=ui.get_feedback_stats,
            outputs=[feedback_stats_display]
        )
        
        # Folder monitoring event handlers
        def start_monitoring_and_refresh(folder_path):
            # Validate input before proceeding
            if not folder_path or not folder_path.strip():
                return (
                    "❌ **Please enter a folder path**\n\nExample: `C:\\Documents\\MyFolder` or `/home/user/documents`",
                    ui.get_monitoring_status(),
                    ui._format_document_registry(),
                    gr.update(choices=ui.get_document_paths(), value=None)
                )
            
            result = ui.start_folder_monitoring(folder_path)
            status = ui.get_monitoring_status()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return result, status, registry, gr.update(choices=safe_choices, value=None)
        
        def stop_monitoring_and_refresh():
            result = ui.stop_folder_monitoring()
            status = ui.get_monitoring_status()
            return result, status
        
        def refresh_monitoring_status():
            status = ui.get_monitoring_status()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return status, registry, gr.update(choices=safe_choices, value=None)
        
        start_monitor_btn.click(
            fn=start_monitoring_and_refresh,
            inputs=[monitor_folder_input],
            outputs=[monitor_result, monitor_status_display, document_registry_display, delete_doc_path_input]
        )
        
        stop_monitor_btn.click(
            fn=stop_monitoring_and_refresh,
            outputs=[monitor_result, monitor_status_display]
        )
        
        status_refresh_btn.click(
            fn=refresh_monitoring_status,
            outputs=[monitor_status_display, document_registry_display, delete_doc_path_input]
        )
        
        # Individual folder management event handlers
        def refresh_folders_and_display():
            display_text, folder_list = ui.get_monitored_folders()
            if folder_list:
                return (
                    display_text,
                    gr.update(choices=folder_list, value=None, visible=True),
                    gr.update(visible=True),
                    gr.update(visible=False, value="")
                )
            else:
                return (
                    display_text,
                    gr.update(choices=[], value=None, visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False, value="")
                )
        
        def remove_folder_and_refresh(selected_folder):
            if not selected_folder:
                return (
                    "❌ Please select a folder to remove",
                    ui._format_document_registry(),
                    gr.update(choices=ui.get_document_paths(), value=None),
                    ui.get_monitoring_status()
                )
            
            # Remove the folder
            result = ui.remove_folder_monitoring(selected_folder)
            
            # Refresh displays
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            monitoring_status = ui.get_monitoring_status()
            
            # Refresh folder list
            display_text, folder_list = ui.get_monitored_folders()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return (
                result,
                registry,
                gr.update(choices=safe_choices, value=None),
                monitoring_status,
                display_text,
                gr.update(choices=folder_list, value=None, visible=len(folder_list) > 0)
            )
        
        refresh_folders_btn.click(
            fn=refresh_folders_and_display,
            outputs=[monitored_folders_display, folder_selector, remove_folder_btn, remove_folder_result]
        )
        
        remove_folder_btn.click(
            fn=remove_folder_and_refresh,
            inputs=[folder_selector],
            outputs=[remove_folder_result, document_registry_display, delete_doc_path_input, monitor_status_display, monitored_folders_display, folder_selector]
        )
        
        # Vector diagnostics event handlers
        def get_stats_and_refresh():
            stats = ui.get_vector_store_stats()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return stats, registry, gr.update(choices=safe_choices, value=None)
        
        def search_docs_and_refresh(search_term, limit):
            search_result = ui.search_vector_store(search_term, limit)
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return search_result, registry, gr.update(choices=safe_choices, value=None)
        
        def sync_registry_and_refresh():
            sync_result = ui.sync_registry_with_vector_store()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return sync_result, registry, gr.update(choices=safe_choices, value=None)
        
        get_stats_btn.click(
            fn=get_stats_and_refresh,
            outputs=[diagnostics_result, document_registry_display, delete_doc_path_input]
        )
        
        search_docs_btn.click(
            fn=search_docs_and_refresh,
            inputs=[search_term_input, search_limit_slider],
            outputs=[diagnostics_result, document_registry_display, delete_doc_path_input]
        )
        
        sync_registry_btn.click(
            fn=sync_registry_and_refresh,
            outputs=[diagnostics_result, document_registry_display, delete_doc_path_input]
        )
        
        # Document overview event handlers
        def refresh_documents_and_display():
            try:
                documents_info = ui.get_documents_in_vector_store()
                # Also refresh the delete dropdown
                dropdown_choices = ui.get_document_paths_from_overview()
                return documents_info, gr.update(choices=dropdown_choices, value=None), gr.update(visible=False, value="")
            except Exception as e:
                return f"❌ **Error getting documents:** {str(e)}", gr.update(choices=["Error loading documents"], value=None), gr.update(visible=False, value="")
        
        def delete_document_from_overview_and_refresh(document_selection):
            try:
                # Perform the deletion
                delete_result = ui.delete_document_from_overview(document_selection)
                
                # Refresh the documents display
                documents_info = ui.get_documents_in_vector_store()
                
                # Refresh the delete dropdown
                dropdown_choices = ui.get_document_paths_from_overview()
                
                return (
                    documents_info,
                    gr.update(choices=dropdown_choices, value=None),
                    gr.update(visible=True, value=delete_result)
                )
            except Exception as e:
                error_msg = f"❌ **Error during deletion:** {str(e)}"
                return (
                    "❌ Error refreshing documents after deletion",
                    gr.update(choices=["Error loading documents"], value=None),
                    gr.update(visible=True, value=error_msg)
                )
        
        refresh_documents_btn.click(
            fn=refresh_documents_and_display,
            outputs=[documents_display, document_selection_dropdown, delete_result_display]
        )
        
        delete_document_btn.click(
            fn=delete_document_from_overview_and_refresh,
            inputs=[document_selection_dropdown],
            outputs=[documents_display, document_selection_dropdown, delete_result_display]
        )
        
        # Heartbeat monitoring event handlers
        heartbeat_status_btn.click(
            fn=ui.get_heartbeat_status,
            outputs=heartbeat_output
        )
        
        heartbeat_start_btn.click(
            fn=ui.start_heartbeat,
            outputs=heartbeat_output
        )
        
        heartbeat_stop_btn.click(
            fn=ui.stop_heartbeat,
            outputs=heartbeat_output
        )
        
        heartbeat_logs_btn.click(
            fn=ui.get_heartbeat_logs,
            inputs=log_limit,
            outputs=heartbeat_output
        )
        
        # Enhanced conversation event handlers
        def start_conversation_and_update():
            """Start a new conversation and update UI"""
            history, thread_id, status = ui.start_new_conversation()
            conversation_status_text = ui.get_conversation_status(thread_id)
            
            # Clear all suggestion elements
            suggestion_updates = [
                gr.update(value="", visible=False) for _ in range(4)  # suggestion buttons
            ]
            topic_updates = [
                gr.update(value="", visible=False) for _ in range(6)  # topic chips
            ]
            
            return (
                history, thread_id, status, conversation_status_text,
                "💡 Start a conversation to see personalized hints and suggestions!",
                "", "", "",  # Clear insights, entity exploration, technical terms
                {}  # Clear debug info
            ) + tuple(suggestion_updates) + tuple(topic_updates)
        
        def send_message_and_update(message, thread_id, history):
            """Send message and update conversation with enhanced suggestions"""
            try:
                message_cleared, updated_history, status, enhanced_data = ui.send_conversation_message(message, thread_id, history)
            except Exception as e:
                # Fallback when conversation API is not available
                updated_history = history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "🚧 Conversation API not available. Please use the Query Testing tab for Q&A functionality."}
                ]
                enhanced_data = {
                    'suggestions': [],
                    'topics': [],
                    'entities': [],
                    'technical_terms': [],
                    'insights': {},
                    'hints': ['💡 Use the Query Testing tab for document Q&A functionality']
                }
                message_cleared = ""
                status = f"❌ Conversation API error: {str(e)}"
            
            conversation_status_text = ui.get_conversation_status(thread_id)
            
            # Update suggestion buttons with error handling
            suggestions = enhanced_data.get('suggestions', [])
            suggestion_updates = []
            for i in range(4):
                if i < len(suggestions):
                    suggestion = suggestions[i]
                    if isinstance(suggestion, dict):
                        icon = suggestion.get('icon', '💬')
                        text = suggestion.get('question', suggestion.get('text', ''))
                        # Increase character limit and make truncation smarter
                        if len(text) > 120:
                            # Try to truncate at word boundary
                            truncated = text[:120]
                            last_space = truncated.rfind(' ')
                            if last_space > 80:  # Only truncate at word if it's not too short
                                text = truncated[:last_space] + "..."
                            else:
                                text = truncated + "..."
                        button_text = f"{icon} {text}" if text else ""
                    else:
                        # Handle case where suggestion is a string
                        text = str(suggestion)
                        if len(text) > 120:
                            # Try to truncate at word boundary
                            truncated = text[:120]
                            last_space = truncated.rfind(' ')
                            if last_space > 80:  # Only truncate at word if it's not too short
                                text = truncated[:last_space] + "..."
                            else:
                                text = truncated + "..."
                        button_text = f"💬 {text}" if text else ""
                    
                    if button_text.strip():
                        suggestion_updates.append(gr.update(value=button_text, visible=True))
                    else:
                        suggestion_updates.append(gr.update(value="", visible=False))
                else:
                    suggestion_updates.append(gr.update(value="", visible=False))
            
            # Update topic chips with error handling
            topics = enhanced_data.get('topics', [])
            topic_updates = []
            for i in range(6):
                if i < len(topics):
                    topic = topics[i] if isinstance(topics[i], str) else str(topics[i])
                    if topic.strip():
                        topic_updates.append(gr.update(value=f"🔍 {topic}", visible=True))
                    else:
                        topic_updates.append(gr.update(value="", visible=False))
                else:
                    topic_updates.append(gr.update(value="", visible=False))
            
            # Format interaction hints
            hints = enhanced_data.get('hints', [])
            hints_text = "\n".join([f"• {hint}" for hint in hints]) if hints else "💡 Continue the conversation for more suggestions!"
            
            # Format conversation insights
            insights = enhanced_data.get('insights', {})
            insights_text = ""
            if insights:
                coverage = insights.get('information_coverage', 'unknown')
                continuity = insights.get('topic_continuity', 0)
                insights_text = f"📊 **Coverage:** {coverage} | **Continuity:** {continuity:.1f}"
                
                exploration_path = insights.get('exploration_path', [])
                if exploration_path:
                    insights_text += f"\n\n**Suggested Path:**\n"
                    insights_text += "\n".join([f"• {step}" for step in exploration_path[:3]])
            
            # Format entities
            entities = enhanced_data.get('entities', [])
            entities_text = ""
            if entities:
                entities_text = "**Mentioned Entities:**\n"
                for entity in entities[:4]:
                    if isinstance(entity, dict):
                        name = entity.get('name', 'Unknown')
                        entity_type = entity.get('type', 'unknown')
                        entities_text += f"• {name} ({entity_type})\n"
                    else:
                        entities_text += f"• {entity}\n"
            
            # Format technical terms
            terms = enhanced_data.get('technical_terms', [])
            terms_text = ""
            if terms:
                terms_text = "**Technical Terms:**\n"
                for term in terms[:3]:
                    if isinstance(term, dict):
                        term_name = term.get('term', 'Unknown')
                        difficulty = term.get('difficulty', 'medium')
                        terms_text += f"• {term_name} ({difficulty})\n"
                    else:
                        terms_text += f"• {term}\n"
            
            return (
                message_cleared, updated_history, status, conversation_status_text,
                hints_text,
                insights_text if insights_text else "",
                entities_text if entities_text else "",
                terms_text if terms_text else "",
                enhanced_data  # Debug info
            ) + tuple(suggestion_updates) + tuple(topic_updates)
        
        def end_conversation_and_update(thread_id):
            """End conversation and update UI"""
            end_history, cleared_thread, status = ui.end_conversation(thread_id)
            
            # Clear all UI elements
            suggestion_updates = [
                gr.update(value="", visible=False) for _ in range(4)
            ]
            topic_updates = [
                gr.update(value="", visible=False) for _ in range(6)
            ]
            
            return (
                end_history, cleared_thread, status, "No active conversation",
                "💡 Start a new conversation to see suggestions!",
                "", "", "",  # Clear insights, entities, terms
                {}  # Clear debug info
            ) + tuple(suggestion_updates) + tuple(topic_updates)
        
        def handle_suggestion_click(suggestion_text, thread_id, history):
            """Handle suggestion button click"""
            if not suggestion_text or not suggestion_text.strip():
                return "", history, "No suggestion selected", {}
            
            # Extract the actual question from the button text (remove emoji and handle truncation)
            clean_question = suggestion_text.split(" ", 1)[1] if " " in suggestion_text else suggestion_text
            # Remove trailing "..." if present from truncation
            if clean_question.endswith("..."):
                clean_question = clean_question[:-3].strip()
            
            # Send the suggestion as a message and get the full response
            try:
                full_response = send_message_and_update(clean_question, thread_id, history)
                # Extract only the first 4 values that match our outputs
                message_cleared = full_response[0]
                updated_history = full_response[1] 
                status = full_response[2]
                debug_data = full_response[8] if len(full_response) > 8 else {}
                
                # Ensure debug_data is JSON serializable
                if not isinstance(debug_data, (dict, list, str, int, float, bool, type(None))):
                    debug_data = str(debug_data)
                
                return message_cleared, updated_history, status, debug_data
            except Exception as e:
                return "", history, f"Error: {str(e)}", {"error": str(e)}
        
        def handle_topic_click(topic_text, thread_id, history):
            """Handle topic chip click"""
            if not topic_text or not topic_text.strip():
                return "", history, "No topic selected", {}
            
            # Extract topic name and create a question
            topic_name = topic_text.replace("🔍 ", "")
            question = f"Tell me more about {topic_name}"
            
            # Send the topic exploration question and get the full response
            try:
                full_response = send_message_and_update(question, thread_id, history)
                # Extract only the first 4 values that match our outputs
                message_cleared = full_response[0]
                updated_history = full_response[1]
                status = full_response[2] 
                debug_data = full_response[8] if len(full_response) > 8 else {}
                
                # Ensure debug_data is JSON serializable
                if not isinstance(debug_data, (dict, list, str, int, float, bool, type(None))):
                    debug_data = str(debug_data)
                
                return message_cleared, updated_history, status, debug_data
            except Exception as e:
                return "", history, f"Error: {str(e)}", {"error": str(e)}
        
        def clear_suggestions():
            """Clear all suggestions and reset UI"""
            suggestion_updates = [
                gr.update(value="", visible=False) for _ in range(4)
            ]
            topic_updates = [
                gr.update(value="", visible=False) for _ in range(6)
            ]
            
            return (
                "💡 Suggestions cleared. Continue the conversation for new suggestions!",
                "", "", "",  # Clear insights, entities, terms
                {}  # Clear debug info
            ) + tuple(suggestion_updates) + tuple(topic_updates)
        
        # Enhanced conversation tab event handlers
        start_conversation_btn.click(
            fn=start_conversation_and_update,
            outputs=[
                chatbot, thread_id_display, conversation_status, conversation_status,
                interaction_hints, conversation_insights, entity_exploration, technical_terms,
                debug_info,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
        )
        
        send_button.click(
            fn=send_message_and_update,
            inputs=[message_input, thread_id_display, chatbot],
            outputs=[
                message_input, chatbot, conversation_status, conversation_status,
                interaction_hints, conversation_insights, entity_exploration, technical_terms,
                debug_info,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
        )
        
        message_input.submit(
            fn=send_message_and_update,
            inputs=[message_input, thread_id_display, chatbot],
            outputs=[
                message_input, chatbot, conversation_status, conversation_status,
                interaction_hints, conversation_insights, entity_exploration, technical_terms,
                debug_info,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
        )
        
        end_conversation_btn.click(
            fn=end_conversation_and_update,
            inputs=[thread_id_display],
            outputs=[
                chatbot, thread_id_display, conversation_status, conversation_status,
                interaction_hints, conversation_insights, entity_exploration, technical_terms,
                debug_info,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
        )
        
        clear_suggestions_btn.click(
            fn=clear_suggestions,
            outputs=[
                interaction_hints, conversation_insights, entity_exploration, technical_terms,
                debug_info,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
        )
        
        # Suggestion button click handlers
        for i, btn in enumerate([suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4]):
            btn.click(
                fn=handle_suggestion_click,
                inputs=[btn, thread_id_display, chatbot],
                outputs=[
                    message_input, chatbot, conversation_status, debug_info
                ]
            )
        
        # Topic chip click handlers
        for i, chip in enumerate([topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6]):
            chip.click(
                fn=handle_topic_click,
                inputs=[chip, thread_id_display, chatbot],
                outputs=[
                    message_input, chatbot, conversation_status, debug_info
                ]
            )

        # Initialize connection status on load
        interface.load(
            fn=ui.check_api_connection,
            outputs=[connection_status]
        )
    
    return interface

def check_server_status(api_url: str = "http://localhost:8000", max_retries: int = 3) -> bool:
    """Check if the server is running"""
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Server is running and healthy!")
                return True
            else:
                print(f"❌ Attempt {attempt + 1}/{max_retries}: Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt + 1}/{max_retries}: Server not responding - {e}")
        
        if attempt < max_retries - 1:
            print("⏳ Waiting 2 seconds before retry...")
            time.sleep(2)
    
    return False

def main():
    """Main function to launch the fixed UI"""
    print("DEBUG: Starting main() function")
    
    # Check server status
    print("DEBUG: Checking server status...")
    if not check_server_status():
        print("❌ Cannot connect to RAG server. Please ensure the server is running on http://localhost:8000")
        print("   Start the server with: python main.py")
        return
    
    print("DEBUG: Server is running, proceeding with UI creation...")
    
    # Create and launch interface
    print("🎛️ Creating fixed interface...")
    print("DEBUG: About to call create_fixed_interface()")
    interface = create_fixed_interface()
    print("DEBUG: Interface created successfully")
    
    print("""
🌟 FIXED DOCUMENT LIFECYCLE MANAGEMENT UI
==================================================
🌐 API Server: http://localhost:8000
🎛️ Fixed UI: http://localhost:7869
📁 Key Improvements:
  ✅ Smart Upload/Update (single interface)
  ✅ Auto-refresh dropdowns
  ✅ Clear status messages
  ✅ Upload counter tracking
  ✅ Better user experience
💬 UPDATED: Enhanced Conversational Chat with LangGraph State Persistence
  ✅ Multi-turn conversations with persistent state
  ✅ Thread-based conversation management
  ✅ Smart suggestion buttons
  ✅ Interactive topic exploration
  ✅ Real-time conversation insights
  ✅ LangGraph state checkpointer integration
🎯 Test the improved Upload → Update → Delete → Query → Chat workflow!
   No more confusion about upload vs update!
Ready to launch! Press Ctrl+C to stop the UI
==================================================
""")
    
    print("DEBUG: About to launch interface on port 7869")
    try:
        # Try with specific port first
        interface.launch(
            server_port=7869,
            share=False,
            show_error=True,
            inbrowser=True,
            prevent_thread_lock=False
        )
    except ValueError as ve:
        print(f"❌ ValueError on port 7869: {ve}")
        print("🔄 Trying with auto port selection...")
        try:
            interface.launch(
                share=False,
                show_error=True,
                inbrowser=True,
                prevent_thread_lock=False
            )
        except Exception as e2:
            print(f"❌ Auto port launch failed: {e2}")
            print("🔧 Trying minimal launch configuration...")
            try:
                interface.launch(
                    show_error=True
                )
            except Exception as e3:
                print(f"❌ All launch attempts failed: {e3}")
                print("💡 Please try running: gradio --version")
                print("💡 Or try: pip install --upgrade gradio")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("🔄 Trying basic launch...")
        interface.launch()

if __name__ == "__main__":
    main()