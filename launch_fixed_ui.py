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
        
        # Automatically sync registry with vector store on startup
        self._auto_sync_registry()
        
        # Initialize monitoring configuration
        self._initialize_monitoring_config()
    
    def _initialize_monitoring_config(self):
        """Initialize monitoring configuration from saved settings"""
        try:
            # Check if monitoring initialization is disabled via environment variable
            if os.getenv('DISABLE_MONITORING_INIT', '').lower() in ['true', '1', 'yes']:
                print("DEBUG: Monitoring initialization disabled via DISABLE_MONITORING_INIT environment variable")
                return
            
            # Disable automatic initialization by default since UI provides full control
            # Users can manage folder monitoring through the UI interface
            print("DEBUG: Skipping automatic folder monitoring initialization")
            print("DEBUG: Use the 'Folder Monitor' tab in the UI to manage folder monitoring")
            print("DEBUG: Set ENABLE_MONITORING_INIT=true environment variable to enable automatic initialization")
            
            if not os.getenv('ENABLE_MONITORING_INIT', '').lower() in ['true', '1', 'yes']:
                return
            # Check if backend is available before attempting to configure monitoring
            backend_available = False
            try:
                health_response = requests.get(f"{self.api_url}/health", timeout=3)
                backend_available = health_response.status_code == 200
            except Exception:
                print("DEBUG: Backend not available, skipping monitoring initialization")
                return
            
            if not backend_available:
                print("DEBUG: Backend not responding, skipping monitoring initialization")
                return
                
            # Check if folder monitoring endpoints are available
            try:
                # Test if the folder monitoring endpoint exists
                test_response = requests.get(f"{self.api_url}/folder-monitor/status", timeout=3)
                if test_response.status_code == 404:
                    print("DEBUG: Folder monitoring endpoints not available in backend, skipping initialization")
                    # Try to check what endpoints are available
                    try:
                        docs_response = requests.get(f"{self.api_url}/docs", timeout=3)
                        if docs_response.status_code == 200:
                            print("DEBUG: Backend API docs are available at /docs - check for folder monitoring endpoints")
                    except:
                        pass
                    return
                elif test_response.status_code >= 500:
                    print(f"DEBUG: Folder monitoring service error (HTTP {test_response.status_code}), skipping initialization")
                    return
                elif test_response.status_code == 200:
                    print("DEBUG: Folder monitoring endpoints are available")
                    # Check current status
                    try:
                        status_data = test_response.json()
                        current_status = status_data.get('status', 'unknown')
                        print(f"DEBUG: Current folder monitoring status: {current_status}")
                    except:
                        print("DEBUG: Could not parse folder monitoring status response")
                else:
                    print(f"DEBUG: Folder monitoring status endpoint returned HTTP {test_response.status_code}")
            except Exception as e:
                print(f"DEBUG: Could not check folder monitoring availability: {e}")
                # Continue anyway - the endpoint might exist but not respond to status
                
            # Load configuration from file
            config_path = "data/config/system_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                configured_folders = config.get('folder_monitoring', {}).get('monitored_folders', [])
                print(f"DEBUG: Found {len(configured_folders)} folders in configuration")
                
                # Track successfully added folders
                successfully_added_folders = []
                
                # Try to add configured folders to monitoring if they exist
                for folder in configured_folders:
                    if os.path.exists(folder):
                        try:
                            # Try the primary endpoint first
                            response = requests.post(
                                f"{self.api_url}/folder-monitor/add",
                                json={"folder_path": folder},
                                timeout=5
                            )
                            
                            # If that fails, try alternative endpoint patterns
                            if response.status_code == 404:
                                print(f"DEBUG: Trying alternative endpoint for {folder}")
                                response = requests.post(
                                    f"{self.api_url}/monitoring/folders/add",
                                    json={"folder_path": folder},
                                    timeout=5
                                )
                            if response.status_code == 200:
                                print(f"DEBUG: Successfully added {folder} to monitoring")
                                successfully_added_folders.append(folder)
                            else:
                                error_details = ""
                                try:
                                    error_data = response.json()
                                    error_details = f" - {error_data.get('detail', error_data.get('message', 'No details'))}"
                                except:
                                    response_text = response.text[:500] if response.text else 'No response text'
                                    error_details = f" - {response_text}"
                                
                                print(f"DEBUG: Could not add {folder} to monitoring: HTTP {response.status_code}{error_details}")
                                print(f"DEBUG: Request was: POST {self.api_url}/folder-monitor/add with {{'folder_path': '{folder}'}}")
                                
                                # If this is the first folder and we get 400, the API might not support folder monitoring
                                if response.status_code == 400 and folder == configured_folders[0]:
                                    print("DEBUG: First folder failed with HTTP 400 - folder monitoring API may not be implemented")
                                    print("DEBUG: Skipping remaining folder monitoring initialization")
                                    return
                        except Exception as e:
                            print(f"DEBUG: Exception adding {folder} to monitoring: {e}")
                    else:
                        print(f"DEBUG: Configured folder does not exist: {folder}")
                
                # Only try to start monitoring if we successfully added at least one folder
                if successfully_added_folders:
                    print(f"DEBUG: Attempting to start monitoring for {len(successfully_added_folders)} successfully added folders")
                    try:
                        response = requests.post(f"{self.api_url}/folder-monitor/start", timeout=5)
                        if response.status_code == 200:
                            print(f"DEBUG: Folder monitoring started successfully for folders: {successfully_added_folders}")
                        else:
                            error_details = ""
                            try:
                                error_data = response.json()
                                error_details = f" - {error_data.get('detail', error_data.get('message', 'No details'))}"
                            except:
                                response_text = response.text[:500] if response.text else 'No response text'
                                error_details = f" - {response_text}"
                            print(f"DEBUG: Could not start folder monitoring: HTTP {response.status_code}{error_details}")
                            print(f"DEBUG: Request was: POST {self.api_url}/folder-monitor/start")
                            print(f"DEBUG: Successfully added folders were: {successfully_added_folders}")
                    except Exception as e:
                        print(f"DEBUG: Exception starting folder monitoring: {e}")
                        print(f"DEBUG: Successfully added folders were: {successfully_added_folders}")
                elif configured_folders:
                    print(f"DEBUG: No folders were successfully added to monitoring (out of {len(configured_folders)} configured)")
                    print("DEBUG: Cannot start monitoring without successfully added folders")
                else:
                    print("DEBUG: No folders configured for monitoring")
            else:
                print("DEBUG: Configuration file not found")
                
        except Exception as e:
            print(f"DEBUG: Failed to initialize monitoring config: {e}")
        
    def _safe_response_text(self, response, max_length: int = 200) -> str:
        """Safely extract text from response with length limit"""
        try:
            if hasattr(response, 'text') and response.text is not None:
                text = str(response.text)
                return text[:max_length] if len(text) > max_length else text
            elif hasattr(response, 'content') and response.content is not None:
                content = response.content
                if isinstance(content, bytes):
                    text = content.decode('utf-8', errors='replace')
                else:
                    text = str(content)
                return text[:max_length] if len(text) > max_length else text
            else:
                return "No response content available"
        except Exception as e:
            return f"Error reading response: {str(e)}"

    def _auto_sync_registry(self):
        """Automatically sync registry with vector store on startup"""
        try:
            print("DEBUG: Auto-syncing registry with vector store...")
            
            # First try to get documents from the API
            response = requests.get(f"{self.api_url}/documents", timeout=10)
            documents_by_path = {}
            
            if response.status_code == 200:
                data = response.json()
                document_details = data.get('document_details', [])
                
                print(f"DEBUG: Retrieved {len(document_details)} document details from API")
                
                # Process API documents
                for doc_detail in document_details:
                    doc_id = doc_detail.get('doc_id', 'unknown')
                    doc_path = doc_detail.get('doc_path', '')
                    filename = doc_detail.get('filename', '')
                    upload_timestamp = doc_detail.get('upload_timestamp', '')
                    source = doc_detail.get('source', 'unknown')
                    chunks = doc_detail.get('chunks', 0)
                    
                    # Create registry path with better chunk handling
                    if doc_path and doc_path != '':
                        registry_path = doc_path
                    elif filename and filename != '':
                        registry_path = f"/docs/{os.path.splitext(filename)[0]}"
                    else:
                        if '_chunk_' in doc_id:
                            # For chunk-based documents, create a base path without chunk suffix
                            base_name = doc_id.split('_chunk_')[0]
                            registry_path = f"/{base_name}"
                        else:
                            registry_path = f"/{doc_id}"
                    
                    # Add to registry with proper chunk grouping
                    if registry_path in documents_by_path:
                        # Update existing document entry
                        documents_by_path[registry_path]['chunks'] += chunks if chunks > 0 else 1
                        documents_by_path[registry_path]['chunk_docs'].append(doc_id)
                        # Update timestamp if newer
                        if upload_timestamp and upload_timestamp > documents_by_path[registry_path]['last_updated']:
                            documents_by_path[registry_path]['last_updated'] = upload_timestamp
                    else:
                        # Create new document entry
                        display_filename = filename if filename else os.path.basename(registry_path)
                        if not display_filename or display_filename == registry_path:
                            if '_chunk_' in doc_id:
                                # For chunk-based docs, create a meaningful filename
                                base_name = doc_id.split('_chunk_')[0]
                                display_filename = base_name.replace('_', ' ').replace('docs ', '').title()
                            else:
                                display_filename = f"{doc_id}.txt"
                        
                        documents_by_path[registry_path] = {
                            'status': 'active',
                            'upload_count': 1,
                            'last_updated': upload_timestamp or datetime.now().isoformat(),
                            'filename': display_filename,
                            'original_filename': filename,
                            'chunks': chunks if chunks > 0 else 1,
                            'source': source or 'auto_sync',
                            'doc_id': doc_id,
                            'chunk_docs': [doc_id]
                        }
            
            # Skip automatic search discovery during startup for faster initialization
            # Search discovery can be triggered manually via the UI button
            print("DEBUG: Skipping automatic search discovery during startup for faster initialization")
            print("DEBUG: Use 'Discover Documents via Search' button in Vector Diagnostics tab if needed")
            discovered_files = set()
            
            # Add documents to registry
            self.document_registry.clear()
            for doc_path, doc_info in documents_by_path.items():
                self.document_registry[doc_path] = doc_info
            
            print(f"DEBUG: Auto-synced {len(documents_by_path)} documents to registry")
            for path, info in documents_by_path.items():
                print(f"DEBUG:   - {path} -> {info['filename']} ({info['chunks']} chunks)")
                    
        except Exception as e:
            print(f"DEBUG: Auto-sync failed: {str(e)}")
            import traceback
            print(f"DEBUG: Auto-sync error details: {traceback.format_exc()}")
            # Don't fail initialization if sync fails

    def check_api_connection(self) -> str:
        """Check if the API is accessible"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=3)
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
                return f"❌ **API Error: HTTP {response.status_code}**\n🌐 Backend URL: {self.api_url}"
        except requests.exceptions.Timeout:
            return f"⏰ **Connection Timeout**\n🌐 Backend URL: {self.api_url}\n💡 Make sure the backend server is running"
        except requests.exceptions.ConnectionError:
            return f"🔌 **Connection Refused**\n🌐 Backend URL: {self.api_url}\n💡 Backend server may not be started"
        except Exception as e:
            return f"❌ **Connection Error:** {str(e)}\n🌐 Backend URL: {self.api_url}"

    def upload_and_refresh(self, file, doc_path, original_filename_override=None) -> Tuple[str, str, List[str]]:
        """Upload file and refresh dropdowns"""
        print(f"DEBUG: upload_and_refresh called with file: {file}, doc_path: {doc_path}")
        
        if file is None:
            registry_display = self._format_document_registry()
            return "Please select a file to upload.", registry_display, []
        
        try:
            # Extract original filename from Gradio file object
            original_filename = None
            temp_file_path = file.name if hasattr(file, 'name') else str(file)
            
            # Debug: Print all available attributes of the file object
            print(f"DEBUG: File object type: {type(file)}")
            print(f"DEBUG: File object attributes: {dir(file)}")
            if hasattr(file, '__dict__'):
                print(f"DEBUG: File object dict: {file.__dict__}")
            
            # Priority 1: Use user-provided override if available
            if original_filename_override and original_filename_override.strip():
                original_filename = original_filename_override.strip()
                print(f"DEBUG: Using user-provided override: {original_filename}")
            # Priority 2: Try to get original filename from Gradio file object attributes
            elif hasattr(file, 'orig_name') and file.orig_name:
                original_filename = file.orig_name
                print(f"DEBUG: Found orig_name: {original_filename}")
            elif hasattr(file, 'filename') and file.filename:
                original_filename = file.filename
                print(f"DEBUG: Found filename: {original_filename}")
            elif hasattr(file, 'original_name') and file.original_name:
                original_filename = file.original_name
                print(f"DEBUG: Found original_name: {original_filename}")
            elif hasattr(file, 'name') and file.name and not ('tmp' in file.name.lower() or 'temp' in file.name.lower()):
                # If file.name doesn't look like a temp path, use it
                original_filename = os.path.basename(file.name)
                print(f"DEBUG: Using file.name as original: {original_filename}")
            else:
                # Fallback: Ask user or use a default name
                original_filename = "uploaded_document.pdf"  # Default fallback
                print(f"DEBUG: Using default fallback filename: {original_filename}")
                print(f"DEBUG: Available file attributes: {[attr for attr in dir(file) if not attr.startswith('_')]}")
            
            print(f"DEBUG: Final - Original filename: {original_filename}, Temp path: {temp_file_path}")
            
            # Use doc_path if provided, otherwise generate from original filename
            if not doc_path or not doc_path.strip():
                clean_filename = os.path.splitext(original_filename)[0]
                doc_path = f"/docs/{clean_filename}"
            
            # Ensure doc_path starts with /
            if not doc_path.startswith('/'):
                doc_path = f"/{doc_path}"
            
            # Read file content
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
            
            # Prepare metadata with doc_path and enhanced source info
            metadata = {
                "doc_path": doc_path,
                "operation": "upload",
                "source": "fixed_ui",
                "source_type": "web_upload",  # Add source_type for consistency
                "upload_source": "fixed_ui",  # Additional source field
                "upload_timestamp": datetime.now().isoformat(),
                "original_filename": original_filename,  # Use the actual original filename
                "filename": original_filename,  # Use the actual original filename
                "display_name": os.path.splitext(original_filename)[0],
                "temp_file_path": temp_file_path  # Keep track of temp path for debugging
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
                
                # Extract doc_id from API response or generate a better one
                api_doc_id = result.get('doc_id') or result.get('document_id')
                if not api_doc_id:
                    # Generate a better doc_id using original filename instead of temp path
                    api_doc_id = f"doc_{original_filename.replace(' ', '_').replace('.', '_')}"
                    print(f"DEBUG: Generated doc_id from filename: {api_doc_id}")
                else:
                    print(f"DEBUG: Using API-provided doc_id: {api_doc_id}")
                
                # Add to registry
                self.document_registry[doc_path] = {
                    'status': 'active',
                    'upload_count': self.document_registry.get(doc_path, {}).get('upload_count', 0) + 1,
                    'last_updated': datetime.now().isoformat(),
                    'filename': original_filename,  # Use the original filename
                    'original_filename': original_filename,  # Store original filename
                    'temp_file_path': temp_file_path,  # Store temp path for reference
                    'doc_id': api_doc_id,  # Store the document ID
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
                result_msg += f"📁 **Original File:** `{original_filename}`\n"
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
                    error_msg += f"Response: {self._safe_response_text(response)}"
                
                registry_display = self._format_document_registry()
                return error_msg, registry_display, []
                
        except Exception as e:
            error_msg = f"❌ **Upload Error**\n{str(e)}"
            registry_display = self._format_document_registry()
            return error_msg, registry_display, []

    def delete_document(self, doc_path_display: str) -> Tuple[str, str, List[str]]:
        """Delete a document from the system"""
        if not doc_path_display or not doc_path_display.strip():
            return "❌ Please select a document from the dropdown to delete", "", []
        
        if doc_path_display == "No documents uploaded" or doc_path_display == "(No documents uploaded yet)":
            return "❌ No documents available to delete. Please upload a document first.", "", []
        
        # Extract actual doc_path from display name
        # Format is either "filename (path)" or just "path"
        if " (" in doc_path_display and doc_path_display.endswith(")"):
            # Extract path from "filename (path)" format
            doc_path = doc_path_display.split(" (")[-1][:-1]  # Remove the closing parenthesis
        else:
            # It's just the path
            doc_path = doc_path_display
        
        if doc_path not in self.document_registry:
            available_docs = list(self.document_registry.keys())
            if available_docs:
                return f"❌ Document '{doc_path}' not found in registry.\n\nAvailable documents: {', '.join(available_docs)}", "", []
            else:
                return f"❌ No documents in registry. Please upload a document first.", "", []
        
        try:
            doc_info = self.document_registry[doc_path]
            
            # Get doc_id with better fallback logic
            doc_id = doc_info.get("doc_id")
            if not doc_id:
                # Generate a better fallback using original filename
                original_filename = doc_info.get('filename', doc_info.get('original_filename', ''))
                if original_filename and original_filename != 'Unknown':
                    doc_id = f"doc_{original_filename.replace(' ', '_').replace('.', '_')}"
                    print(f"DEBUG: Generated fallback doc_id from filename: {doc_id}")
                else:
                    # Last resort: use doc_path
                    doc_id = f"doc_{doc_path.replace('/', '_')}"
                    print(f"DEBUG: Generated fallback doc_id from doc_path: {doc_id}")
            else:
                print(f"DEBUG: Using stored doc_id: {doc_id}")
            
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
            # Enhanced document ID display for deletion
            original_filename = doc_info.get('filename', doc_info.get('original_filename', 'Unknown'))
            
            # Show user-friendly document ID
            if original_filename and original_filename != 'Unknown':
                # Show original filename as the primary identifier
                result += f"🆔 **Document ID:** `{original_filename}`\n"
                # Optionally show the technical doc_id if different
                if doc_id and not doc_id.startswith('doc_' + original_filename.replace(' ', '_').replace('.', '_')):
                    result += f"   📋 **Technical ID:** `{doc_id}`\n"
            else:
                # Fallback to showing the doc_id
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
        """Get list of document paths for dropdown with friendly names"""
        # Only return active and updated documents (not deleted ones)
        active_docs = [(path, info) for path, info in self.document_registry.items() 
                      if info.get("status") != "deleted"]
        
        if not active_docs:
            return ["(No documents uploaded yet)"]
        
        # Create user-friendly dropdown options
        dropdown_options = []
        for doc_path, info in active_docs:
            filename = info.get('filename', info.get('original_filename', ''))
            
            # Create a display name that shows both filename and path
            if filename and filename != 'Unknown' and filename != os.path.basename(doc_path):
                # Show filename with path in parentheses
                display_name = f"{filename} ({doc_path})"
            else:
                # Just show the path if no meaningful filename
                display_name = doc_path
            
            dropdown_options.append(display_name)
        
        print(f"DEBUG: Registry has {len(self.document_registry)} total documents, {len(dropdown_options)} active")
        for i, option in enumerate(dropdown_options):
            print(f"DEBUG:   {i+1}. {option}")
        
        return dropdown_options if dropdown_options else ["(No documents uploaded yet)"]

    def _format_document_registry(self) -> str:
        """Format the document registry for display"""
        # Add debug protection to prevent infinite loops
        import time
        current_time = time.time()
        if hasattr(self, '_last_registry_call'):
            time_diff = current_time - self._last_registry_call
            if time_diff < 0.5:  # Prevent calls more frequent than 0.5 seconds
                print(f"DEBUG: Registry call throttled (last call {time_diff:.2f}s ago)")
                return f"📋 **Document Registry** ({len(self.document_registry)} documents) - Cached"
        self._last_registry_call = current_time
        
        if not self.document_registry:
            return "📋 **No documents in registry**"
        
        # Limit debug output to prevent console spam
        if len(self.document_registry) > 0:
            print(f"DEBUG: Registry has {len(self.document_registry)} total documents, {len([p for p, i in self.document_registry.items() if i.get('status') == 'active'])} active")
            # Only show first few documents in debug to prevent spam
            for i, (doc_path, info) in enumerate(list(self.document_registry.items())[:3]):
                filename = info.get('filename', 'Unknown')
                print(f"DEBUG:   {i+1}. {filename} ({doc_path})")
            if len(self.document_registry) > 3:
                print(f"DEBUG:   ... and {len(self.document_registry) - 3} more documents")
        
        registry_text = f"📋 **Document Registry** ({len(self.document_registry)} documents)\n\n"
        
        for doc_path, info in self.document_registry.items():
            status_emoji = {
                "active": "✅",
                "updated": "🔄", 
                "deleted": "🗑️"
            }.get(info.get("status", "unknown"), "❓")
            
            # Get the best display name
            filename = info.get('filename', info.get('original_filename', 'Unknown'))
            
            # Create a more user-friendly display
            if filename != 'Unknown' and filename != os.path.basename(doc_path):
                registry_text += f"{status_emoji} **{filename}**\n"
                registry_text += f"   📄 Path: `{doc_path}`\n"
            else:
                registry_text += f"{status_emoji} **{doc_path}**\n"
            
            registry_text += f"   📁 File: {filename}\n"
            
            # Show chunks count more clearly
            chunks = info.get('chunks', info.get('chunks_created', 0))
            if isinstance(chunks, int):
                registry_text += f"   📝 Chunks: {chunks}\n"
            else:
                registry_text += f"   📝 Chunks: {chunks}\n"
            
            # Format timestamp better
            last_updated = info.get('last_updated', 'Unknown')
            if last_updated != 'Unknown':
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    registry_text += f"   📅 Last Updated: {formatted_time}\n"
                except:
                    registry_text += f"   📅 Last Updated: {last_updated}\n"
            else:
                registry_text += f"   📅 Last Updated: {last_updated}\n"
            
            registry_text += f"   📊 Status: {info.get('status', 'unknown').upper()}\n"
            
            # Show source information with enhanced display
            source = info.get('source', 'unknown')
            source_display = {
                'fixed_ui': '🖥️ Web UI',
                'web_upload': '📤 File Upload',
                'folder_monitor': '📁 Folder Monitor',
                'api': '🔌 API',
                'auto_sync': '🔄 Auto Sync'
            }.get(source, f"📋 {source.replace('_', ' ').title()}")
            registry_text += f"   🔧 Source: {source_display}\n"
            
            registry_text += f"   📈 Upload Count: {info.get('upload_count', 1)}\n"
            
            # Optional fields
            if info.get('is_update'):
                registry_text += f"   🔄 Is Update: Yes\n"
            if info.get('old_vectors_deleted', 0) > 0:
                registry_text += f"   🗑️ Old Vectors Deleted: {info['old_vectors_deleted']}\n"
            
            if info.get("status") == "deleted" and "deleted_at" in info:
                registry_text += f"   🗑️ Deleted: {info['deleted_at']}\n"
            
            # Show chunk document IDs for debugging (if available)
            if info.get('chunk_docs') and len(info.get('chunk_docs', [])) > 1:
                registry_text += f"   🔗 Chunk IDs: {len(info['chunk_docs'])} chunks\n"
            
            registry_text += "\n"
        
        return registry_text

    def test_query(self, query: str, max_results: int = 5) -> Tuple[str, str, str]:
        """Test a query against the system"""
        print(f"DEBUG: test_query called with query='{query}', max_results={max_results}")
        print(f"DEBUG: query type: {type(query)}, query length: {len(str(query))}")
        
        if not query or not str(query).strip():
            print(f"DEBUG: Query is empty or whitespace-only")
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
                print(f"DEBUG: Query response - Error: {self._safe_response_text(response)}")
            
            if response.status_code == 200:
                response_json = response.json()
                print(f"DEBUG: Full response structure: {response_json}")
                
                # Handle the correct API response structure: {"success": true, "data": {"response": "...", "sources": [...]}}
                if response_json.get('success') and 'data' in response_json:
                    data = response_json['data']
                    raw_answer = data.get('response', '')
                    sources = data.get('sources', [])
                    print(f"DEBUG: Extracted response length: {len(raw_answer)}")
                    print(f"DEBUG: Extracted sources count: {len(sources)}")
                else:
                    print(f"DEBUG: Unexpected response structure or success=false")
                    raw_answer = ''
                    sources = []
                    data = {}
                
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
                            
                            # Enhanced matching logic for chunk-based documents
                            doc_id_matches = False
                            
                            # Direct match
                            if doc_id == info_doc_id:
                                doc_id_matches = True
                            # Chunk-based matching (e.g., doc_id contains chunk info)
                            elif '_chunk_' in doc_id:
                                base_doc_id = doc_id.split('_chunk_')[0]
                                if base_doc_id in doc_path or doc_path.endswith(base_doc_id):
                                    doc_id_matches = True
                            # Path-based matching
                            elif doc_id.startswith(doc_path) or doc_path.startswith(doc_id):
                                doc_id_matches = True
                            # Registry path matching (remove leading slash for comparison)
                            elif doc_path.lstrip('/') in doc_id or doc_id in doc_path.lstrip('/'):
                                doc_id_matches = True
                            
                            if doc_id_matches:
                                registry_match = (doc_path, info)
                                break
                        
                        sources_text += f"**Source {i}** (Score: {score:.3f})\n"
                        
                        # Enhanced document ID display
                        if doc_id == 'unknown' and registry_match:
                            # Use registry information for better document identification
                            doc_path, info = registry_match
                            filename = info.get('filename', info.get('original_filename', 'Unknown'))
                            sources_text += f"Document ID: `{filename}` (Registry: `{doc_path}`)\n"
                        elif doc_id == 'unknown':
                            # Try to extract meaningful info from metadata
                            metadata = source.get('metadata', {})
                            filename = metadata.get('filename', metadata.get('original_filename', ''))
                            if filename:
                                sources_text += f"Document ID: `{filename}` (Vector ID: unknown)\n"
                            else:
                                sources_text += f"Document ID: `unknown` ⚠️\n"
                        else:
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
                    error_msg += f"\nResponse: {self._safe_response_text(response)}"
                
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
                    error_msg += f"Response: {self._safe_response_text(response)}"
                
                return error_msg
                
        except Exception as e:
            return f"❌ **Clear Error:** {str(e)}"

    def update_monitoring_config(self, folder_paths: list = None) -> str:
        """Update the monitoring configuration to ensure persistence"""
        try:
            config_path = "data/config/system_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                if folder_paths is not None:
                    # Use the provided folder paths directly
                    config['folder_monitoring']['monitored_folders'] = folder_paths
                else:
                    # If no paths provided, keep existing ones
                    current_folders = config['folder_monitoring'].get('monitored_folders', [])
                    config['folder_monitoring']['monitored_folders'] = current_folders
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                final_folders = config['folder_monitoring']['monitored_folders']
                return f"✅ Configuration updated with {len(final_folders)} monitored folders"
            else:
                return "❌ Configuration file not found"
        except Exception as e:
            return f"❌ Failed to update configuration: {str(e)}"

    def start_folder_monitoring(self, folder_path: str) -> str:
        """Legacy method - calls add_folder_to_monitoring for backward compatibility"""
        return self.add_folder_to_monitoring(folder_path)

    def add_folder_to_monitoring(self, folder_path: str) -> str:
        """Add a folder to monitoring (renamed from start_folder_monitoring for clarity)"""
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
                        result = f"ℹ️ **Folder Already Being Monitored**\n\n"
                        result += f"📁 **Folder Path:** `{folder_path}`\n"
                        result += f"📅 **Status Check:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        result += f"📁 **Total Folders Monitored:** {len(monitored_folders)}\n"
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
                    result = f"✅ **Folder Added to Backend Monitoring!**\n\n"
                    result += f"📁 **Folder Path:** `{folder_path}`\n"
                    result += f"📄 **Files Found:** {data.get('files_found', 0)}\n"
                    result += f"📅 **Added At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    
                    # Check for immediate scan results
                    if data.get('immediate_scan'):
                        result += f"\n🔍 **Immediate Scan Results:**\n"
                        result += f"- Changes Detected: {data.get('changes_detected', 0)}\n"
                        result += f"- Files Tracked: {data.get('files_tracked', 0)}\n"
                    
                    # Update configuration for persistence
                    status_response = requests.get(f"{self.api_url}/folder-monitor/status", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('success'):
                            current_folders = status_data.get('status', {}).get('monitored_folders', [])
                            config_result = self.update_monitoring_config(current_folders)
                            result += f"\n🔧 **Config Update:** {config_result}\n"
                    
                    result += f"\n💡 **Note:** Backend will automatically detect new files and changes in this folder."
                    result += f"\n🔧 **Configuration:** Folder monitoring settings have been saved for persistence."
                    
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
                    return f"❌ HTTP {response.status_code}: {self._safe_response_text(response)}"
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
                    return f"❌ HTTP {response.status_code}: {self._safe_response_text(response)}"
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
                        try:
                            # Parse and format the timestamp
                            from datetime import datetime
                            dt = datetime.fromisoformat(last_scan.replace('Z', '+00:00'))
                            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                            status_text += f"**🕐 Last Scan:** {formatted_time}\n"
                        except:
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
                            
                            # Add existence check and file count
                            if os.path.exists(display_path):
                                try:
                                    # Count files in folder with expanded file types
                                    supported_extensions = {
                                        '.txt', '.md', '.pdf', '.docx', '.doc', '.json', '.csv', 
                                        '.xlsx', '.xls', '.xlsm', '.xlsb', '.pptx', '.ppt',
                                        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg',
                                        '.vsdx', '.vsd', '.vsdm', '.vstx', '.vst', '.vstm'
                                    }
                                    file_count = 0
                                    for root, dirs, files in os.walk(display_path):
                                        file_count += len([f for f in files if os.path.splitext(f)[1].lower() in supported_extensions])
                                    status_text += f"   ✅ Folder exists and accessible ({file_count} supported files)\n"
                                except:
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

    def get_detailed_file_status(self) -> str:
        """Get detailed status of all monitored files"""
        try:
            response = requests.get(f"{self.api_url}/folder-monitor/files", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    files = data.get('files', {})
                    
                    if not files:
                        return "📭 **No files are currently being tracked**\n\nAdd files to monitored folders to see their status here."
                    
                    status_text = f"## 📄 Detailed File Status ({len(files)} files)\n\n"
                    
                    # Group files by status
                    by_status = {
                        'success': [],
                        'failed': [],
                        'pending': [],
                        'unknown': []
                    }
                    
                    for file_path, file_info in files.items():
                        status = file_info.get('ingestion_status', 'unknown')
                        by_status.get(status, by_status['unknown']).append((file_path, file_info))
                    
                    # Display by status
                    for status, status_files in by_status.items():
                        if not status_files:
                            continue
                            
                        status_emoji = {
                            'success': '✅',
                            'failed': '❌',
                            'pending': '⏳',
                            'unknown': '❓'
                        }.get(status, '❓')
                        
                        status_text += f"### {status_emoji} {status.title()} ({len(status_files)} files)\n\n"
                        
                        for file_path, file_info in status_files:
                            filename = os.path.basename(file_path)
                            status_text += f"**📄 {filename}**\n"
                            status_text += f"   📁 Path: `{file_path}`\n"
                            
                            # File details
                            if 'file_size' in file_info:
                                size_mb = file_info['file_size'] / (1024 * 1024)
                                status_text += f"   📊 Size: {size_mb:.2f} MB\n"
                            
                            if 'last_modified' in file_info:
                                try:
                                    from datetime import datetime
                                    dt = datetime.fromisoformat(file_info['last_modified'].replace('Z', '+00:00'))
                                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                                    status_text += f"   🕐 Modified: {formatted_time}\n"
                                except:
                                    status_text += f"   🕐 Modified: {file_info['last_modified']}\n"
                            
                            if 'detected_at' in file_info:
                                try:
                                    from datetime import datetime  
                                    dt = datetime.fromisoformat(file_info['detected_at'].replace('Z', '+00:00'))
                                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                                    status_text += f"   🔍 Detected: {formatted_time}\n"
                                except:
                                    status_text += f"   🔍 Detected: {file_info['detected_at']}\n"
                            
                            if 'ingestion_error' in file_info and file_info['ingestion_error']:
                                status_text += f"   ⚠️ Error: {file_info['ingestion_error']}\n"
                            
                            if 'parent_folder' in file_info:
                                status_text += f"   📂 Folder: `{file_info['parent_folder']}`\n"
                            
                            status_text += "\n"
                    
                    return status_text
                else:
                    return f"❌ Error: {data.get('error', 'Unknown error')}"
            else:
                return f"❌ HTTP Error: {response.status_code}"
        except Exception as e:
            return f"❌ Connection Error: {str(e)}"

    def sync_config_with_backend(self) -> str:
        """Sync configuration file with current backend monitoring state"""
        try:
            # Get current monitoring status from backend
            response = requests.get(f"{self.api_url}/folder-monitor/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    backend_folders = data.get('status', {}).get('monitored_folders', [])
                    
                    # Update configuration with backend state
                    config_result = self.update_monitoring_config(backend_folders)
                    
                    result = f"🔄 **Configuration Synced with Backend**\n\n"
                    result += f"📁 **Folders in Backend:** {len(backend_folders)}\n"
                    result += f"🔧 **Config Update:** {config_result}\n"
                    
                    if backend_folders:
                        result += f"\n📋 **Current Monitored Folders:**\n"
                        for i, folder in enumerate(backend_folders, 1):
                            result += f"{i}. `{folder}`\n"
                    
                    return result
                else:
                    return f"❌ Backend Error: {data.get('error', 'Unknown error')}"
            else:
                return f"❌ HTTP Error: {response.status_code}"
        except Exception as e:
            return f"❌ Sync Error: {str(e)}"

    def get_supported_file_types_info(self) -> str:
        """Get detailed information about supported file types"""
        info = "## 📋 Comprehensive File Type Support\n\n"
        
        file_categories = {
            "📄 Text Documents": {
                "extensions": [".txt", ".md"],
                "description": "Plain text and Markdown files",
                "processing": "Direct text extraction"
            },
            "📖 PDF Documents": {
                "extensions": [".pdf"],
                "description": "Portable Document Format files",
                "processing": "Text extraction with OCR fallback for scanned PDFs"
            },
            "📝 Microsoft Word": {
                "extensions": [".docx", ".doc"],
                "description": "Word documents (modern and legacy formats)",
                "processing": "Text and formatting extraction"
            },
            "📊 Microsoft Excel": {
                "extensions": [".xlsx", ".xls", ".xlsm", ".xlsb"],
                "description": "Excel spreadsheets and workbooks",
                "processing": "Cell content and structure extraction"
            },
            "🎯 Microsoft PowerPoint": {
                "extensions": [".pptx", ".ppt"],
                "description": "PowerPoint presentations",
                "processing": "Slide content and notes extraction"
            },
            "📐 Microsoft Visio": {
                "extensions": [".vsdx", ".vsd", ".vsdm", ".vstx", ".vst", ".vstm"],
                "description": "Visio diagrams and templates",
                "processing": "Shape text and diagram metadata extraction"
            },
            "🖼️ Image Files": {
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".svg"],
                "description": "Various image formats",
                "processing": "OCR text extraction from images"
            },
            "📊 Data Files": {
                "extensions": [".json", ".csv"],
                "description": "Structured data files",
                "processing": "Data parsing and content extraction"
            }
        }
        
        for category, details in file_categories.items():
            info += f"### {category}\n"
            info += f"**Extensions**: {', '.join(details['extensions'])}\n"
            info += f"**Description**: {details['description']}\n"
            info += f"**Processing**: {details['processing']}\n\n"
        
        info += "### 🔧 Processing Notes\n"
        info += "- **OCR Support**: Images and scanned documents are processed using optical character recognition\n"
        info += "- **Structured Content**: Office documents preserve formatting and structure information\n"
        info += "- **Metadata Extraction**: File properties, creation dates, and author information are captured\n"
        info += "- **Large File Handling**: Files up to 100MB are supported by default\n"
        info += "- **Batch Processing**: Multiple files are processed efficiently in parallel\n\n"
        
        info += "### ⚠️ Important Considerations\n"
        info += "- **Image Quality**: Higher resolution images provide better OCR results\n"
        info += "- **File Corruption**: Damaged files may fail processing and will be marked as failed\n"
        info += "- **Password Protection**: Encrypted files cannot be processed automatically\n"
        info += "- **Complex Layouts**: Some complex document layouts may require manual review\n"
        
        return info

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
                return f"❌ **Failed to get stats:** HTTP {response.status_code}\n{self._safe_response_text(response)}"
                
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
                return f"❌ **Failed to get documents:** HTTP {response.status_code}\n{self._safe_response_text(response)}"
                
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

    def discover_documents_via_search(self) -> str:
        """Manually trigger document discovery via search when backend is available"""
        try:
            # Check if backend is available
            health_response = requests.get(f"{self.api_url}/health", timeout=3)
            if health_response.status_code != 200:
                return "❌ **Backend not available** - Cannot perform search discovery"
            
            print("DEBUG: Manual search discovery triggered...")
            search_queries = [
                "Building", "network", "facility", "manager", "roster", "excel", 
                "pdf", "document", "layout", "floor", "equipment"
            ]
            
            discovered_files = set()
            documents_by_path = {}
            
            for query in search_queries:
                try:
                    search_response = requests.post(
                        f"{self.api_url}/query",
                        json={"query": query, "max_results": 20, "include_metadata": True},
                        timeout=5
                    )
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        sources = search_data.get('sources', [])
                        
                        for source in sources:
                            metadata = source.get('metadata', {})
                            filename = metadata.get('filename', metadata.get('original_filename', ''))
                            
                            if filename and filename not in discovered_files:
                                discovered_files.add(filename)
                                
                                # Create registry entry for discovered file
                                registry_path = f"/docs/{os.path.splitext(filename)[0]}"
                                
                                if registry_path not in documents_by_path:
                                    documents_by_path[registry_path] = {
                                        'status': 'active',
                                        'upload_count': 1,
                                        'last_updated': datetime.now().isoformat(),
                                        'filename': filename,
                                        'original_filename': filename,
                                        'chunks': 1,
                                        'source': 'search_discovery',
                                        'doc_id': source.get('doc_id', 'unknown'),
                                        'chunk_docs': [source.get('doc_id', 'unknown')]
                                    }
                                else:
                                    # Update chunk count
                                    documents_by_path[registry_path]['chunks'] += 1
                                    
                except Exception as search_error:
                    print(f"DEBUG: Search discovery error for '{query}': {str(search_error)}")
                    continue
            
            # Add discovered documents to registry
            for doc_path, doc_info in documents_by_path.items():
                if doc_path not in self.document_registry:
                    self.document_registry[doc_path] = doc_info
            
            return f"✅ **Search Discovery Complete**\n🔍 Discovered {len(discovered_files)} files\n📄 Added {len(documents_by_path)} documents to registry"
            
        except Exception as e:
            return f"❌ **Discovery Error:** {str(e)}"

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
                return f"❌ **Failed to start heartbeat:** HTTP {response.status_code}\n{self._safe_response_text(response)}"
                
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
                return f"❌ **Failed to stop heartbeat:** HTTP {response.status_code}\n{self._safe_response_text(response)}"
                
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
                            
                            # Try different ways to get document identifier and original filename
                            doc_path = None
                            doc_name = None
                            original_filename = None
                            
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
                            
                            # Extract original filename with priority order
                            if isinstance(metadata, dict):
                                # Priority 1: original_filename field
                                if metadata.get('original_filename'):
                                    original_filename = metadata['original_filename']
                                # Priority 2: filename field (if not a temp path)
                                elif metadata.get('filename') and not ('temp' in str(metadata['filename']).lower() or 'tmp' in str(metadata['filename']).lower()):
                                    original_filename = metadata['filename']
                                # Priority 3: nested metadata
                                elif 'metadata' in metadata and isinstance(metadata['metadata'], dict):
                                    nested = metadata['metadata']
                                    if nested.get('original_filename'):
                                        original_filename = nested['original_filename']
                                    elif nested.get('filename') and not ('temp' in str(nested['filename']).lower() or 'tmp' in str(nested['filename']).lower()):
                                        original_filename = nested['filename']
                            
                            # Ensure doc_path is not None
                            if doc_path is None:
                                doc_path = f"/unknown/vector_{i}"
                                doc_name = f"Unknown Document {i}"
                            
                            if doc_path not in documents:
                                # Determine source - check multiple source fields with better priority
                                source = 'unknown'
                                if isinstance(metadata, dict):
                                    # Priority 1: 'source' field (from UI)
                                    if metadata.get('source'):
                                        source = metadata['source']
                                    # Priority 2: 'upload_source' field (from enhanced uploads)
                                    elif metadata.get('upload_source'):
                                        source = metadata['upload_source']
                                    # Priority 3: 'source_type' field (from ingestion engine)
                                    elif metadata.get('source_type'):
                                        source = metadata['source_type']
                                    # Priority 4: Check nested metadata
                                    elif 'metadata' in metadata and isinstance(metadata['metadata'], dict):
                                        nested = metadata['metadata']
                                        if nested.get('source'):
                                            source = nested['source']
                                        elif nested.get('upload_source'):
                                            source = nested['upload_source']
                                        elif nested.get('source_type'):
                                            source = nested['source_type']
                                    
                                    # If still unknown, try to infer from file path
                                    if source == 'unknown':
                                        if 'temp' in str(doc_path).lower() or 'tmp' in str(doc_path).lower():
                                            source = 'web_upload'  # Likely from UI upload
                                        elif '/docs/' in str(doc_path):
                                            source = 'fixed_ui'  # From UI with doc_path
                                
                                documents[doc_path] = {
                                    'name': doc_name,
                                    'path': doc_path,
                                    'chunks': 0,
                                    'source': source,
                                    'last_updated': None,
                                    'file_size': None,
                                    'original_filename': original_filename
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
                                
                                # Update original filename if not already set
                                if not documents[doc_path]['original_filename']:
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
                # Use original filename for display if available and it's a temp path
                display_name = doc_info['name']
                is_temp_path = 'temp' in str(doc_path).lower() or 'tmp' in str(doc_path).lower()
                
                if is_temp_path and doc_info['original_filename']:
                    display_name = doc_info['original_filename']
                
                doc_text += f"📄 **{display_name}**\n"
                
                # Show path differently for temp vs normal paths
                if is_temp_path:
                    doc_text += f"   📁 Path: `{doc_path}` (temporary)\n"
                    if doc_info['original_filename']:
                        doc_text += f"   📁 Original File: `{doc_info['original_filename']}`\n"
                else:
                    doc_text += f"   📁 Path: `{doc_path}`\n"
                
                doc_text += f"   📝 Chunks: **{doc_info['chunks']}**\n"
                
                # Enhanced source display with better formatting
                source_display = doc_info['source']
                source_emoji = {
                    'fixed_ui': '🖥️ Web UI',
                    'web_upload': '📤 File Upload',
                    'folder_monitor': '📁 Folder Monitor',
                    'api': '🔌 API',
                    'auto_sync': '🔄 Auto Sync'
                }.get(source_display, f"📋 {source_display.replace('_', ' ').title()}")
                
                doc_text += f"   🔧 Source: {source_emoji}\n"
                
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
                    
                    # Get current monitored folders from backend and update config
                    try:
                        status_response = requests.get(f"{self.api_url}/folder-monitor/status", timeout=10)
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get('success'):
                                current_folders = status_data.get('status', {}).get('monitored_folders', [])
                                config_result = self.update_monitoring_config(current_folders)
                                return f"✅ Successfully removed folder from monitoring: {folder_path}\n📄 Files removed from tracking: {files_removed}\n🔧 {config_result}"
                    except Exception as config_error:
                        print(f"DEBUG: Failed to update config after folder removal: {config_error}")
                    
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
                
                # Add to local conversation history
                import datetime
                timestamp = datetime.datetime.now().strftime("%m/%d %H:%M")
                title = f"New Chat - {timestamp}"
                self._add_to_conversation_history(thread_id, title)
                
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
            
            # Update conversation title with first user message
            if len(history) == 2:  # First user message (after welcome message)
                # Create a meaningful title from the first user message
                title = message.strip()[:60]
                if len(message) > 60:
                    # Try to break at word boundary
                    last_space = title.rfind(' ')
                    if last_space > 30:
                        title = title[:last_space] + "..."
                    else:
                        title += "..."
                self._update_conversation_title(thread_id, title)
            
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
    
    def get_conversation_history(self) -> List[Tuple[str, str]]:
        """Get list of conversation threads with their titles"""
        try:
            print(f"DEBUG: Fetching conversation history from {self.api_url}/api/conversation/threads")
            response = requests.get(f"{self.api_url}/api/conversation/threads", timeout=5)
            
            print(f"DEBUG: Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"DEBUG: Response data: {data}")
                
                threads = data.get('threads', [])
                print(f"DEBUG: Found {len(threads)} threads from API")
                
                # If API returns empty threads, try to get from local storage simulation
                if not threads:
                    print("DEBUG: API returned empty threads, trying alternative approach...")
                    return self._get_local_conversation_history()
                
                # Format as (thread_id, title) tuples for dropdown
                formatted_threads = []
                for thread in threads:
                    thread_id = thread.get('thread_id', '')
                    # Create a meaningful title from first message or use timestamp
                    title = thread.get('title', '')
                    if not title:
                        # Use first user message as title (truncated)
                        messages = thread.get('messages', [])
                        for msg in messages:
                            if msg.get('type') == 'user':
                                content = msg.get('content', '').strip()
                                if content:
                                    # Clean up the title - remove extra whitespace and make it more readable
                                    title = content[:60].strip()
                                    if len(content) > 60:
                                        # Try to break at word boundary
                                        last_space = title.rfind(' ')
                                        if last_space > 30:
                                            title = title[:last_space] + "..."
                                        else:
                                            title += "..."
                                    break
                        
                        # If still no title, create a descriptive one with timestamp
                        if not title:
                            import datetime
                            timestamp = datetime.datetime.now().strftime("%m/%d %H:%M")
                            title = f"New Chat - {timestamp}"
                    
                    formatted_threads.append((thread_id, title))
                    print(f"DEBUG: Added thread: {thread_id[:8]} - {title}")
                
                print(f"DEBUG: Returning {len(formatted_threads)} formatted threads")
                return formatted_threads
            
            elif response.status_code == 404:
                print("DEBUG: Conversation threads endpoint not found - trying alternative approach")
                return self._get_local_conversation_history()
            else:
                print(f"DEBUG: Unexpected response status: {response.status_code}")
                print(f"DEBUG: Response text: {response.text}")
                return self._get_local_conversation_history()
                
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Request error getting conversation history: {e}")
            return self._get_local_conversation_history()
        except Exception as e:
            print(f"DEBUG: Unexpected error getting conversation history: {e}")
            return self._get_local_conversation_history()
    
    def _get_local_conversation_history(self) -> List[Tuple[str, str]]:
        """Fallback method to get conversation history from local tracking"""
        try:
            # Store conversation threads in a simple in-memory store for now
            # In a real implementation, this would query the database directly
            if not hasattr(self, '_conversation_threads'):
                self._conversation_threads = []
            
            print(f"DEBUG: Local conversation history has {len(self._conversation_threads)} threads")
            return self._conversation_threads
            
        except Exception as e:
            print(f"DEBUG: Error getting local conversation history: {e}")
            return []
    
    def _add_to_conversation_history(self, thread_id: str, title: str = None):
        """Add a conversation to local history tracking"""
        try:
            if not hasattr(self, '_conversation_threads'):
                self._conversation_threads = []
            
            # Generate title if not provided
            if not title:
                import datetime
                timestamp = datetime.datetime.now().strftime("%m/%d %H:%M")
                title = f"Chat - {timestamp}"
            
            # Check if thread already exists
            existing_threads = [t[0] for t in self._conversation_threads]
            if thread_id not in existing_threads:
                self._conversation_threads.insert(0, (thread_id, title))
                print(f"DEBUG: Added thread to local history: {thread_id[:8]} - {title}")
                
                # Keep only last 20 conversations
                if len(self._conversation_threads) > 20:
                    self._conversation_threads = self._conversation_threads[:20]
            
        except Exception as e:
            print(f"DEBUG: Error adding to conversation history: {e}")
    
    def _update_conversation_title(self, thread_id: str, new_title: str):
        """Update the title of an existing conversation"""
        try:
            if not hasattr(self, '_conversation_threads'):
                self._conversation_threads = []
            
            # Find and update the thread
            for i, (tid, old_title) in enumerate(self._conversation_threads):
                if tid == thread_id:
                    self._conversation_threads[i] = (thread_id, new_title)
                    print(f"DEBUG: Updated conversation title: {thread_id[:8]} - {new_title}")
                    break
                    
        except Exception as e:
            print(f"DEBUG: Error updating conversation title: {e}")
    
    def load_conversation_thread(self, thread_id: str) -> Tuple[List[Dict[str, str]], str, str]:
        """Load a specific conversation thread"""
        if not thread_id:
            return [], "", "No thread selected"
        
        try:
            response = requests.get(f"{self.api_url}/api/conversation/thread/{thread_id}")
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])
                
                # Convert to chatbot format
                history = []
                for msg in messages:
                    if msg.get('type') in ['user', 'assistant']:
                        history.append({
                            "role": msg['type'],
                            "content": msg.get('content', '')
                        })
                
                return history, thread_id, f"✅ Loaded conversation {thread_id[:8]}"
            else:
                return [], "", f"❌ Failed to load thread: {response.status_code}"
                
        except Exception as e:
            return [], "", f"❌ Error loading thread: {str(e)}"
    
    def delete_conversation_thread(self, thread_id: str) -> str:
        """Delete a conversation thread"""
        if not thread_id:
            return "No thread selected"
        
        try:
            response = requests.delete(f"{self.api_url}/api/conversation/thread/{thread_id}")
            
            if response.status_code == 200:
                return f"✅ Thread {thread_id[:8]} deleted successfully"
            else:
                return f"❌ Failed to delete thread: {response.status_code}"
                
        except Exception as e:
            return f"❌ Error deleting thread: {str(e)}"
    
    def auto_start_new_conversation(self) -> Tuple[List[Dict[str, str]], str, str]:
        """Automatically start a new conversation when page loads"""
        return self.start_new_conversation()

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
    
    def send_conversation_message_stream(self, message: str, thread_id: str, history: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]], str, Dict[str, Any]]:
        """Send a message in the conversation with streaming response using thread_id"""
        if not message.strip():
            return "", history, "Please enter a message", {}
        
        if not thread_id or thread_id == "No thread":
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": "Please start a new conversation first"})
            return "", history, "No active thread", {}
        
        try:
            import json
            
            # Add user message to history
            history.append({"role": "user", "content": message})
            
            # Send to streaming API using thread_id
            response = requests.post(
                f"{self.api_url}/api/conversation/message/stream",
                json={"message": message, "thread_id": thread_id},
                stream=True,
                headers={"Accept": "text/event-stream"}
            )
            
            if response.status_code == 200:
                # Process streaming response
                assistant_response = ""
                metadata = {}
                enhanced_data = {
                    'suggestions': [],
                    'topics': [],
                    'entities': [],
                    'technical_terms': [],
                    'insights': {},
                    'hints': []
                }
                
                # Process each chunk from the stream
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            
                            if data.get('type') == 'status':
                                # Status update - could show in UI
                                continue
                                
                            elif data.get('type') == 'metadata':
                                # Store metadata for later use
                                metadata = data
                                
                            elif data.get('type') == 'content':
                                # Accumulate response chunks
                                chunk = data.get('chunk', '')
                                assistant_response += chunk
                                
                            elif data.get('type') == 'suggestions':
                                # Process suggestions
                                suggestions = data.get('suggested_questions', [])
                                processed_suggestions = []
                                for suggestion in suggestions[:4]:
                                    if isinstance(suggestion, str):
                                        processed_suggestions.append({
                                            'question': suggestion,
                                            'icon': '💬',
                                            'priority': 0.5,
                                            'has_quick_answer': False
                                        })
                                    else:
                                        processed_suggestions.append(suggestion)
                                enhanced_data['suggestions'] = processed_suggestions
                                
                            elif data.get('type') == 'topics':
                                # Process topics
                                enhanced_data['topics'] = data.get('related_topics', [])[:6]
                                
                            elif data.get('type') == 'sources':
                                # Process sources
                                sources = data.get('sources', [])
                                enhanced_data['sources'] = sources
                                
                            elif data.get('type') == 'complete':
                                # Streaming complete
                                break
                                
                            elif data.get('type') == 'error':
                                # Handle error
                                error_msg = data.get('message', 'Unknown error occurred')
                                history.append({"role": "assistant", "content": f"Error: {error_msg}"})
                                return "", history, f"❌ Streaming Error: {error_msg}", {}
                                
                        except json.JSONDecodeError:
                            # Skip malformed JSON
                            continue
                
                # Add complete assistant response to history
                if assistant_response:
                    history.append({"role": "assistant", "content": assistant_response})
                else:
                    history.append({"role": "assistant", "content": "No response generated"})
                
                # Format additional info from metadata
                info_parts = []
                if metadata.get('turn_count'):
                    info_parts.append(f"Turn: {metadata['turn_count']}")
                if metadata.get('current_phase'):
                    info_parts.append(f"Phase: {metadata['current_phase']}")
                if metadata.get('confidence_score'):
                    info_parts.append(f"Confidence: {metadata['confidence_score']:.2f}")
                
                thread_info = " | ".join(info_parts) if info_parts else "Active conversation (streamed)"
                
                # Generate interaction hints
                hints = []
                if enhanced_data.get('suggestions'):
                    hints.append("💡 Click the suggestion buttons below for quick follow-up questions")
                if metadata.get('total_sources', 0) > 0:
                    hints.append(f"📚 Found {metadata['total_sources']} relevant sources")
                enhanced_data['hints'] = hints[:3]
                
                return "", history, f"✅ {thread_info}", enhanced_data
                
            elif response.status_code == 404:
                error_msg = "🚧 Conversation streaming API not available. Using regular API..."
                # Fallback to regular API
                return self.send_conversation_message(message, thread_id, history[:-1])  # Remove user message added above
            else:
                history.append({"role": "assistant", "content": f"Streaming Error: {response.status_code}"})
                return "", history, f"❌ Streaming API Error: {response.status_code}", {}
                
        except requests.exceptions.RequestException as e:
            # Fallback to regular API on connection error
            return self.send_conversation_message(message, thread_id, history[:-1])  # Remove user message added above
        except Exception as e:
            history.append({"role": "assistant", "content": f"Streaming Error: {str(e)}"})
            return "", history, f"❌ Streaming Error: {str(e)}", {}

    # Pipeline Verification Methods
    def validate_file_for_verification(self, file_path: str) -> Tuple[str, str]:
        """Validate a file before processing with verification"""
        try:
            response = requests.post(
                f"{self.api_url}/api/verification/validate-file",
                json={"file_path": file_path},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("valid"):
                    checks_summary = "\n".join([
                        f"✅ {check['check_name']}: {check['message']}"
                        for check in result.get("checks", [])
                        if check.get("status") == "passed"
                    ])
                    warnings = "\n".join([
                        f"⚠️ {check['check_name']}: {check['message']}"
                        for check in result.get("checks", [])
                        if check.get("status") == "warning"
                    ])
                    
                    status = f"✅ File validation passed!\n\n{checks_summary}"
                    if warnings:
                        status += f"\n\nWarnings:\n{warnings}"
                    
                    details = json.dumps(result, indent=2)
                    return status, details
                else:
                    errors = "\n".join([
                        f"❌ {check['check_name']}: {check['message']}"
                        for check in result.get("checks", [])
                        if check.get("status") == "failed"
                    ])
                    return f"❌ File validation failed!\n\n{errors}", json.dumps(result, indent=2)
            else:
                return f"❌ Validation error: {response.status_code}", f"HTTP Error: {response.text}"
                
        except Exception as e:
            return f"❌ Validation error: {str(e)}", f"Exception: {str(e)}"

    def ingest_with_verification(self, file_path: str, metadata: dict = None) -> Tuple[str, str, str]:
        """Ingest file with full pipeline verification"""
        try:
            payload = {"file_path": file_path}
            if metadata:
                payload["metadata"] = metadata
                
            response = requests.post(
                f"{self.api_url}/api/verification/ingest-with-verification",
                json=payload,
                timeout=300  # 5 minutes for large files
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Format status
                if result.get("success"):
                    status = f"✅ Ingestion successful!\n"
                    if "ingestion_result" in result:
                        ing_result = result["ingestion_result"]
                        status += f"📄 File ID: {ing_result.get('file_id', 'N/A')}\n"
                        status += f"📝 Chunks created: {ing_result.get('chunks_created', 0)}\n"
                        status += f"🔢 Vectors stored: {ing_result.get('vectors_stored', 0)}"
                else:
                    status = f"❌ Ingestion failed: {result.get('error', 'Unknown error')}"
                
                # Format verification details
                verification_details = "## Verification Results\n\n"
                warning_count = 0
                error_count = 0
                
                for stage, checks in result.get("verification_results", {}).items():
                    verification_details += f"### {stage.replace('_', ' ').title()}\n"
                    for check in checks:
                        status = check["status"]
                        if status == "passed":
                            emoji = "✅"
                        elif status == "failed":
                            emoji = "❌"
                            error_count += 1
                        else:
                            emoji = "⚠️"
                            warning_count += 1
                        
                        verification_details += f"{emoji} **{check['check_name']}**: {check['message']}\n"
                        
                        # Add explanation for common warnings
                        if status == "warning" and "fallback processor" in check['message'].lower():
                            verification_details += f"   💡 *This is normal for text files (.txt, .md, .py, etc.)*\n"
                    verification_details += "\n"
                
                # Add summary
                if warning_count > 0 or error_count > 0:
                    verification_details += "---\n\n### 📊 Summary\n"
                    if error_count > 0:
                        verification_details += f"❌ **Errors**: {error_count}\n"
                    if warning_count > 0:
                        verification_details += f"⚠️ **Warnings**: {warning_count}\n"
                    verification_details += "\n💡 *See the Troubleshooting tab for solutions to common warnings*\n"
                
                # Raw JSON details - use safe serialization
                try:
                    raw_details = json.dumps(result, indent=2, default=str)
                except Exception as e:
                    raw_details = f"JSON serialization error: {str(e)}\n\nRaw result: {str(result)}"
                
                return status, verification_details, raw_details
            else:
                error_msg = f"❌ Ingestion error: {response.status_code}"
                return error_msg, f"HTTP Error: {self._safe_response_text(response)}", ""
                
        except Exception as e:
            error_msg = f"❌ Ingestion error: {str(e)}"
            return error_msg, f"Exception: {str(e)}", ""

    def get_verification_dashboard_url(self) -> str:
        """Get the URL for the verification dashboard"""
        return f"{self.api_url}/api/verification/dashboard"

    def test_content_extraction(self, file_path: str) -> Tuple[str, str]:
        """Test content extraction without full ingestion"""
        try:
            response = requests.post(
                f"{self.api_url}/api/verification/test-extraction",
                json={"file_path": file_path},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "error" in result:
                    return f"❌ Extraction error: {result['error']}", json.dumps(result, indent=2)
                
                status = f"✅ Content extraction test completed!\n\n"
                status += f"📄 Processor: {result.get('processor', 'Unknown')}\n"
                status += f"📊 Status: {result.get('status', 'Unknown')}\n"
                status += f"📑 Sheets: {result.get('sheets', 0)}\n"
                status += f"📝 Chunks: {result.get('chunks', 0)}\n"
                status += f"🖼️ Embedded objects: {result.get('embedded_objects', 0)}\n"
                
                if result.get('sample_chunk'):
                    status += f"\n**Sample chunk:**\n{result['sample_chunk'][:200]}..."
                
                return status, json.dumps(result, indent=2, default=str)
            else:
                return f"❌ Test error: {response.status_code}", f"HTTP Error: {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ Test error: {str(e)}", f"Exception: {str(e)}"

    def test_chunking_methods(self, text: str, method: str = "semantic") -> Tuple[str, str]:
        """Test different chunking methods"""
        try:
            response = requests.post(
                f"{self.api_url}/api/verification/test-chunking",
                json={"text": text, "method": method},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                status = f"✅ Chunking test completed!\n\n"
                status += f"🔧 Method: {result.get('method', 'Unknown')}\n"
                status += f"📝 Chunks: {result.get('chunk_count', 0)}\n"
                status += f"📏 Average size: {result.get('avg_size', 0):.0f} chars\n"
                
                chunk_sizes = result.get('chunk_sizes', [])
                if chunk_sizes:
                    status += f"📊 Size range: {min(chunk_sizes)} - {max(chunk_sizes)} chars\n"
                
                return status, json.dumps(result, indent=2, default=str)
            else:
                return f"❌ Chunking test error: {response.status_code}", f"HTTP Error: {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ Chunking test error: {str(e)}", f"Exception: {str(e)}"

    def get_verification_sessions(self) -> Tuple[str, str]:
        """Get all verification sessions"""
        try:
            response = requests.get(
                f"{self.api_url}/api/verification/sessions",
                timeout=30
            )
            
            if response.status_code == 200:
                sessions = response.json()
                
                if not sessions:
                    return "📋 No verification sessions found", "[]"
                
                # Format sessions display
                sessions_display = "## 📋 Verification Sessions\n\n"
                for session in sessions[:10]:  # Show last 10 sessions
                    session_id = session.get('session_id', 'Unknown')
                    file_path = session.get('file_path', 'Unknown')
                    status = session.get('status', 'Unknown')
                    timestamp = session.get('timestamp', 'Unknown')
                    
                    # Status emoji
                    status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
                    
                    sessions_display += f"### {status_emoji} {session_id[:8]}...\n"
                    sessions_display += f"**File**: `{file_path.split('/')[-1] if '/' in file_path else file_path}`\n"
                    sessions_display += f"**Status**: {status.title()}\n"
                    sessions_display += f"**Time**: {timestamp}\n\n"
                
                return sessions_display, json.dumps(sessions, indent=2, default=str)
            else:
                return f"❌ Error fetching sessions: {response.status_code}", f"HTTP Error: {response.text}"
                
        except Exception as e:
            return f"❌ Sessions error: {str(e)}", f"Exception: {str(e)}"

    def get_pipeline_health_status(self) -> str:
        """Get overall pipeline health status"""
        try:
            response = requests.get(
                f"{self.api_url}/api/verification/health",
                timeout=15
            )
            
            if response.status_code == 200:
                health = response.json()
                
                status_display = "## 🏥 Pipeline Health Status\n\n"
                
                # Overall status
                overall_status = health.get('status', 'unknown')
                status_emoji = "✅" if overall_status == "healthy" else "⚠️" if overall_status == "warning" else "❌"
                status_display += f"### {status_emoji} Overall Status: {overall_status.title()}\n\n"
                
                # Component status
                components = health.get('components', {})
                for component, status in components.items():
                    comp_emoji = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
                    status_display += f"- {comp_emoji} **{component.replace('_', ' ').title()}**: {status.title()}\n"
                
                # Recent activity
                if 'recent_activity' in health:
                    activity = health['recent_activity']
                    status_display += f"\n### 📊 Recent Activity\n"
                    status_display += f"- **Sessions Today**: {activity.get('sessions_today', 0)}\n"
                    status_display += f"- **Success Rate**: {activity.get('success_rate', 0):.1f}%\n"
                    status_display += f"- **Average Duration**: {activity.get('avg_duration', 0):.1f}s\n"
                
                return status_display
            else:
                return f"❌ Health check failed: {response.status_code}"
                
        except Exception as e:
            return f"❌ Health check error: {str(e)}"

    def get_pipeline_stage_status(self) -> str:
        """Get visual pipeline stage status"""
        try:
            response = requests.get(
                f"{self.api_url}/api/verification/pipeline-status",
                timeout=15
            )
            
            if response.status_code == 200:
                pipeline_status = response.json()
                
                # Pipeline stages with emojis
                stages = [
                    ("FILE_VALIDATION", "📁", "File Validation"),
                    ("PROCESSOR_SELECTION", "⚙️", "Processor Selection"),
                    ("CONTENT_EXTRACTION", "📄", "Content Extraction"),
                    ("TEXT_CHUNKING", "✂️", "Text Chunking"),
                    ("EMBEDDING_GENERATION", "🧮", "Embedding Generation"),
                    ("VECTOR_STORAGE", "💾", "Vector Storage"),
                    ("METADATA_STORAGE", "🏷️", "Metadata Storage")
                ]
                
                status_display = "## 🔄 Pipeline Stages Status\n\n"
                
                for stage_key, emoji, stage_name in stages:
                    stage_info = pipeline_status.get('stages', {}).get(stage_key, {})
                    status = stage_info.get('status', 'unknown')
                    last_run = stage_info.get('last_run', 'Never')
                    success_rate = stage_info.get('success_rate', 0)
                    
                    # Status emoji
                    if status == 'healthy':
                        status_emoji = "✅"
                    elif status == 'warning':
                        status_emoji = "⚠️"
                    elif status == 'error':
                        status_emoji = "❌"
                    else:
                        status_emoji = "⚪"
                    
                    status_display += f"### {emoji} {stage_name}\n"
                    status_display += f"{status_emoji} **Status**: {status.title()}\n"
                    status_display += f"📅 **Last Run**: {last_run}\n"
                    status_display += f"📊 **Success Rate**: {success_rate:.1f}%\n\n"
                
                return status_display
            else:
                # Fallback display if endpoint doesn't exist
                return """## 🔄 Pipeline Stages

### 📁 File Validation
✅ **Status**: Ready
📋 Validates file existence, size, permissions, and format

### ⚙️ Processor Selection  
✅ **Status**: Ready
🔧 Selects appropriate processor (PDF, Excel, Text, etc.)

### 📄 Content Extraction
✅ **Status**: Ready
📝 Extracts text content from documents

### ✂️ Text Chunking
✅ **Status**: Ready
📄 Splits content into manageable chunks

### 🧮 Embedding Generation
✅ **Status**: Ready
🔢 Generates vector embeddings using Azure AI

### 💾 Vector Storage
✅ **Status**: Ready
🗄️ Stores vectors in FAISS index

### 🏷️ Metadata Storage
✅ **Status**: Ready
📊 Persists file and chunk metadata
"""
                
        except Exception as e:
            return f"❌ Pipeline status error: {str(e)}"

    def get_session_details(self, session_id: str) -> Tuple[str, str]:
        """Get detailed information about a specific verification session"""
        try:
            response = requests.get(
                f"{self.api_url}/api/verification/session/{session_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                session = response.json()
                
                # Format session details
                details_display = f"## 📋 Session Details: {session_id[:8]}...\n\n"
                
                # Basic info
                details_display += f"**Session ID**: `{session_id}`\n"
                details_display += f"**File Path**: `{session.get('file_path', 'Unknown')}`\n"
                details_display += f"**Status**: {session.get('status', 'Unknown').title()}\n"
                details_display += f"**Timestamp**: {session.get('timestamp', 'Unknown')}\n\n"
                
                # Verification results
                if 'result' in session and 'verification_results' in session['result']:
                    details_display += "### 🔍 Verification Results\n\n"
                    
                    for stage, checks in session['result']['verification_results'].items():
                        stage_name = stage.replace('_', ' ').title()
                        details_display += f"#### {stage_name}\n"
                        
                        for check in checks:
                            status = check.get('status', 'unknown')
                            emoji = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
                            details_display += f"{emoji} **{check.get('check_name', 'Unknown')}**: {check.get('message', 'No message')}\n"
                        
                        details_display += "\n"
                
                return details_display, json.dumps(session, indent=2)
            else:
                return f"❌ Session not found: {response.status_code}", f"HTTP Error: {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ Session details error: {str(e)}", f"Exception: {str(e)}"

    def explain_pipeline_warnings(self) -> str:
        """Explain common pipeline warnings and how to resolve them"""
        return """## ⚠️ Common Pipeline Warnings & Solutions

### 🔧 "Fallback Processor Used"
**What it means**: The system couldn't find a specialized processor for your file type, so it used a generic text extraction method.

**When this happens**:
- For `.txt`, `.md`, `.py`, `.js` files (expected behavior)
- For unsupported file formats
- When specialized processors fail to initialize

**Solutions**:
- ✅ **For text files**: This is normal and expected
- 🔧 **For other files**: Check if the file format is supported
- 📋 **For corrupted files**: Try re-saving or converting the file

### 📏 "File Size Warning"
**What it means**: Your file is larger than recommended (>100MB)

**Solutions**:
- ✂️ **Split large files** into smaller sections
- 🗜️ **Compress images** in documents
- 📊 **For Excel files**: Remove unnecessary sheets or data

### 🔍 "Content Extraction Issues"
**What it means**: Some content couldn't be extracted properly

**Solutions**:
- 📄 **For PDFs**: Ensure text is selectable (not scanned images)
- 📊 **For Excel**: Check for merged cells or complex formatting
- 🔓 **For protected files**: Remove password protection

### 🧮 "Embedding Generation Warnings"
**What it means**: Some text chunks couldn't be embedded

**Solutions**:
- 📝 **Check text quality**: Remove special characters or corrupted text
- 📏 **Chunk size**: Very short or very long chunks may cause issues
- 🔄 **Retry**: Temporary Azure AI service issues

### 💾 "Vector Storage Warnings"
**What it means**: Issues storing vectors in the FAISS index

**Solutions**:
- 💽 **Check disk space**: Ensure sufficient storage
- 🔄 **Restart system**: Clear any locked index files
- 🧹 **Clear vector store**: If index is corrupted

### 📊 "Metadata Storage Issues"  
**What it means**: File metadata couldn't be saved properly

**Solutions**:
- 🔓 **Check permissions**: Ensure write access to data directory
- 💽 **Check disk space**: Ensure sufficient storage
- 🔄 **Restart system**: Clear any locked database files
"""

    def start_monitoring_service(self) -> str:
        """Start the monitoring service (without adding folders)"""
        try:
            response = requests.post(f"{self.api_url}/folder-monitor/start", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = f"🟢 **Backend Folder Monitoring Started**\n\n"
                    result += f"📅 **Started At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    
                    # Get current status to show what's being monitored
                    status_response = requests.get(f"{self.api_url}/folder-monitor/status", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('success'):
                            status_info = status_data.get('status', {})
                            monitored_folders = status_info.get('monitored_folders', [])
                            result += f"📁 **Folders Being Monitored:** {len(monitored_folders)}\n"
                            
                            if monitored_folders:
                                result += f"\n**📂 Monitored Folders:**\n"
                                for folder in monitored_folders[:5]:  # Show first 5
                                    result += f"- `{folder}`\n"
                                if len(monitored_folders) > 5:
                                    result += f"- ... and {len(monitored_folders) - 5} more\n"
                                
                                # Trigger immediate scan to process files
                                try:
                                    scan_response = requests.post(f"{self.api_url}/folder-monitor/scan", timeout=30)
                                    if scan_response.status_code == 200:
                                        scan_data = scan_response.json()
                                        if scan_data.get('success'):
                                            result += f"\n🔍 **Immediate Scan Triggered:**\n"
                                            result += f"- Changes Detected: {scan_data.get('changes_detected', 0)}\n"
                                            result += f"- Files Tracked: {scan_data.get('files_tracked', 0)}\n"
                                        else:
                                            result += f"\n⚠️ **Scan Warning:** {scan_data.get('error', 'Unknown error')}\n"
                                    else:
                                        result += f"\n⚠️ **Scan Error:** HTTP {scan_response.status_code}\n"
                                except Exception as scan_e:
                                    result += f"\n⚠️ **Scan Error:** {str(scan_e)}\n"
                            else:
                                result += f"\n⚠️ **Note:** No folders are currently configured for monitoring.\n"
                                result += f"Use the folder input above to add folders to monitor.\n"
                    
                    result += f"\n💡 **Note:** Monitoring service is now active and will check for file changes automatically."
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    if "already running" in error_msg.lower():
                        return f"ℹ️ **Monitoring Already Running**\n\n🟢 The folder monitoring service is already active.\n\n💡 Use 'Refresh Status' to see current monitoring details."
                    else:
                        return f"❌ Failed to start monitoring: {error_msg}"
            elif response.status_code == 400:
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    if "no folders configured" in error_detail.lower():
                        return f"⚠️ **Cannot Start Monitoring**\n\n❌ {error_detail}\n\n💡 **Solution:** Add a folder to monitoring first using the input field above."
                    else:
                        return f"❌ HTTP {response.status_code}: {error_detail}"
                except:
                    return f"❌ HTTP {response.status_code}: {self._safe_response_text(response)}"
            else:
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    return f"❌ HTTP {response.status_code}: {error_detail}"
                except:
                    return f"❌ HTTP {response.status_code}: {self._safe_response_text(response)}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    # ========================================================================================
    # VECTOR INDEX MANAGEMENT METHODS
    # ========================================================================================
    
    def get_vectors_paginated(self, page: int = 1, page_size: int = 20, include_content: bool = False, 
                             doc_filter: str = "", source_type_filter: str = "") -> str:
        """Get paginated list of vectors with metadata"""
        # Ensure page and page_size are integers
        try:
            page = int(page)
        except Exception:
            page = 1
        try:
            page_size = int(page_size)
        except Exception:
            page_size = 20
        try:
            params = {
                'page': page,
                'page_size': page_size,
                'include_content': include_content,
                'include_embeddings': False
            }
            
            if doc_filter.strip():
                params['doc_filter'] = doc_filter.strip()
            if source_type_filter.strip():
                params['source_type_filter'] = source_type_filter.strip()
            
            response = requests.get(f"{self.api_url}/vectors", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    vectors_data = data.get('data', {})
                    vectors = vectors_data.get('vectors', [])
                    pagination = vectors_data.get('pagination', {})
                    summary = vectors_data.get('summary', {})
                    
                    result = "📊 **Vector Index Browser**\n\n"
                    result += f"📄 **Page {pagination.get('page', 1)} of {pagination.get('total_pages', 1)}** "
                    result += f"({pagination.get('total_vectors', 0)} total vectors)\n\n"
                    
                    # Summary statistics
                    result += "📈 **Summary Statistics:**\n"
                    result += f"🔢 Total vectors: {summary.get('total_vectors', 0)}\n"
                    result += f"📁 Unique documents: {summary.get('unique_documents', 0)}\n"
                    
                    source_types = summary.get('source_types', {})
                    if source_types:
                        result += f"🏷️ Source types: {', '.join([f'{k}({v})' for k, v in source_types.items()])}\n"
                    
                    result += "\n📋 **Vectors on this page:**\n\n"
                    
                    for i, vector in enumerate(vectors, 1):
                        result += f"**{i}. Vector ID: {vector.get('vector_id', 'unknown')}**\n"
                        result += f"   📄 Document: `{vector.get('doc_path', 'unknown')}`\n"
                        result += f"   🆔 Doc ID: `{vector.get('doc_id', 'unknown')}`\n"
                        result += f"   🏷️ Source: {vector.get('source_type', 'unknown')}\n"
                        result += f"   📊 Chunk: {vector.get('chunk_index', 0)}\n"
                        result += f"   ⏰ Added: {vector.get('timestamp', 'unknown')}\n"
                        
                        if include_content and 'content' in vector:
                            content = vector['content']
                            preview = content[:200] + "..." if len(content) > 200 else content
                            result += f"   📝 Content: {preview}\n"
                            result += f"   📏 Length: {vector.get('content_length', 0)} chars\n"
                        
                        result += "\n"
                    
                    # Navigation info
                    if pagination.get('has_previous') or pagination.get('has_next'):
                        result += "🔄 **Navigation:**\n"
                        if pagination.get('has_previous'):
                            result += f"⬅️ Previous page available\n"
                        if pagination.get('has_next'):
                            result += f"➡️ Next page available\n"
                    
                    return result
                else:
                    return f"❌ **Failed to get vectors:** {data.get('error', 'Unknown error')}"
            else:
                return f"❌ **HTTP Error {response.status_code}:** {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ **Error getting vectors:** {str(e)}"
    
    def get_vector_details(self, vector_id: str, include_embedding: bool = False) -> str:
        """Get detailed information about a specific vector"""
        try:
            if not vector_id.strip():
                return "❌ **Please provide a vector ID**"
            
            params = {'include_embedding': include_embedding}
            response = requests.get(f"{self.api_url}/vectors/{vector_id.strip()}", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    vector_info = data.get('data', {})
                    
                    result = f"🔍 **Vector Details - ID: {vector_id}**\n\n"
                    
                    # Basic information
                    result += "📋 **Basic Information:**\n"
                    result += f"🆔 Vector ID: `{vector_info.get('vector_id', 'unknown')}`\n"
                    result += f"📄 Document ID: `{vector_info.get('doc_id', 'unknown')}`\n"
                    result += f"📁 Document Path: `{vector_info.get('doc_path', 'unknown')}`\n"
                    result += f"🏷️ Source Type: {vector_info.get('source_type', 'unknown')}\n"
                    result += f"📊 Chunk Index: {vector_info.get('chunk_index', 0)}\n"
                    result += f"⏰ Timestamp: {vector_info.get('timestamp', 'unknown')}\n"
                    result += f"📏 Content Length: {vector_info.get('content_length', 0)} characters\n\n"
                    
                    # Content
                    content = vector_info.get('content', '')
                    if content:
                        result += "📝 **Content:**\n"
                        preview = content[:500] + "..." if len(content) > 500 else content
                        result += f"```\n{preview}\n```\n\n"
                    
                    # Embedding statistics
                    if 'embedding_stats' in vector_info:
                        stats = vector_info['embedding_stats']
                        result += "🧮 **Embedding Statistics:**\n"
                        result += f"📐 Dimension: {stats.get('dimension', 'unknown')}\n"
                        result += f"📊 Norm: {stats.get('norm', 'unknown'):.4f}\n"
                        result += f"📉 Min Value: {stats.get('min_value', 'unknown'):.4f}\n"
                        result += f"📈 Max Value: {stats.get('max_value', 'unknown'):.4f}\n"
                        result += f"📊 Mean Value: {stats.get('mean_value', 'unknown'):.4f}\n\n"
                    
                    # Similar vectors
                    similar_vectors = vector_info.get('similar_vectors', [])
                    if similar_vectors:
                        result += "🔗 **Similar Vectors:**\n"
                        for i, similar in enumerate(similar_vectors, 1):
                            result += f"{i}. **Vector {similar.get('vector_id', 'unknown')}** "
                            result += f"(similarity: {similar.get('similarity', 0):.3f})\n"
                            result += f"   📄 Doc: `{similar.get('doc_id', 'unknown')}`\n"
                            result += f"   📝 Preview: {similar.get('content_preview', 'No preview')}\n\n"
                    
                    return result
                else:
                    return f"❌ **Failed to get vector details:** {data.get('error', 'Unknown error')}"
            else:
                return f"❌ **HTTP Error {response.status_code}:** {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ **Error getting vector details:** {str(e)}"
    
    def search_vectors_advanced(self, query: str, k: int = 10, similarity_threshold: float = 0.0, 
                               doc_filter: str = "") -> str:
        """Search vectors with advanced filtering and statistics"""
        try:
            if not query.strip():
                return "❌ **Please provide a search query**"
            
            params = {
                'query': query.strip(),
                'k': k,
                'similarity_threshold': similarity_threshold,
                'include_embeddings': False
            }
            
            if doc_filter.strip():
                params['doc_filter'] = doc_filter.strip()
            
            response = requests.get(f"{self.api_url}/vectors/search", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    search_data = data.get('data', {})
                    results = search_data.get('results', [])
                    stats = search_data.get('statistics', {})
                    params_used = search_data.get('search_params', {})
                    
                    result = f"🔍 **Advanced Vector Search Results**\n\n"
                    result += f"🎯 **Query:** '{search_data.get('query', 'unknown')}'\n\n"
                    
                    # Search statistics
                    result += "📊 **Search Statistics:**\n"
                    result += f"📄 Results found: {stats.get('total_results', 0)}\n"
                    result += f"📈 Average similarity: {stats.get('avg_similarity', 0):.3f}\n"
                    result += f"🔝 Max similarity: {stats.get('max_similarity', 0):.3f}\n"
                    result += f"📉 Min similarity: {stats.get('min_similarity', 0):.3f}\n"
                    result += f"✅ Above threshold: {stats.get('results_above_threshold', 0)}\n\n"
                    
                    # Search parameters
                    result += "⚙️ **Search Parameters:**\n"
                    result += f"🔢 Max results (k): {params_used.get('k', 'unknown')}\n"
                    result += f"📊 Similarity threshold: {params_used.get('similarity_threshold', 0):.3f}\n"
                    if params_used.get('doc_filter'):
                        result += f"🔍 Document filter: '{params_used.get('doc_filter')}'\n"
                    result += "\n"
                    
                    # Results
                    if results:
                        result += "📋 **Search Results:**\n\n"
                        for i, res in enumerate(results, 1):
                            result += f"**{i}. Similarity: {res.get('similarity', 0):.3f}**\n"
                            result += f"   🆔 Vector ID: `{res.get('vector_id', 'unknown')}`\n"
                            result += f"   📄 Document: `{res.get('doc_path', 'unknown')}`\n"
                            result += f"   🏷️ Source: {res.get('source_type', 'unknown')}\n"
                            result += f"   📊 Chunk: {res.get('chunk_index', 0)}\n"
                            result += f"   📝 Preview: {res.get('content_preview', 'No preview')}\n\n"
                    else:
                        result += "❌ **No results found**\n"
                        result += "💡 Try lowering the similarity threshold or using different search terms.\n"
                    
                    return result
                else:
                    return f"❌ **Search failed:** {data.get('error', 'Unknown error')}"
            else:
                return f"❌ **HTTP Error {response.status_code}:** {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ **Error searching vectors:** {str(e)}"
    
    # ========================================================================================
    # QUERY PERFORMANCE MONITORING METHODS
    # ========================================================================================
    
    def get_query_performance_metrics(self, time_range_hours: int = 24, limit: int = 50) -> str:
        """Get comprehensive query performance analytics"""
        try:
            params = {
                'limit': limit,
                'include_details': True,
                'time_range_hours': time_range_hours
            }
            
            response = requests.get(f"{self.api_url}/performance/queries", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    perf_data = data.get('data', {})
                    stats = perf_data.get('performance_stats', {})
                    complexity = perf_data.get('complexity_stats', {})
                    errors = perf_data.get('error_analysis', {})
                    recent_queries = perf_data.get('recent_queries', [])
                    
                    result = f"📈 **Query Performance Analytics**\n\n"
                    result += f"⏰ **Time Range:** Last {time_range_hours} hours\n"
                    result += f"📊 **Data Points:** {perf_data.get('data_points', 0)} queries\n\n"
                    
                    # Performance statistics
                    result += "🚀 **Performance Statistics:**\n"
                    result += f"📝 Total queries: {stats.get('total_queries', 0)}\n"
                    result += f"⏱️ Avg response time: {stats.get('avg_response_time', 0):.3f}s\n"
                    result += f"🚀 Min response time: {stats.get('min_response_time', 0):.3f}s\n"
                    result += f"🐌 Max response time: {stats.get('max_response_time', 0):.3f}s\n"
                    result += f"✅ Success rate: {stats.get('success_rate', 0):.1f}%\n"
                    result += f"❌ Error rate: {stats.get('error_rate', 0):.1f}%\n\n"
                    
                    # Component breakdown
                    result += "🔧 **Component Performance:**\n"
                    result += f"🧠 Avg embedding time: {stats.get('avg_embedding_time', 0):.3f}s\n"
                    result += f"🔍 Avg search time: {stats.get('avg_search_time', 0):.3f}s\n"
                    result += f"🤖 Avg LLM time: {stats.get('avg_llm_time', 0):.3f}s\n\n"
                    
                    # Query complexity
                    result += "📊 **Query Complexity:**\n"
                    result += f"📏 Avg query length: {complexity.get('avg_query_length', 0):.0f} characters\n"
                    result += f"📄 Avg sources returned: {complexity.get('avg_sources_returned', 0):.1f}\n"
                    result += f"📈 Max sources returned: {complexity.get('max_sources_returned', 0)}\n\n"
                    
                    # Error analysis
                    if errors.get('total_errors', 0) > 0:
                        result += "❌ **Error Analysis:**\n"
                        result += f"🔢 Total errors: {errors.get('total_errors', 0)}\n"
                        error_types = errors.get('error_types', {})
                        for error_type, count in error_types.items():
                            result += f"   • {error_type}: {count}\n"
                        result += "\n"
                    
                    # Recent queries
                    if recent_queries:
                        result += f"📋 **Recent Queries** (last {min(len(recent_queries), 10)}):\n\n"
                        for i, query_log in enumerate(recent_queries[-10:], 1):
                            status = "✅" if query_log.get('success') else "❌"
                            result += f"{i}. {status} **{query_log.get('response_time', 0):.3f}s** - "
                            result += f"'{query_log.get('query', 'unknown')[:50]}...'\n"
                            
                            if query_log.get('embedding_time'):
                                result += f"   🧠 Embedding: {query_log.get('embedding_time', 0):.3f}s, "
                                result += f"🔍 Search: {query_log.get('search_time', 0):.3f}s, "
                                result += f"🤖 LLM: {query_log.get('llm_time', 0):.3f}s\n"
                            
                            result += f"   📄 Sources: {query_log.get('sources_count', 0)}\n\n"
                    
                    return result
                else:
                    return f"❌ **Failed to get performance metrics:** {data.get('error', 'Unknown error')}"
            else:
                return f"❌ **HTTP Error {response.status_code}:** {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ **Error getting performance metrics:** {str(e)}"
    
    def test_query_performance(self, query: str, max_results: int = 3) -> str:
        """Test query performance with detailed timing breakdown"""
        try:
            if not query.strip():
                return "❌ **Please provide a test query**"
            
            payload = {
                'query': query.strip(),
                'max_results': max_results
            }
            
            response = requests.post(f"{self.api_url}/performance/test", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    perf_data = data.get('data', {})
                    component_times = perf_data.get('component_times', {})
                    breakdown = perf_data.get('performance_breakdown', {})
                    results = perf_data.get('results', {})
                    
                    result = f"🧪 **Query Performance Test**\n\n"
                    result += f"🎯 **Query:** '{perf_data.get('query', 'unknown')}'\n\n"
                    
                    # Overall timing
                    result += "⏱️ **Overall Performance:**\n"
                    result += f"🚀 Total time: **{perf_data.get('total_time', 0):.3f} seconds**\n\n"
                    
                    # Component breakdown
                    result += "🔧 **Component Breakdown:**\n"
                    embedding_time = component_times.get('embedding', 0)
                    search_time = component_times.get('search', 0)
                    llm_time = component_times.get('llm', 0)
                    
                    result += f"🧠 **Embedding Generation:** {embedding_time:.3f}s ({breakdown.get('embedding_percentage', 0):.1f}%)\n"
                    result += f"🔍 **Vector Search:** {search_time:.3f}s ({breakdown.get('search_percentage', 0):.1f}%)\n"
                    result += f"🤖 **LLM Generation:** {llm_time:.3f}s ({breakdown.get('llm_percentage', 0):.1f}%)\n\n"
                    
                    # Results summary
                    result += "📊 **Results Summary:**\n"
                    result += f"📄 Sources found: {results.get('sources_found', 0)}\n"
                    result += f"📐 Embedding dimension: {results.get('embedding_dimension', 'unknown')}\n\n"
                    
                    # Performance analysis
                    result += "🔍 **Performance Analysis:**\n"
                    total_time = perf_data.get('total_time', 0)
                    
                    if total_time < 1.0:
                        result += "✅ **Excellent** - Very fast response time\n"
                    elif total_time < 2.0:
                        result += "🟢 **Good** - Acceptable response time\n"
                    elif total_time < 5.0:
                        result += "🟡 **Fair** - Could be optimized\n"
                    else:
                        result += "🔴 **Slow** - Performance optimization needed\n"
                    
                    # Component analysis
                    if breakdown.get('llm_percentage', 0) > 70:
                        result += "💡 **Tip:** LLM is the bottleneck - consider shorter context or faster model\n"
                    elif breakdown.get('search_percentage', 0) > 50:
                        result += "💡 **Tip:** Search is slow - consider index optimization\n"
                    elif breakdown.get('embedding_percentage', 0) > 30:
                        result += "💡 **Tip:** Embedding generation is slow - consider caching\n"
                    
                    # Error handling
                    if 'llm_error' in component_times:
                        result += f"\n❌ **LLM Error:** {component_times['llm_error']}\n"
                    
                    return result
                else:
                    return f"❌ **Performance test failed:** {data.get('error', 'Unknown error')}"
            else:
                return f"❌ **HTTP Error {response.status_code}:** {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ **Error testing query performance:** {str(e)}"
    
    def get_system_performance(self) -> str:
        """Get real-time system performance metrics"""
        try:
            response = requests.get(f"{self.api_url}/performance/system", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    sys_data = data.get('data', {})
                    sys_resources = sys_data.get('system_resources', {})
                    process_resources = sys_data.get('process_resources', {})
                    vector_store = sys_data.get('vector_store', {})
                    query_perf = sys_data.get('query_performance', {})
                    
                    result = f"🖥️ **System Performance Monitor**\n\n"
                    result += f"⏰ **Timestamp:** {data.get('timestamp', 'unknown')}\n\n"
                    
                    # System resources
                    memory = sys_resources.get('memory', {})
                    cpu = sys_resources.get('cpu', {})
                    disk = sys_resources.get('disk', {})
                    
                    result += "💾 **System Memory:**\n"
                    result += f"📊 Usage: {memory.get('percent_used', 0):.1f}%\n"
                    result += f"📈 Used: {memory.get('used', 0) / (1024**3):.1f} GB\n"
                    result += f"📉 Available: {memory.get('available', 0) / (1024**3):.1f} GB\n"
                    result += f"📏 Total: {memory.get('total', 0) / (1024**3):.1f} GB\n\n"
                    
                    result += "🖥️ **CPU Usage:**\n"
                    result += f"📊 Current: {cpu.get('percent_used', 0):.1f}%\n"
                    result += f"🔢 Cores: {cpu.get('core_count', 'unknown')}\n\n"
                    
                    result += "💽 **Disk Usage:**\n"
                    result += f"📊 Usage: {disk.get('percent_used', 0):.1f}%\n"
                    result += f"📈 Used: {disk.get('used', 0) / (1024**3):.1f} GB\n"
                    result += f"📉 Free: {disk.get('free', 0) / (1024**3):.1f} GB\n\n"
                    
                    # Process resources
                    proc_memory = process_resources.get('memory', {})
                    result += "🔧 **RAG Process Resources:**\n"
                    result += f"💾 Memory (RSS): {proc_memory.get('rss', 0) / (1024**2):.1f} MB\n"
                    result += f"📊 CPU: {process_resources.get('cpu_percent', 0):.1f}%\n"
                    result += f"🧵 Threads: {process_resources.get('threads', 0)}\n"
                    result += f"📁 Open files: {process_resources.get('open_files', 0)}\n\n"
                    
                    # Vector store health
                    result += "🗄️ **Vector Store Health:**\n"
                    result += f"📊 Total vectors: {vector_store.get('ntotal', 0)}\n"
                    result += f"✅ Active vectors: {vector_store.get('active_vectors', 0)}\n"
                    result += f"🗑️ Deleted vectors: {vector_store.get('deleted_vectors', 0)}\n"
                    result += f"📐 Dimension: {vector_store.get('dimension', 'unknown')}\n\n"
                    
                    # Query performance summary
                    result += "🚀 **Query Performance Summary:**\n"
                    result += f"📝 Total logged queries: {query_perf.get('total_logged_queries', 0)}\n"
                    result += f"⏱️ Recent avg response time: {query_perf.get('recent_avg_response_time', 0):.3f}s\n\n"
                    
                    # Health indicators
                    result += "🚦 **Health Indicators:**\n"
                    
                    # Memory health
                    memory_usage = memory.get('percent_used', 0)
                    if memory_usage < 70:
                        result += "✅ Memory: Healthy\n"
                    elif memory_usage < 85:
                        result += "🟡 Memory: Warning\n"
                    else:
                        result += "🔴 Memory: Critical\n"
                    
                    # CPU health
                    cpu_usage = cpu.get('percent_used', 0)
                    if cpu_usage < 70:
                        result += "✅ CPU: Healthy\n"
                    elif cpu_usage < 90:
                        result += "🟡 CPU: Warning\n"
                    else:
                        result += "🔴 CPU: Critical\n"
                    
                    # Disk health
                    disk_usage = disk.get('percent_used', 0)
                    if disk_usage < 80:
                        result += "✅ Disk: Healthy\n"
                    elif disk_usage < 95:
                        result += "🟡 Disk: Warning\n"
                    else:
                        result += "🔴 Disk: Critical\n"
                    
                    return result
                else:
                    return f"❌ **Failed to get system performance:** {data.get('error', 'Unknown error')}"
            else:
                return f"❌ **HTTP Error {response.status_code}:** {self._safe_response_text(response)}"
                
        except Exception as e:
            return f"❌ **Error getting system performance:** {str(e)}"

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
    .status-warning { color: #2196f3; font-weight: bold; }
    
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
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #2196f3;
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
    
    with gr.Blocks(css=css, title="AI Force Intelligent Support Agent") as interface:
        
        gr.Markdown("# **AI Force Intelligent Support Agent**")
        
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
                        
                        original_filename_input = gr.Textbox(
                            label="📝 Original Filename (Optional)",
                            placeholder="e.g., BuildingC_Network_Layout.pdf (auto-detected if empty)",
                            info="Override the auto-detected filename. Useful if the original name isn't detected correctly."
                        )
                        
                        upload_btn = gr.Button("📤 Upload/Update Document", variant="primary", size="lg")
                        
                        gr.Markdown("---")
                        
                        # Delete Section
                        gr.Markdown("#### 🗑️ Delete Document")
                        delete_doc_path_input = gr.Dropdown(
                            label="📄 Select Document to Delete",
                            choices=ui.get_document_paths(),
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
                            value=ui._format_document_registry(),
                            height=600
                        )
                        
                        refresh_registry_btn = gr.Button("🔄 Refresh Registry")
            
            # Query Testing Tab
            with gr.Tab("🔍 Query Testing"):
                gr.Markdown("### Test Queries to See Document Lifecycle Effects")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### 🔍 Query Input")
                        gr.Markdown("**Choose one of the following methods to test queries:**")
                        
                        # Method 1: Simple textbox
                        with gr.Group():
                            gr.Markdown("#### Method 1: Direct Query Input")
                            test_query_input = gr.Textbox(
                                label="Enter your query here",
                                placeholder="Type your question...",
                                lines=1,
                                interactive=True
                            )
                            test_direct_btn = gr.Button("🔍 Test Direct Query", variant="primary")
                        
                        # Method 2: Dropdown with common queries
                        with gr.Group():
                            gr.Markdown("#### Method 2: Pre-defined Queries")
                            common_queries = [
                                "What is the company policy?",
                                "How do I configure the system?", 
                                "What are the network requirements?",
                                "Who is Maia Garcia?",
                                "Tell me about the application process",
                                "What documents do I need?"
                            ]
                            query_dropdown = gr.Dropdown(
                                choices=common_queries,
                                label="Select a common query",
                                value=None
                            )
                            test_dropdown_btn = gr.Button("🔍 Test Selected Query", variant="secondary")
                        
                        # Method 3: Manual text area
                        with gr.Group():
                            gr.Markdown("#### Method 3: Text Area Input")
                            test_textarea = gr.Textbox(
                                label="Enter query in text area",
                                placeholder="Type your question here...",
                                lines=3,
                                max_lines=5,
                                interactive=True
                            )
                            test_textarea_btn = gr.Button("🔍 Test Text Area Query", variant="secondary")
                        
                        max_results_slider = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="Maximum Results"
                        )
                        
                        # Fallback method
                        with gr.Group():
                            gr.Markdown("#### Fallback: Hardcoded Test")
                            test_hardcoded_btn = gr.Button("🧪 Test Hardcoded Query", variant="secondary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 💡 Query Testing Tips")
                        gr.Markdown("""
                        **How to test:**
                        1. Enter your question in the query box
                        2. Adjust max results if needed
                        3. Click "Test Query" to see results
                        
                        **What you'll see:**
                        - 🤖 **AI Response**: Generated answer
                        - 📚 **Sources**: Documents used
                        - 🔍 **Analysis**: Document lifecycle info
                        
                        **Try these example queries:**
                        - "What is the company policy?"
                        - "How do I configure the system?"
                        - "What are the network requirements?"
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
                            choices=ui.get_document_paths_from_overview(),
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
                **Monitor folders for file changes and automatically sync with RAG system:**
                - 📁 **New files** → Automatically uploaded
                - 🔄 **Modified files** → Automatically updated
                - 🗑️ **Deleted files** → Automatically removed from vector store
                - ⏰ **Check interval**: Every 30 seconds (configurable)
                - 📊 **Real-time status** → See what files are processed and what failed
                """)
                
                with gr.Row():
                    with gr.Column(scale=2):
                        # Folder monitoring controls
                        monitor_folder_input = gr.Textbox(
                            label="📁 Folder Path to Monitor (Optional)",
                            placeholder="e.g., C:\\Documents\\MyDocs or /home/user/documents",
                            info="Enter a folder path to add it to monitoring, or leave empty to just start the monitoring service."
                        )
                        
                        with gr.Row():
                            start_monitor_btn = gr.Button("🟢 Start/Resume Monitoring", variant="primary")
                            stop_monitor_btn = gr.Button("🛑 Stop Monitoring", variant="stop")
                            status_refresh_btn = gr.Button("🔄 Refresh Status", variant="secondary")
                            force_scan_btn = gr.Button("🔍 Force Scan", variant="secondary")
                        
                        with gr.Row():
                            retry_failed_btn = gr.Button("🔄 Retry Failed Files", variant="secondary")
                        
                        gr.Markdown("""
                        **💡 How to use:**
                        1. **Option A - Start monitoring service:** Leave folder path empty and click "Start/Resume Monitoring"
                        2. **Option B - Add folder and start:** Enter folder path and click "Start/Resume Monitoring"
                        3. **Check status** to see if monitoring is active and what folders are monitored
                        4. **Add/modify files** in monitored folders to test auto-ingestion
                        5. **Use "Force Scan"** to immediately check for changes
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
                        
                        # Real-time refresh controls
                        with gr.Row():
                            auto_refresh_checkbox = gr.Checkbox(
                                label="🔄 Auto-refresh every 30 seconds",
                                value=False,
                                info="Automatically update status and file details"
                            )
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### 📄 File Processing Status")
                        
                        file_status_display = gr.Markdown(
                            value="*Click 'Refresh Status' to see file processing details*",
                            visible=True
                        )
                        
                        with gr.Row():
                            refresh_files_btn = gr.Button("📄 Refresh File Status", variant="secondary", size="sm")
                        
                        gr.Markdown("---")
                        
                        gr.Markdown("#### 🗂️ Manage Individual Folders")
                        
                        monitored_folders_display = gr.Markdown(
                            value="*Click 'Refresh Folders' to see monitored folders*",
                            visible=True
                        )
                        
                        with gr.Row():
                            refresh_folders_btn = gr.Button("🔄 Refresh Folders", variant="secondary", size="sm")
                            sync_config_btn = gr.Button("🔄 Sync Config", variant="secondary", size="sm")
                        
                        gr.Markdown("""
                        **🔄 Sync Config**: Updates configuration file with current backend state  
                        **🔄 Refresh Folders**: Shows current monitored folders from backend
                        """)
                            
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
                        
                        file_types_display = gr.Markdown("""
                        - 📄 **Text files**: .txt, .md
                        - 📊 **Data files**: .json, .csv
                        - 📖 **PDF Documents**: .pdf
                        - 📝 **Word Documents**: .docx, .doc
                        - 📊 **Excel files**: .xlsx, .xls, .xlsm, .xlsb
                        - 🎯 **PowerPoint**: .pptx, .ppt
                        - 🖼️ **Images**: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .tif, .webp, .svg
                        - 📐 **Visio Diagrams**: .vsdx, .vsd, .vsdm, .vstx, .vst, .vstm
                        
                        *Click "Show Details" for comprehensive file type information*
                        """)
                        
                        with gr.Row():
                            show_file_types_btn = gr.Button("📋 Show File Type Details", variant="secondary", size="sm")
                            hide_file_types_btn = gr.Button("📋 Hide Details", variant="secondary", size="sm", visible=False)
                        
                        gr.Markdown("""
                        #### 🔄 How It Works
                        1. **Start monitoring** a folder
                        2. **Add/modify/delete** files in that folder
                        3. **System automatically syncs** changes
                        4. **Check file status** to see processing details
                        5. **Query testing** to verify changes
                        
                        #### ⚠️ Important Notes
                        - Multiple folders can be monitored simultaneously
                        - Files are checked every 30 seconds
                        - Large files may take time to process
                        - Use "Auto-refresh" for real-time updates
                        - Check "File Processing Status" for detailed info
                        - Images and diagrams are processed using OCR when available
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
                        
                        gr.Markdown("#### 🔍 Document Discovery")
                        gr.Markdown("""
                        **🔍 Search-based document discovery:**
                        - Searches vector store for documents via queries
                        - Adds found documents to UI registry
                        - Useful when backend is running but initial sync failed
                        """)
                        discover_docs_btn = gr.Button("🔍 Discover Documents via Search", variant="secondary")
                        
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
                    # Use a more robust import strategy without dynamic path manipulation
                    servicenow_available = False
                    
                    # Try multiple import strategies
                    import_strategies = [
                        # Strategy 1: Direct import if module is in Python path
                        lambda: __import__('src.api.servicenow_ui', fromlist=['ServiceNowUI']),
                        # Strategy 2: Try relative import from current package
                        lambda: __import__('rag_system.src.api.servicenow_ui', fromlist=['ServiceNowUI']),
                        # Strategy 3: Try importing from ServiceNow-Int directory
                        lambda: __import__('ServiceNow-Int.servicenow_ui', fromlist=['ServiceNowUI'])
                    ]
                    
                    ServiceNowUI = None
                    for i, strategy in enumerate(import_strategies, 1):
                        try:
                            module = strategy()
                            if hasattr(module, 'ServiceNowUI'):
                                ServiceNowUI = module.ServiceNowUI
                                print(f"[OK] ServiceNow UI imported successfully using strategy {i}")
                                break
                        except (ImportError, AttributeError) as e:
                            print(f"[DEBUG] Import strategy {i} failed: {e}")
                            continue
                    
                    if ServiceNowUI is not None:
                        servicenow_ui = ServiceNowUI()
                        servicenow_available = True
                        print("[OK] ServiceNow UI initialized successfully!")
                    else:
                        print("[WARNING] ServiceNow UI module not found in any expected location")
                        servicenow_available = False
                    
                except Exception as e:
                    print(f"[ERROR] ServiceNow UI initialization failed: {e}")
                    print(f"   Current working directory: {os.getcwd()}")
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
                with gr.Row():
                    # Left sidebar for chat history and controls (ChatGPT style)
                    with gr.Column(scale=1, min_width=300):
                        # New Chat button at top
                        with gr.Row():
                            new_chat_btn = gr.Button("🆕 New Chat", variant="primary", size="lg")
                        
                        # Chat History
                        with gr.Group():
                            gr.Markdown("### 📚 Chat History")
                            
                            # Refresh history button
                            refresh_history_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm")
                            
                            # History dropdown
                            chat_history_dropdown = gr.Dropdown(
                                label="Previous Conversations",
                                choices=[],
                                value=None,
                                interactive=True,
                                allow_custom_value=False
                            )
                            
                            # History actions
                            with gr.Row():
                                load_chat_btn = gr.Button("📂 Load", variant="secondary", size="sm")
                                delete_chat_btn = gr.Button("🗑️ Delete", variant="stop", size="sm")
                        
                        # Settings & Controls
                        with gr.Group():
                            gr.Markdown("### ⚙️ Chat Settings")
                            
                            # Enhanced checkboxes for features
                            streaming_toggle = gr.Checkbox(
                                label="🌊 Enable Streaming",
                                value=True,
                                info="Real-time response streaming"
                            )
                            
                            show_sources_toggle = gr.Checkbox(
                                label="📚 Show Sources",
                                value=False,  # Changed to False - user can enable if needed
                                info="Display source documents"
                            )
                            
                            show_suggestions_toggle = gr.Checkbox(
                                label="💡 Smart Suggestions",
                                value=True,
                                info="Show follow-up questions"
                            )
                            
                            show_topics_toggle = gr.Checkbox(
                                label="🔍 Topic Exploration",
                                value=True,
                                info="Show explorable topics"
                            )
                            
                            show_insights_toggle = gr.Checkbox(
                                label="🎯 Conversation Insights",
                                value=False,
                                info="Show conversation analytics"
                            )
                        
                        # Current Thread Info
                        with gr.Group():
                            gr.Markdown("### ℹ️ Current Thread")
                            
                            thread_id_display = gr.Textbox(
                                label="Thread ID",
                                value="",
                                interactive=False,
                                max_lines=1,
                                show_copy_button=True
                            )
                            
                            conversation_status = gr.Markdown(
                                value="🔄 Starting new conversation..."
                            )
                    
                    # Main chat area (ChatGPT style)
                    with gr.Column(scale=3):
                        # Chat display
                        chatbot = gr.Chatbot(
                            label="",
                            height=500,
                            show_label=False,
                            container=True,
                            type="messages",
                            show_copy_button=True,
                            bubble_full_width=False,
                            value=[]  # Will be populated by auto-start
                        )
                        
                        # Message input area (bottom)
                        with gr.Row():
                            message_input = gr.Textbox(
                                placeholder="Message ChatRAG... Press Enter to send",
                                label="",
                                lines=2,
                                scale=4,
                                show_copy_button=False,
                                show_label=False,
                                container=False
                            )
                            send_button = gr.Button("📤", variant="primary", scale=1, size="lg")
                        
                        # Dynamic suggestion area (conditionally shown)
                        suggestions_container = gr.Group(visible=True)
                        with suggestions_container:
                            # Smart suggestions (shown when enabled)
                            suggestions_group = gr.Group(visible=False)
                            with suggestions_group:
                                gr.Markdown("### 💡 Smart Suggestions")
                                with gr.Row():
                                    suggestion_btn_1 = gr.Button("", variant="secondary", visible=False, scale=1)
                                    suggestion_btn_2 = gr.Button("", variant="secondary", visible=False, scale=1)
                                    suggestion_btn_3 = gr.Button("", variant="secondary", visible=False, scale=1)
                                    suggestion_btn_4 = gr.Button("", variant="secondary", visible=False, scale=1)
                            
                            # Topic exploration (shown when enabled)
                            topics_group = gr.Group(visible=False)
                            with topics_group:
                                gr.Markdown("### 🔍 Explore Topics")
                                with gr.Row():
                                    topic_chip_1 = gr.Button("", variant="outline", visible=False, size="sm")
                                    topic_chip_2 = gr.Button("", variant="outline", visible=False, size="sm")
                                    topic_chip_3 = gr.Button("", variant="outline", visible=False, size="sm")
                                    topic_chip_4 = gr.Button("", variant="outline", visible=False, size="sm")
                                    topic_chip_5 = gr.Button("", variant="outline", visible=False, size="sm")
                                    topic_chip_6 = gr.Button("", variant="outline", visible=False, size="sm")
                        
                        # Insights and additional info (conditionally shown)
                        insights_container = gr.Group(visible=False)
                        with insights_container:
                            # Conversation insights
                            conversation_insights = gr.Markdown(
                                label="💡 Conversation Insights",
                                value="",
                                visible=False
                            )
                            
                            # Interactive hints
                            interaction_hints = gr.Markdown(
                                label="🎯 Interactive Hints",
                                value="",
                                visible=False
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
                        
                        # Debug info (collapsible, hidden by default)
                        with gr.Accordion("🔧 Debug Info", open=False, visible=False) as debug_accordion:
                            debug_info = gr.JSON(
                                label="Last Response Data",
                                value={},
                                visible=True
                            )
                
                # Hidden components for internal state management
                clear_suggestions_btn = gr.Button("Clear", visible=False)  # Hidden clear button

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

                ### **Query Testing Flow**
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
                
                ## 🚀 Enhanced Conversation Features

                ### **Smart Suggestions:**
                - 💡 **One-click questions**: Generated based on context
                - ⚡ **Quick responses**: Pre-computed answers for common follow-ups
                - 🎯 **Prioritized suggestions**: Most relevant questions first
                - 🔍 **Context-aware**: Suggestions adapt to conversation flow
                
                ### **Topic Exploration:**
                - 🏷️ **Topic chips**: Click to explore related areas
                - 👥 **Entity cards**: Discover people, places, products
                - 🔧 **Technical terms**: Get definitions and explanations
                - 📊 **Related areas**: Find connected topics
                
                ### **Conversation Intelligence:**
                - 📈 **Conversation health**: Real-time quality assessment
                - 🎯 **Exploration paths**: Suggested conversation directions
                - 💬 **Context retention**: Maintains conversation memory
                - 📊 **Turn analytics**: Track conversation depth and coverage

                ## 💡 Conversation Pro Tips

                ### **Getting Better Suggestions:**
                - Ask specific questions about your documents
                - Use natural, conversational language
                - Build on previous responses for deeper insights
                - Click suggestion buttons for instant follow-ups
                
                ### **Topic Exploration:**
                - Click topic chips to dive deeper
                - Explore entities mentioned in responses
                - Ask about technical terms for definitions
                - Follow suggested exploration paths
                
                ### **Conversation Flow:**
                - Start with broad questions, then get specific
                - Use clarification suggestions when confused
                - Explore related topics for comprehensive understanding
                - End conversations when you have what you need
                
                ## 🤖 Enhanced Conversational Chat with Smart Suggestions
                
                **Engage in intelligent conversations with your RAG system:**
                - 🧠 **Multi-turn conversations** with context retention
                - 🔍 **Knowledge-based responses** using your document database
                - 💡 **Smart follow-up suggestions** with one-click responses
                - 🎯 **Topic exploration** with interactive chips
                - 📊 **Conversation analytics** and session management
                - ⚡ **Quick actions** and contextual hints
                
                ## 🔍 What is Topic Exploration?
                
                **Topic Exploration** is an intelligent feature that helps you discover related concepts and areas of interest based on your conversation:
                
                ### **How it works:**
                - 🎯 **Analyzes your conversation** to identify key topics and themes
                - 🔗 **Finds related concepts** from your document database
                - 💡 **Suggests exploration paths** to deepen your understanding
                - 🏷️ **Creates clickable topic chips** for easy navigation
                
                ### **Topic Chips:**
                - **🔍 Click any topic chip** to explore that subject
                - **Automatically generates questions** about the selected topic
                - **Maintains conversation context** while exploring new areas
                - **Helps discover connections** between different concepts
                
                ### **Example:**
                If you're discussing "network security", topic exploration might suggest:
                - 🔍 Firewall Configuration
                - 🔍 VPN Setup
                - 🔍 Access Control Lists
                - 🔍 Threat Detection
                - 🔍 Security Policies
                - 🔍 Incident Response
                
                **💡 Pro Tip:** Use topic exploration to discover information you didn't know existed in your documents!
                - ⚡ **Response Mode**: Stream responses in real-time for better user experience
                """)

            # Pipeline Verification Tab
            with gr.Tab("🔍 Pipeline Verification"):
                gr.Markdown("### 🔍 Pipeline Verification & Debugging")
                gr.Markdown("""
                **Debug and verify your RAG ingestion pipeline step-by-step:**
                - 📋 **File Validation**: Check files before processing
                - 🔧 **Content Extraction**: Test extraction without full ingestion
                - 📝 **Chunking Methods**: Compare different chunking strategies
                - ✅ **Full Verification**: Complete pipeline verification with detailed reports
                - 📊 **Interactive Dashboard**: Visual pipeline monitoring
                """)
                
                with gr.Tabs():
                    # File Validation Tab
                    with gr.Tab("📋 File Validation"):
                        gr.Markdown("#### 📋 Validate Files Before Processing")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                validate_file_input = gr.File(
                                    label="📁 Select File to Validate",
                                    file_types=[".txt", ".pdf", ".docx", ".doc", ".md", ".json", ".csv", ".xlsx", ".xls", ".xlsm", ".xlsb"],
                                    type="filepath"
                                )
                                
                                validate_file_btn = gr.Button("🔍 Validate File", variant="primary")
                                
                                with gr.Row():
                                    with gr.Column():
                                        validation_status = gr.Markdown(
                                            label="Validation Status",
                                            value="📋 Select a file and click 'Validate File' to check compatibility"
                                        )
                                    
                                    with gr.Column():
                                        validation_details = gr.Code(
                                            label="Validation Details",
                                            language="json",
                                            value="{}",
                                            lines=10
                                        )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 📋 Validation Checks")
                                gr.Markdown("""
                                **File validation includes:**
                                - ✅ **File exists** and is accessible
                                - 📏 **File size** within limits
                                - 🔓 **File permissions** (readable)
                                - 📄 **File extension** supported
                                - 🔍 **File format** validation
                                
                                **Supported formats:**
                                - 📄 Text: .txt, .md
                                - 📊 Excel: .xlsx, .xls, .xlsm, .xlsb
                                - 📝 Word: .docx, .doc
                                - 📋 PDF: .pdf
                                - 📊 Data: .csv, .json
                                
                                **Size limits:**
                                - ⚠️ Warning: > 100MB
                                - ❌ Error: > 500MB
                                """)
                    
                    # Content Extraction Test Tab
                    with gr.Tab("🔧 Content Extraction"):
                        gr.Markdown("#### 🔧 Test Content Extraction")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                extract_file_input = gr.File(
                                    label="📁 Select File to Test Extraction",
                                    file_types=[".txt", ".pdf", ".docx", ".doc", ".md", ".json", ".csv", ".xlsx", ".xls", ".xlsm", ".xlsb"],
                                    type="filepath"
                                )
                                
                                test_extraction_btn = gr.Button("🔧 Test Extraction", variant="primary")
                                
                                with gr.Row():
                                    with gr.Column():
                                        extraction_status = gr.Markdown(
                                            label="Extraction Status",
                                            value="🔧 Select a file and click 'Test Extraction' to analyze content"
                                        )
                                    
                                    with gr.Column():
                                        extraction_details = gr.Code(
                                            label="Extraction Details",
                                            language="json",
                                            value="{}",
                                            lines=10
                                        )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 🔧 Extraction Features")
                                gr.Markdown("""
                                **Content extraction tests:**
                                - 📄 **Processor selection** (Excel, PDF, etc.)
                                - 📊 **Sheet/page detection** 
                                - 📝 **Text extraction** quality
                                - 🖼️ **Embedded objects** (images, diagrams)
                                - 📋 **Metadata extraction**
                                - 🔍 **OCR processing** (if applicable)
                                
                                **For Excel files:**
                                - 📊 Multiple sheets
                                - 📈 Charts and graphs
                                - 🖼️ Embedded Visio diagrams
                                - 📋 Formulas and data
                                
                                **For PDF files:**
                                - 📄 Text extraction
                                - 🖼️ Image extraction
                                - 📋 Metadata and structure
                                """)
                    
                    # Chunking Test Tab
                    with gr.Tab("📝 Chunking Test"):
                        gr.Markdown("#### 📝 Test Different Chunking Methods")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                chunking_text_input = gr.Textbox(
                                    label="📝 Text to Chunk",
                                    placeholder="Enter text to test chunking methods...",
                                    lines=5,
                                    max_lines=10
                                )
                                
                                chunking_method_dropdown = gr.Dropdown(
                                    label="🔧 Chunking Method",
                                    choices=["semantic", "fixed", "recursive"],
                                    value="semantic"
                                )
                                
                                test_chunking_btn = gr.Button("📝 Test Chunking", variant="primary")
                                
                                with gr.Row():
                                    with gr.Column():
                                        chunking_status = gr.Markdown(
                                            label="Chunking Status",
                                            value="📝 Enter text and select a method to test chunking"
                                        )
                                    
                                    with gr.Column():
                                        chunking_details = gr.Code(
                                            label="Chunking Details",
                                            language="json",
                                            value="{}",
                                            lines=10
                                        )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 📝 Chunking Methods")
                                gr.Markdown("""
                                **Available methods:**
                                - 🧠 **Semantic**: Context-aware chunking
                                - 📏 **Fixed**: Fixed-size chunks
                                - 🔄 **Recursive**: Hierarchical chunking
                                
                                **Chunking analysis:**
                                - 📊 **Chunk count** and sizes
                                - 📏 **Size distribution** 
                                - 🔗 **Overlap detection**
                                - 📋 **Metadata preservation**
                                
                                **Quality metrics:**
                                - ⚖️ **Size consistency**
                                - 🔗 **Overlap appropriateness**
                                - 📝 **Content completeness**
                                - 🎯 **Semantic coherence**
                                """)
                    
                    # Full Verification Tab
                    with gr.Tab("✅ Full Verification"):
                        gr.Markdown("#### ✅ Complete Pipeline Verification")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                verify_file_input = gr.File(
                                    label="📁 Select File for Full Verification",
                                    file_types=[".txt", ".pdf", ".docx", ".doc", ".md", ".json", ".csv", ".xlsx", ".xls", ".xlsm", ".xlsb"],
                                    type="filepath"
                                )
                                
                                verify_metadata_input = gr.Textbox(
                                    label="📋 Metadata (JSON, Optional)",
                                    placeholder='{"doc_type": "manual", "category": "technical"}',
                                    lines=2
                                )
                                
                                full_verify_btn = gr.Button("✅ Run Full Verification", variant="primary")
                                
                                with gr.Accordion("📊 Verification Results", open=True):
                                    verification_status = gr.Markdown(
                                        label="Verification Status",
                                        value="✅ Select a file and click 'Run Full Verification' for complete pipeline analysis"
                                    )
                                    
                                    verification_report = gr.Markdown(
                                        label="Verification Report",
                                        value="",
                                        height=300
                                    )
                                
                                with gr.Accordion("🔧 Raw Details", open=False):
                                    verification_raw = gr.Code(
                                        label="Raw Verification Data",
                                        language="json",
                                        value="{}",
                                        lines=15
                                    )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### ✅ Full Pipeline Verification")
                                gr.Markdown("""
                                **Complete verification includes:**
                                - 📋 **File validation** (4 checks)
                                - 🔧 **Content extraction** (6 checks)
                                - 📝 **Text chunking** (5 checks)
                                - 🔢 **Embedding generation** (4 checks)
                                - 💾 **Vector storage** (3 checks)
                                - 📊 **Metadata storage** (2 checks)
                                
                                **Verification stages:**
                                1. 📋 File input validation
                                2. 🔧 Processor selection
                                3. 📄 Content extraction
                                4. 📝 Text chunking
                                5. 🔢 Embedding generation
                                6. 💾 FAISS vector storage
                                7. 📊 Metadata persistence
                                
                                **Output includes:**
                                - ✅ **Pass/Fail** for each check
                                - ⚠️ **Warnings** for potential issues
                                - 📊 **Performance metrics**
                                - 🔧 **Debug information**
                                - 📋 **Detailed reports**
                                """)
                    
                    # Pipeline Status Tab
                    with gr.Tab("🔄 Pipeline Status"):
                        gr.Markdown("#### 🔄 Real-time Pipeline Status")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                pipeline_health_btn = gr.Button("🏥 Check Pipeline Health", variant="primary")
                                pipeline_stages_btn = gr.Button("🔄 View Stage Status", variant="secondary")
                                
                                with gr.Row():
                                    with gr.Column():
                                        pipeline_health_status = gr.Markdown(
                                            label="Pipeline Health",
                                            value="🏥 Click 'Check Pipeline Health' to view system status"
                                        )
                                    
                                    with gr.Column():
                                        pipeline_stages_status = gr.Markdown(
                                            label="Pipeline Stages",
                                            value="🔄 Click 'View Stage Status' to see detailed stage information"
                                        )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 🔄 Pipeline Monitoring")
                                gr.Markdown("""
                                **Real-time monitoring:**
                                - 🏥 **Health Status**: Overall system health
                                - 🔄 **Stage Status**: Individual stage performance
                                - 📊 **Success Rates**: Performance metrics
                                - ⏱️ **Response Times**: Processing speeds
                                - 📈 **Recent Activity**: Usage statistics
                                
                                **Pipeline Stages:**
                                - 📁 File Validation
                                - ⚙️ Processor Selection
                                - 📄 Content Extraction
                                - ✂️ Text Chunking
                                - 🧮 Embedding Generation
                                - 💾 Vector Storage
                                - 🏷️ Metadata Storage
                                """)
                    
                    # Session Management Tab
                    with gr.Tab("📋 Session History"):
                        gr.Markdown("#### 📋 Verification Session Management")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                sessions_refresh_btn = gr.Button("🔄 Refresh Sessions", variant="primary")
                                
                                session_id_input = gr.Textbox(
                                    label="🔍 Session ID (for details)",
                                    placeholder="Enter session ID to view details...",
                                    lines=1
                                )
                                
                                session_details_btn = gr.Button("📋 Get Session Details", variant="secondary")
                                
                                with gr.Row():
                                    with gr.Column():
                                        sessions_display = gr.Markdown(
                                            label="Recent Sessions",
                                            value="📋 Click 'Refresh Sessions' to view recent verification sessions"
                                        )
                                    
                                    with gr.Column():
                                        session_details_display = gr.Markdown(
                                            label="Session Details",
                                            value="🔍 Enter a session ID and click 'Get Session Details' for detailed information"
                                        )
                                
                                with gr.Accordion("🔧 Raw Session Data", open=False):
                                    sessions_raw = gr.Code(
                                        label="Raw Session Data",
                                        language="json",
                                        value="[]",
                                        lines=10
                                    )
                                    
                                    session_details_raw = gr.Code(
                                        label="Raw Session Details",
                                        language="json", 
                                        value="{}",
                                        lines=10
                                    )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 📋 Session Management")
                                gr.Markdown("""
                                **Session tracking:**
                                - 📋 **Recent Sessions**: Last 10 verification sessions
                                - ✅ **Success/Failure**: Status indicators
                                - ⏱️ **Timestamps**: When sessions ran
                                - 📄 **File Names**: Which files were processed
                                - 🔍 **Detailed View**: Complete session information
                                
                                **Session details include:**
                                - 📋 Session metadata
                                - 🔍 Verification results for each stage
                                - ⚠️ Warnings and errors
                                - 📊 Performance metrics
                                - 🔧 Debug information
                                """)
                    
                    # Troubleshooting Tab
                    with gr.Tab("⚠️ Troubleshooting"):
                        gr.Markdown("#### ⚠️ Pipeline Troubleshooting Guide")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                warnings_guide_btn = gr.Button("⚠️ View Common Warnings", variant="primary")
                                
                                warnings_guide_display = gr.Markdown(
                                    label="Troubleshooting Guide",
                                    value="⚠️ Click 'View Common Warnings' to see solutions for common pipeline issues"
                                )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### ⚠️ Common Issues")
                                gr.Markdown("""
                                **Frequent warnings:**
                                - 🔧 **Fallback Processor Used**
                                - 📏 **File Size Warnings**
                                - 🔍 **Content Extraction Issues**
                                - 🧮 **Embedding Generation Problems**
                                - 💾 **Vector Storage Errors**
                                - 📊 **Metadata Storage Issues**
                                
                                **Quick fixes:**
                                - 🔄 **Restart System**: Clears temporary issues
                                - 🧹 **Clear Vector Store**: Fixes corrupted indices
                                - 📋 **Check File Format**: Ensure supported types
                                - 💽 **Check Disk Space**: Ensure sufficient storage
                                """)

                    # Interactive Dashboard Tab
                    with gr.Tab("📊 Interactive Dashboard"):
                        gr.Markdown("#### 📊 Visual Pipeline Monitoring")
                        
                        with gr.Row():
                            with gr.Column():
                                dashboard_url_display = gr.Markdown(
                                    label="Dashboard URL",
                                    value=f"🔗 **Dashboard URL**: {ui.get_verification_dashboard_url()}"
                                )
                                
                                open_dashboard_btn = gr.Button("🚀 Open Interactive Dashboard", variant="primary")
                                
                                gr.Markdown("""
                                #### 📊 Dashboard Features
                                
                                **Real-time monitoring:**
                                - 🔄 **Live pipeline status** updates
                                - 📊 **Visual stage indicators**
                                - ⏱️ **Processing time** tracking
                                - 📈 **Performance metrics**
                                
                                **Interactive debugging:**
                                - 🔍 **Step-by-step** verification
                                - 📋 **Detailed check results**
                                - 🔧 **Debug console** with logs
                                - 📊 **Chunk analysis** tools
                                
                                **Visual pipeline:**
                                - 🟢 **Passed stages** (green)
                                - 🔴 **Failed stages** (red)
                                - 🟡 **Warning stages** (yellow)
                                - ⚪ **Pending stages** (gray)
                                
                                **Export capabilities:**
                                - 📄 **Verification reports** (JSON)
                                - 📊 **Performance data**
                                - 🔧 **Debug outputs**
                                - 📋 **Chunk samples**
                                """)
                            
                            with gr.Column():
                                gr.HTML(f"""
                                <div style="border: 2px solid #ddd; border-radius: 8px; padding: 20px; text-align: center; background: #f9f9f9;">
                                    <h3>🚀 Interactive Pipeline Dashboard</h3>
                                    <p>Click the button below to open the full interactive dashboard in a new tab:</p>
                                    <a href="{ui.get_verification_dashboard_url()}" target="_blank" 
                                       style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; 
                                              text-decoration: none; border-radius: 6px; font-weight: bold; margin: 10px;">
                                        🔗 Open Dashboard
                                    </a>
                                    <p style="font-size: 0.9em; color: #666; margin-top: 15px;">
                                        The dashboard provides real-time visualization of the pipeline verification process
                                        with interactive debugging tools and detailed reports.
                                    </p>
                                </div>
                                """)

            # Vector Management Tab
            with gr.Tab("🗄️ Vector Management"):
                gr.Markdown("### 🗄️ Vector Index Management & Analysis")
                gr.Markdown("""
                **Comprehensive vector index management and analysis tools:**
                - 📊 **Vector Browser**: Paginated browsing of all vectors with metadata
                - 🔍 **Vector Details**: Deep inspection of individual vectors
                - 🔎 **Advanced Search**: Sophisticated vector search with filtering
                - 📈 **Index Statistics**: Complete vector store analytics
                """)
                
                with gr.Tabs():
                    # Vector Browser Tab
                    with gr.Tab("📊 Vector Browser"):
                        gr.Markdown("#### 📊 Browse Vector Index with Pagination")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                with gr.Row():
                                    vectors_page_input = gr.Number(
                                        label="📄 Page Number",
                                        value=1,
                                        minimum=1,
                                        step=1
                                    )
                                    
                                    vectors_page_size_input = gr.Number(
                                        label="📏 Page Size",
                                        value=20,
                                        minimum=5,
                                        maximum=100,
                                        step=5
                                    )
                                
                                with gr.Row():
                                    vectors_include_content_checkbox = gr.Checkbox(
                                        label="📝 Include Content Preview",
                                        value=False
                                    )
                                
                                with gr.Row():
                                    vectors_doc_filter_input = gr.Textbox(
                                        label="🔍 Document Filter",
                                        placeholder="Filter by document path (e.g., 'manual', 'guide')...",
                                        lines=1
                                    )
                                    
                                    vectors_source_filter_input = gr.Textbox(
                                        label="🏷️ Source Type Filter",
                                        placeholder="Filter by source type (e.g., 'pdf', 'txt')...",
                                        lines=1
                                    )
                                
                                vectors_browse_btn = gr.Button("📊 Browse Vectors", variant="primary")
                                
                                vectors_display = gr.Markdown(
                                    label="Vector Index Browser",
                                    value="📊 Click 'Browse Vectors' to start exploring your vector index...",
                                    height=600
                                )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 📊 Vector Browser Guide")
                                gr.Markdown("""
                                **What you'll see:**
                                - 🆔 **Vector IDs**: Unique identifiers
                                - 📄 **Document paths**: Source document info
                                - 🏷️ **Source types**: File format types
                                - 📊 **Chunk indices**: Position in document
                                - ⏰ **Timestamps**: When vectors were added
                                - 📝 **Content preview**: (if enabled)
                                
                                **Navigation:**
                                - ⬅️ **Previous/Next**: Navigate between pages
                                - 📏 **Page size**: Control how many vectors per page
                                - 🔍 **Filters**: Narrow down results
                                
                                **Filtering options:**
                                - 📁 **Document filter**: Find vectors from specific documents
                                - 🏷️ **Source filter**: Filter by file type or source
                                - 📝 **Content preview**: Toggle content display
                                
                                **Performance tips:**
                                - 🚀 **Smaller page sizes** load faster
                                - 🔍 **Use filters** to find specific content
                                - 📝 **Disable content preview** for speed
                                """)
                    
                    # Vector Details Tab
                    with gr.Tab("🔍 Vector Details"):
                        gr.Markdown("#### 🔍 Detailed Vector Inspection")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                vector_id_input = gr.Textbox(
                                    label="🆔 Vector ID",
                                    placeholder="Enter vector ID for detailed inspection...",
                                    lines=1
                                )
                                
                                vector_include_embedding_checkbox = gr.Checkbox(
                                    label="🧮 Include Embedding Statistics",
                                    value=True
                                )
                                
                                vector_details_btn = gr.Button("🔍 Get Vector Details", variant="primary")
                                
                                vector_details_display = gr.Markdown(
                                    label="Vector Details",
                                    value="🔍 Enter a vector ID and click 'Get Vector Details' for comprehensive analysis...",
                                    height=600
                                )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 🔍 Vector Details Guide")
                                gr.Markdown("""
                                **Detailed information includes:**
                                - 📋 **Basic info**: ID, document, source type
                                - 📝 **Full content**: Complete text content
                                - 🧮 **Embedding stats**: Vector mathematics
                                - 🔗 **Similar vectors**: Related content
                                
                                **Embedding statistics:**
                                - 📐 **Dimension**: Vector size (e.g., 1024)
                                - 📊 **Norm**: Vector magnitude
                                - 📈📉 **Min/Max values**: Range of components
                                - 📊 **Mean value**: Average component value
                                
                                **Similar vectors:**
                                - 🔗 **Top 5 similar**: Most related vectors
                                - 📊 **Similarity scores**: Cosine similarity
                                - 📝 **Content previews**: Quick content view
                                
                                **Use cases:**
                                - 🔍 **Debug search results**: Why certain content appears
                                - 📊 **Quality assessment**: Check embedding quality
                                - 🔗 **Content relationships**: Find related documents
                                - 🧮 **Vector analysis**: Mathematical properties
                                """)
                    
                    # Advanced Vector Search Tab
                    with gr.Tab("🔎 Advanced Search"):
                        gr.Markdown("#### 🔎 Advanced Vector Search & Analysis")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                search_query_input = gr.Textbox(
                                    label="🔍 Search Query",
                                    placeholder="Enter your search query...",
                                    lines=2
                                )
                                
                                with gr.Row():
                                    search_k_input = gr.Number(
                                        label="🔢 Max Results (k)",
                                        value=10,
                                        minimum=1,
                                        maximum=50,
                                        step=1
                                    )
                                    
                                    search_threshold_input = gr.Number(
                                        label="📊 Similarity Threshold",
                                        value=0.0,
                                        minimum=0.0,
                                        maximum=1.0,
                                        step=0.05
                                    )
                                
                                search_doc_filter_input = gr.Textbox(
                                    label="📁 Document Filter (Optional)",
                                    placeholder="Filter by document path...",
                                    lines=1
                                )
                                
                                vector_search_btn = gr.Button("🔎 Search Vectors", variant="primary")
                                
                                vector_search_display = gr.Markdown(
                                    label="Advanced Search Results",
                                    value="🔎 Enter a search query and click 'Search Vectors' for detailed analysis...",
                                    height=600
                                )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 🔎 Advanced Search Guide")
                                gr.Markdown("""
                                **Search parameters:**
                                - 🔍 **Query**: Natural language search
                                - 🔢 **Max results (k)**: Limit number of results
                                - 📊 **Threshold**: Minimum similarity score
                                - 📁 **Document filter**: Restrict to specific docs
                                
                                **Search statistics:**
                                - 📄 **Total results**: Number found
                                - 📈 **Average similarity**: Mean score
                                - 🔝 **Max/Min similarity**: Range of scores
                                - ✅ **Above threshold**: Filtered results
                                
                                **Result details:**
                                - 📊 **Similarity scores**: Relevance ranking
                                - 🆔 **Vector IDs**: For detailed inspection
                                - 📄 **Document info**: Source and type
                                - 📝 **Content previews**: Snippet of content
                                
                                **Optimization tips:**
                                - 🎯 **Specific queries** get better results
                                - 📊 **Higher thresholds** filter noise
                                - 📁 **Document filters** narrow scope
                                - 🔢 **Adjust k** for more/fewer results
                                """)

            # Performance Monitoring Tab
            with gr.Tab("📈 Performance Monitor"):
                gr.Markdown("### 📈 Query Performance Monitoring & System Analytics")
                gr.Markdown("""
                **Comprehensive performance monitoring and system analytics:**
                - 📊 **Query Analytics**: Detailed performance metrics and trends
                - 🧪 **Performance Testing**: Benchmark query performance
                - 🖥️ **System Monitor**: Real-time resource usage and health
                - 📈 **Optimization Insights**: Performance tuning recommendations
                """)
                
                with gr.Tabs():
                    # Query Performance Analytics Tab
                    with gr.Tab("📊 Query Analytics"):
                        gr.Markdown("#### 📊 Query Performance Analytics & Trends")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                with gr.Row():
                                    perf_time_range_input = gr.Number(
                                        label="⏰ Time Range (Hours)",
                                        value=24,
                                        minimum=1,
                                        maximum=168,
                                        step=1
                                    )
                                    
                                    perf_limit_input = gr.Number(
                                        label="📊 Max Records",
                                        value=50,
                                        minimum=10,
                                        maximum=500,
                                        step=10
                                    )
                                
                                query_analytics_btn = gr.Button("📊 Get Performance Analytics", variant="primary")
                                
                                query_analytics_display = gr.Markdown(
                                    label="Query Performance Analytics",
                                    value="📊 Click 'Get Performance Analytics' to view comprehensive query performance data...",
                                    height=600
                                )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 📊 Performance Analytics Guide")
                                gr.Markdown("""
                                **Performance statistics:**
                                - 📝 **Total queries**: Volume metrics
                                - ⏱️ **Response times**: Speed analysis
                                - ✅ **Success rates**: Reliability metrics
                                - 🔧 **Component breakdown**: Bottleneck identification
                                
                                **Component analysis:**
                                - 🧠 **Embedding time**: Text-to-vector conversion
                                - 🔍 **Search time**: Vector similarity search
                                - 🤖 **LLM time**: Response generation
                                
                                **Query complexity:**
                                - 📏 **Query length**: Character count analysis
                                - 📄 **Sources returned**: Result size metrics
                                - 📈 **Complexity trends**: Pattern analysis
                                
                                **Error analysis:**
                                - ❌ **Error types**: Categorized failures
                                - 📊 **Error rates**: Failure frequency
                                - 🔍 **Error patterns**: Root cause analysis
                                
                                **Recent queries:**
                                - 📋 **Latest 10 queries**: Recent activity
                                - ⏱️ **Individual timings**: Per-query breakdown
                                - 📄 **Source counts**: Results per query
                                """)
                    
                    # Performance Testing Tab
                    with gr.Tab("🧪 Performance Testing"):
                        gr.Markdown("#### 🧪 Query Performance Testing & Benchmarking")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                test_query_input = gr.Textbox(
                                    label="🎯 Test Query",
                                    placeholder="Enter a query to benchmark performance...",
                                    lines=2
                                )
                                
                                test_max_results_input = gr.Number(
                                    label="📊 Max Results",
                                    value=3,
                                    minimum=1,
                                    maximum=10,
                                    step=1
                                )
                                
                                performance_test_btn = gr.Button("🧪 Run Performance Test", variant="primary")
                                
                                performance_test_display = gr.Markdown(
                                    label="Performance Test Results",
                                    value="🧪 Enter a test query and click 'Run Performance Test' for detailed timing analysis...",
                                    height=600
                                )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 🧪 Performance Testing Guide")
                                gr.Markdown("""
                                **Test metrics:**
                                - 🚀 **Total time**: End-to-end performance
                                - 🔧 **Component breakdown**: Individual timings
                                - 📊 **Percentage distribution**: Time allocation
                                - 📄 **Results summary**: Output analysis
                                
                                **Component timings:**
                                - 🧠 **Embedding**: Query vectorization time
                                - 🔍 **Search**: Vector similarity search time
                                - 🤖 **LLM**: Response generation time
                                
                                **Performance analysis:**
                                - ✅ **Excellent**: < 1 second
                                - 🟢 **Good**: 1-2 seconds
                                - 🟡 **Fair**: 2-5 seconds
                                - 🔴 **Slow**: > 5 seconds
                                
                                **Optimization tips:**
                                - 💡 **LLM bottleneck**: Use shorter context
                                - 💡 **Search bottleneck**: Optimize index
                                - 💡 **Embedding bottleneck**: Consider caching
                                
                                **Use cases:**
                                - 🎯 **Baseline testing**: Establish performance baselines
                                - 🔍 **Bottleneck identification**: Find slow components
                                - 📊 **Before/after comparison**: Measure improvements
                                - 🧪 **Query optimization**: Test different approaches
                                """)
                    
                    # System Performance Tab
                    with gr.Tab("🖥️ System Monitor"):
                        gr.Markdown("#### 🖥️ Real-time System Performance Monitor")
                        
                        with gr.Row():
                            with gr.Column(scale=2):
                                system_monitor_btn = gr.Button("🖥️ Get System Performance", variant="primary")
                                
                                system_performance_display = gr.Markdown(
                                    label="System Performance Monitor",
                                    value="🖥️ Click 'Get System Performance' to view real-time system metrics...",
                                    height=600
                                )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("#### 🖥️ System Monitor Guide")
                                gr.Markdown("""
                                **System resources:**
                                - 💾 **Memory usage**: RAM consumption
                                - 🖥️ **CPU usage**: Processor load
                                - 💽 **Disk usage**: Storage consumption
                                - 🔧 **Process resources**: RAG system specific
                                
                                **Vector store health:**
                                - 📊 **Total vectors**: Index size
                                - ✅ **Active vectors**: Searchable content
                                - 🗑️ **Deleted vectors**: Soft-deleted content
                                - 📐 **Vector dimension**: Embedding size
                                
                                **Query performance:**
                                - 📝 **Total logged queries**: Activity volume
                                - ⏱️ **Recent avg response**: Performance trend
                                
                                **Health indicators:**
                                - ✅ **Healthy**: Green - optimal performance
                                - 🟡 **Warning**: Yellow - attention needed
                                - 🔴 **Critical**: Red - immediate action required
                                
                                **Monitoring use cases:**
                                - 📊 **Capacity planning**: Resource forecasting
                                - 🔍 **Performance troubleshooting**: Issue diagnosis
                                - 📈 **Trend analysis**: Usage patterns
                                - ⚠️ **Alert management**: Proactive monitoring
                                """)

        # Event Handlers
        
        # Connection status
        refresh_connection_btn.click(
            fn=ui.check_api_connection,
            outputs=[connection_status]
        )
        
        # Main upload/update operation
        def upload_and_refresh(file, doc_path, original_filename):
            print(f"DEBUG: upload_and_refresh called with file: {file}, doc_path: {doc_path}, original_filename: {original_filename}")
            result, registry, dropdown_choices = ui.upload_and_refresh(file, doc_path, original_filename)
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
            inputs=[file_input, doc_path_input, original_filename_input],
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
        
        # Simple query testing function
        def simple_test_query(query_input, max_results):
            print(f"DEBUG: simple_test_query called with: '{query_input}', max_results: {max_results}")
            
            if not query_input or not str(query_input).strip():
                return "❌ Please enter a query to test", "", ""
            
            return ui.test_query(str(query_input).strip(), max_results)
        
        # Method 1: Direct textbox
        test_direct_btn.click(
            fn=simple_test_query,
            inputs=[test_query_input, max_results_slider],
            outputs=[query_answer, query_sources, query_lifecycle_analysis]
        )
        
        test_query_input.submit(
            fn=simple_test_query,
            inputs=[test_query_input, max_results_slider],
            outputs=[query_answer, query_sources, query_lifecycle_analysis]
        )
        
        # Method 2: Dropdown selection
        def test_dropdown_query(selected_query, max_results):
            print(f"DEBUG: test_dropdown_query called with: '{selected_query}', max_results: {max_results}")
            
            if not selected_query:
                return "❌ Please select a query from the dropdown", "", ""
            
            return ui.test_query(selected_query, max_results)
        
        test_dropdown_btn.click(
            fn=test_dropdown_query,
            inputs=[query_dropdown, max_results_slider],
            outputs=[query_answer, query_sources, query_lifecycle_analysis]
        )
        
        # Method 3: Text area
        test_textarea_btn.click(
            fn=simple_test_query,
            inputs=[test_textarea, max_results_slider],
            outputs=[query_answer, query_sources, query_lifecycle_analysis]
        )
        
        test_textarea.submit(
            fn=simple_test_query,
            inputs=[test_textarea, max_results_slider],
            outputs=[query_answer, query_sources, query_lifecycle_analysis]
        )
        
        # Hardcoded test query function
        def test_hardcoded_query(max_results):
            print(f"DEBUG: test_hardcoded_query called with max_results = {max_results}")
            hardcoded_query = "What is the company policy?"
            print(f"DEBUG: Using hardcoded query: '{hardcoded_query}'")
            return ui.test_query(hardcoded_query, max_results)
        

        
        # Hardcoded test button
        test_hardcoded_btn.click(
            fn=test_hardcoded_query,
            inputs=[max_results_slider],
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
            # If folder path is provided, add it to monitoring first
            if folder_path and folder_path.strip():
                # Step 1: Add folder to monitoring
                add_result = ui.add_folder_to_monitoring(folder_path)
                
                # Step 2: Start the monitoring service
                start_result = ui.start_monitoring_service()
                
                # Combine results
                result = f"{add_result}\n\n---\n\n{start_result}"
            else:
                # If no folder path, check if any folders are configured
                try:
                    status_response = requests.get(f"{ui.api_url}/folder-monitor/status", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('success'):
                            monitored_folders = status_data.get('status', {}).get('monitored_folders', [])
                            
                            if monitored_folders:
                                # Folders are configured, just start monitoring
                                result = ui.start_monitoring_service()
                            else:
                                # No folders configured
                                result = "⚠️ **Cannot Start Monitoring**\n\n"
                                result += "❌ No folders are currently configured for monitoring.\n\n"
                                result += "💡 **To start monitoring:**\n"
                                result += "1. Enter a folder path in the input field above\n"
                                result += "2. Click 'Start/Resume Monitoring' again\n\n"
                                result += "📁 **Example paths:**\n"
                                result += "- `D:\\Projects-D\\pepsi-final2\\document_generator\\test_data`\n"
                                result += "- `C:\\Users\\YourName\\Documents\\MyFiles`\n"
                                result += "- `./data/documents`"
                        else:
                            result = f"❌ Error checking status: {status_data.get('error', 'Unknown error')}"
                    else:
                        result = f"❌ HTTP Error {status_response.status_code} checking status"
                except Exception as e:
                    result = f"❌ Error checking folder status: {str(e)}"
            
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
        
        def force_scan_and_refresh():
            """Force an immediate scan of monitored folders"""
            try:
                response = requests.post(f"{ui.api_url}/folder-monitor/scan", timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        result = f"🔍 **Forced Scan Completed**\n\n"
                        result += f"📄 **Changes Detected:** {data.get('changes_detected', 0)}\n"
                        result += f"📊 **Files Tracked:** {data.get('files_tracked', 0)}\n"
                        result += f"📅 **Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        
                        # Check if there are failed files and offer retry
                        try:
                            status_response = requests.get(f"{ui.api_url}/folder-monitor/status", timeout=10)
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                if status_data.get('success'):
                                    status_info = status_data.get('status', {})
                                    failed_files = status_info.get('files_failed', 0)
                                    skipped_files = status_info.get('files_skipped', 0)
                                    
                                    if failed_files > 0:
                                        result += f"\n⚠️ **Note:** {failed_files} files failed processing. You can retry them using the 'Retry Failed Files' button.\n"
                                    if skipped_files > 0:
                                        result += f"\n✅ **Note:** {skipped_files} files were skipped (likely duplicates).\n"
                        except:
                            pass
                        
                        result += f"\n💡 **Note:** Check file status for detailed processing results."
                    else:
                        result = f"❌ **Scan Failed:** {data.get('error', 'Unknown error')}"
                else:
                    result = f"❌ **HTTP Error:** {response.status_code}"
            except Exception as e:
                result = f"❌ **Error:** {str(e)}"
            
            # Also refresh status
            status = ui.get_monitoring_status()
            file_status = ui.get_detailed_file_status()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return result, status, file_status, registry, gr.update(choices=safe_choices, value=None)
        
        def retry_failed_files_and_refresh():
            """Retry failed file ingestion"""
            try:
                response = requests.post(f"{ui.api_url}/folder-monitor/retry", timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        result = f"🔄 **Retry Completed**\n\n"
                        result += f"📄 **Files Reset:** {data.get('files_reset', 0)}\n"
                        result += f"📅 **Retry Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        result += f"\n💡 **Note:** Failed files have been reset to pending status and will be processed automatically."
                    else:
                        result = f"❌ **Retry Failed:** {data.get('error', 'Unknown error')}"
                elif response.status_code == 404:
                    result = f"❌ **Retry Endpoint Not Available**\n\nThe retry functionality requires a server restart to be available."
                else:
                    result = f"❌ **HTTP Error:** {response.status_code}"
            except Exception as e:
                result = f"❌ **Error:** {str(e)}"
            
            # Also refresh status
            status = ui.get_monitoring_status()
            file_status = ui.get_detailed_file_status()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return result, status, file_status, registry, gr.update(choices=safe_choices, value=None)
        
        def refresh_file_status():
            """Refresh detailed file status"""
            file_status = ui.get_detailed_file_status()
            return file_status
        
        def refresh_all_monitoring_info():
            """Refresh all monitoring information for auto-refresh"""
            status = ui.get_monitoring_status()
            file_status = ui.get_detailed_file_status()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return status, file_status, registry, gr.update(choices=safe_choices, value=None)
        
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
        
        force_scan_btn.click(
            fn=force_scan_and_refresh,
            outputs=[monitor_result, monitor_status_display, file_status_display, document_registry_display, delete_doc_path_input]
        )
        
        retry_failed_btn.click(
            fn=retry_failed_files_and_refresh,
            outputs=[monitor_result, monitor_status_display, file_status_display, document_registry_display, delete_doc_path_input]
        )
        
        refresh_files_btn.click(
            fn=refresh_file_status,
            outputs=[file_status_display]
        )
        
        # Auto-refresh functionality with performance safeguards
        # Increased interval to 60 seconds and added safety mechanisms
        auto_refresh_timer = gr.Timer(60, active=False)  # 60 second timer, DISABLED by default
        
        # Performance tracking variables
        auto_refresh_state = {
            'last_refresh_time': 0,
            'consecutive_failures': 0,
            'max_failures': 3,
            'min_interval': 30,  # Minimum 30 seconds between refreshes
            'is_refreshing': False
        }
        
        def toggle_auto_refresh(enabled):
            """Toggle auto-refresh with safety checks"""
            if enabled:
                # Reset failure counter when enabling
                auto_refresh_state['consecutive_failures'] = 0
                auto_refresh_state['last_refresh_time'] = 0
                print("[INFO] Auto-refresh enabled with safety mechanisms")
                return gr.update(active=True)
            else:
                print("[INFO] Auto-refresh disabled")
                return gr.update(active=False)
        
        def safe_refresh_all_monitoring_info():
            """Safely refresh all monitoring information with performance safeguards"""
            import time
            current_time = time.time()
            
            # Check if we're already refreshing
            if auto_refresh_state['is_refreshing']:
                print("[WARNING] Auto-refresh skipped - previous refresh still in progress")
                return None, None, None, None
            
            # Check minimum interval
            if current_time - auto_refresh_state['last_refresh_time'] < auto_refresh_state['min_interval']:
                print("[WARNING] Auto-refresh skipped - too soon since last refresh")
                return None, None, None, None
            
            # Check failure threshold
            if auto_refresh_state['consecutive_failures'] >= auto_refresh_state['max_failures']:
                print(f"[WARNING] Auto-refresh disabled due to {auto_refresh_state['consecutive_failures']} consecutive failures")
                # Disable the timer
                auto_refresh_timer.update(active=False)
                return None, None, None, None
            
            try:
                # Set refreshing flag
                auto_refresh_state['is_refreshing'] = True
                auto_refresh_state['last_refresh_time'] = current_time
                
                print("[DEBUG] Starting auto-refresh cycle")
                
                # Perform the refresh with timeout protection
                status = ui.get_monitoring_status()
                file_status = ui.get_detailed_file_status()
                registry = ui._format_document_registry()
                dropdown_choices = ui.get_document_paths()
                
                # Ensure dropdown_choices is a proper list of strings
                if not isinstance(dropdown_choices, list):
                    dropdown_choices = ["(No documents uploaded yet)"]
                
                safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
                if not safe_choices:
                    safe_choices = ["(No documents uploaded yet)"]
                
                # Reset failure counter on success
                auto_refresh_state['consecutive_failures'] = 0
                print("[DEBUG] Auto-refresh completed successfully")
                
                return status, file_status, registry, gr.update(choices=safe_choices, value=None)
                
            except Exception as e:
                # Increment failure counter
                auto_refresh_state['consecutive_failures'] += 1
                print(f"[ERROR] Auto-refresh failed (attempt {auto_refresh_state['consecutive_failures']}): {str(e)}")
                
                # If we've hit the failure threshold, disable auto-refresh
                if auto_refresh_state['consecutive_failures'] >= auto_refresh_state['max_failures']:
                    print(f"[CRITICAL] Auto-refresh disabled after {auto_refresh_state['max_failures']} consecutive failures")
                    # Return None to indicate no update needed
                    return None, None, None, None
                
                # Return current values to avoid breaking the UI
                return None, None, None, None
                
            finally:
                # Always clear the refreshing flag
                auto_refresh_state['is_refreshing'] = False
        
        auto_refresh_checkbox.change(
            fn=toggle_auto_refresh,
            inputs=[auto_refresh_checkbox],
            outputs=[auto_refresh_timer]
        )
        
        auto_refresh_timer.tick(
            fn=safe_refresh_all_monitoring_info,
            outputs=[monitor_status_display, file_status_display, document_registry_display, delete_doc_path_input]
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
        
        def sync_config_and_refresh():
            """Sync configuration with backend and refresh displays"""
            sync_result = ui.sync_config_with_backend()
            status = ui.get_monitoring_status()
            file_status = ui.get_detailed_file_status()
            display_text, folder_list = ui.get_monitored_folders()
            
            return (
                sync_result,
                status,
                file_status,
                display_text,
                gr.update(choices=folder_list, value=None, visible=len(folder_list) > 0),
                gr.update(visible=len(folder_list) > 0)
            )
        
        sync_config_btn.click(
            fn=sync_config_and_refresh,
            outputs=[monitor_result, monitor_status_display, file_status_display, monitored_folders_display, folder_selector, remove_folder_btn]
        )
        
        def show_file_type_details():
            """Show detailed file type information"""
            detailed_info = ui.get_supported_file_types_info()
            return (
                detailed_info,
                gr.update(visible=False),  # Hide show button
                gr.update(visible=True)    # Show hide button
            )
        
        def hide_file_type_details():
            """Hide detailed file type information and show summary"""
            summary_info = """
            - 📄 **Text files**: .txt, .md
            - 📊 **Data files**: .json, .csv
            - 📖 **PDF Documents**: .pdf
            - 📝 **Word Documents**: .docx, .doc
            - 📊 **Excel files**: .xlsx, .xls, .xlsm, .xlsb
            - 🎯 **PowerPoint**: .pptx, .ppt
            - 🖼️ **Images**: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .tif, .webp, .svg
            - 📐 **Visio Diagrams**: .vsdx, .vsd, .vsdm, .vstx, .vst, .vstm
            
            *Click "Show Details" for comprehensive file type information*
            """
            return (
                summary_info,
                gr.update(visible=True),   # Show show button
                gr.update(visible=False)   # Hide hide button
            )
        
        show_file_types_btn.click(
            fn=show_file_type_details,
            outputs=[file_types_display, show_file_types_btn, hide_file_types_btn]
        )
        
        hide_file_types_btn.click(
            fn=hide_file_type_details,
            outputs=[file_types_display, show_file_types_btn, hide_file_types_btn]
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
        
        def discover_docs_and_refresh():
            discovery_result = ui.discover_documents_via_search()
            registry = ui._format_document_registry()
            dropdown_choices = ui.get_document_paths()
            
            # Ensure dropdown_choices is a proper list of strings
            if not isinstance(dropdown_choices, list):
                dropdown_choices = ["(No documents uploaded yet)"]
            
            safe_choices = [str(choice) for choice in dropdown_choices if choice is not None]
            if not safe_choices:
                safe_choices = ["(No documents uploaded yet)"]
            
            return discovery_result, registry, gr.update(choices=safe_choices, value=None)
        
        discover_docs_btn.click(
            fn=discover_docs_and_refresh,
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
        
        # Enhanced conversation event handlers for ChatGPT-style interface
        def auto_start_conversation():
            """Auto-start a new conversation when page loads"""
            # Add protection against multiple calls during initialization
            import time
            current_time = time.time()
            if hasattr(auto_start_conversation, '_last_call'):
                time_diff = current_time - auto_start_conversation._last_call
                if time_diff < 2.0:  # Prevent calls more frequent than 2 seconds
                    print(f"DEBUG: auto_start_conversation throttled (last call {time_diff:.2f}s ago)")
                    return [], "", "Initialization in progress...", gr.update(), "", "", "", "", {"throttled": True}, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), *([gr.update(value="", visible=False)] * 10)
            auto_start_conversation._last_call = current_time
            
            print("DEBUG: Starting auto_start_conversation...")
            history, thread_id, status = ui.auto_start_new_conversation()
            print(f"DEBUG: New conversation - Thread ID: {thread_id}, Status: {status}")
            
            # Load conversation history for dropdown
            print("DEBUG: Loading conversation history...")
            history_choices = ui.get_conversation_history()
            print(f"DEBUG: Got {len(history_choices)} history choices")
            
            if history_choices:
                formatted_choices = [f"{title} ({tid[:8]})" for tid, title in history_choices]
                history_dropdown_update = gr.update(choices=formatted_choices, value=None)
                print(f"DEBUG: Formatted history choices: {formatted_choices}")
            else:
                history_dropdown_update = gr.update(choices=["(No previous conversations)"], value=None)
                print("DEBUG: No history found, showing empty message")
            
            # Clear all suggestion elements
            suggestion_updates = [
                gr.update(value="", visible=False) for _ in range(4)  # suggestion buttons
            ]
            topic_updates = [
                gr.update(value="", visible=False) for _ in range(6)  # topic chips
            ]
            
            print("DEBUG: Returning auto_start_conversation results")
            return (
                history, thread_id, status,
                history_dropdown_update,  # Populate history dropdown
                "", "", "", "",  # Clear insights, interaction hints, entity exploration, technical terms
                {"conversation_started": True}, # Clear debug info with valid dict
                gr.update(visible=False),  # Hide suggestions group
                gr.update(visible=False),  # Hide topics group
                gr.update(visible=False),  # Hide insights container
            ) + tuple(suggestion_updates) + tuple(topic_updates)
        
        def start_new_chat():
            """Start a new conversation manually"""
            history, thread_id, status = ui.start_new_conversation()
            
            # Refresh history dropdown
            history_choices = ui.get_conversation_history()
            formatted_choices = [f"{title} ({thread_id[:8]})" for thread_id, title in history_choices]
            
            # Clear all suggestion elements
            suggestion_updates = [
                gr.update(value="", visible=False) for _ in range(4)
            ]
            topic_updates = [
                gr.update(value="", visible=False) for _ in range(6)
            ]
            
            return (
                history, thread_id, status,
                gr.update(choices=formatted_choices, value=None),  # Update history dropdown
                "", "", "", "",  # Clear insights, interaction hints, entity exploration, technical terms
                {"new_chat_started": True},  # Clear debug info with valid dict
                gr.update(visible=False),  # Hide suggestions group
                gr.update(visible=False),  # Hide topics group
                gr.update(visible=False),  # Hide insights container
            ) + tuple(suggestion_updates) + tuple(topic_updates)
        
        def refresh_chat_history():
            """Refresh the chat history dropdown"""
            print("DEBUG: Refreshing chat history...")
            history_choices = ui.get_conversation_history()
            print(f"DEBUG: Got {len(history_choices)} history choices")
            
            if history_choices:
                formatted_choices = [f"{title} ({thread_id[:8]})" for thread_id, title in history_choices]
                print(f"DEBUG: Formatted choices: {formatted_choices}")
                return gr.update(choices=formatted_choices, value=None)
            else:
                print("DEBUG: No history choices found, returning empty dropdown")
                return gr.update(choices=["(No previous conversations)"], value=None)
        
        def load_selected_chat(selected_chat):
            """Load a selected chat from history"""
            if not selected_chat:
                return [], "", "No chat selected", gr.update()
            
            # Extract thread_id from formatted string
            thread_id = selected_chat.split("(")[-1].rstrip(")")
            history, loaded_thread_id, status = ui.load_conversation_thread(thread_id)
            
            return history, loaded_thread_id, status, gr.update()
        
        def delete_selected_chat(selected_chat):
            """Delete a selected chat from history"""
            if not selected_chat:
                return "No chat selected", gr.update()
            
            # Extract thread_id from formatted string
            thread_id = selected_chat.split("(")[-1].rstrip(")")
            delete_status = ui.delete_conversation_thread(thread_id)
            
            # Refresh history dropdown
            history_choices = ui.get_conversation_history()
            formatted_choices = [f"{title} ({thread_id[:8]})" for thread_id, title in history_choices]
            
            return delete_status, gr.update(choices=formatted_choices, value=None)
        
        def send_message_and_update(message, thread_id, history, use_streaming=True, show_suggestions=True, show_topics=True, show_insights=False):
            """Send message and update conversation with enhanced suggestions (streaming or regular)"""
            try:
                if use_streaming:
                    message_cleared, updated_history, status, enhanced_data = ui.send_conversation_message_stream(message, thread_id, history)
                else:
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
            
            # Update suggestion buttons with error handling
            suggestions = enhanced_data.get('suggestions', [])
            suggestion_updates = []
            suggestions_visible = show_suggestions and len(suggestions) > 0
            
            for i in range(4):
                if i < len(suggestions) and show_suggestions:
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
            
            # Control visibility based on settings
            suggestions_group_visible = show_suggestions and suggestions_visible
            topics_group_visible = show_topics and len(topics) > 0
            insights_container_visible = show_insights and (insights_text or entities_text or terms_text or hints_text)
            
            # Ensure enhanced_data is always a valid dict for JSON component
            if not isinstance(enhanced_data, dict):
                enhanced_data = {"debug_info": str(enhanced_data), "message_processed": True}
            
            return (
                message_cleared,  # Clear message input
                updated_history,  # Updated chat history
                status,  # Status message
                enhanced_data,  # Debug info (always a valid dict)
                gr.update(visible=suggestions_group_visible),  # Suggestions group visibility
                gr.update(visible=topics_group_visible),  # Topics group visibility
                gr.update(visible=insights_container_visible),  # Insights container visibility
                gr.update(value=insights_text, visible=bool(insights_text and show_insights)),  # Conversation insights
                gr.update(value=hints_text, visible=bool(hints_text and show_insights)),  # Interaction hints
                gr.update(value=entities_text, visible=bool(entities_text and show_insights)),  # Entity exploration
                gr.update(value=terms_text, visible=bool(terms_text and show_insights)),  # Technical terms
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
                {"conversation_ended": True}  # Clear debug info with valid dict
            ) + tuple(suggestion_updates) + tuple(topic_updates)
        
        def handle_suggestion_click(suggestion_text, thread_id, history):
            """Handle suggestion button click"""
            if not suggestion_text or not suggestion_text.strip():
                return "", history, "No suggestion selected", {"status": "no_suggestion"}
            
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
                debug_data = full_response[3] if len(full_response) > 3 else {"suggestion_processed": True}
                
                # Ensure debug_data is always a valid dict
                if not isinstance(debug_data, dict):
                    debug_data = {"debug_info": str(debug_data), "suggestion_processed": True}
                
                return message_cleared, updated_history, status, debug_data
            except Exception as e:
                return "", history, f"Error: {str(e)}", {"error": str(e), "suggestion_failed": True}
        
        def handle_topic_click(topic_text, thread_id, history):
            """Handle topic chip click"""
            if not topic_text or not topic_text.strip():
                return "", history, "No topic selected", {"status": "no_topic"}
            
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
                debug_data = full_response[3] if len(full_response) > 3 else {"topic_processed": True}
                
                # Ensure debug_data is always a valid dict
                if not isinstance(debug_data, dict):
                    debug_data = {"debug_info": str(debug_data), "topic_processed": True}
                
                return message_cleared, updated_history, status, debug_data
            except Exception as e:
                return "", history, f"Error: {str(e)}", {"error": str(e), "topic_failed": True}
        
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
                {"suggestions_cleared": True}  # Clear debug info with valid dict
            ) + tuple(suggestion_updates) + tuple(topic_updates)

        # Pipeline Verification Event Handlers
        def validate_file_and_update(file_path):
            """Validate file for verification"""
            if not file_path:
                return "📋 Please select a file first", "{}"
            
            status, details = ui.validate_file_for_verification(file_path)
            return status, details

        def test_extraction_and_update(file_path):
            """Test content extraction"""
            if not file_path:
                return "🔧 Please select a file first", "{}"
            
            status, details = ui.test_content_extraction(file_path)
            return status, details

        def test_chunking_and_update(text, method):
            """Test chunking methods"""
            if not text or not text.strip():
                return "📝 Please enter text to chunk", "{}"
            
            status, details = ui.test_chunking_methods(text, method)
            return status, details

        def full_verification_and_update(file_path, metadata_str):
            """Run full pipeline verification"""
            if not file_path:
                return "✅ Please select a file first", "", "{}"
            
            # Parse metadata if provided
            metadata = None
            if metadata_str and metadata_str.strip():
                try:
                    import json
                    metadata = json.loads(metadata_str)
                except json.JSONDecodeError:
                    return "❌ Invalid JSON in metadata field", "", "{}"
            
            status, report, raw_details = ui.ingest_with_verification(file_path, metadata)
            return status, report, raw_details

        def open_dashboard():
            """Open verification dashboard in new tab"""
            import webbrowser
            try:
                webbrowser.open(ui.get_verification_dashboard_url())
                return "🚀 Dashboard opened in new tab"
            except Exception as e:
                return f"❌ Error opening dashboard: {str(e)}"

        def refresh_pipeline_health():
            """Refresh pipeline health status"""
            return ui.get_pipeline_health_status()

        def refresh_pipeline_stages():
            """Refresh pipeline stages status"""
            return ui.get_pipeline_stage_status()

        def refresh_sessions():
            """Refresh verification sessions"""
            sessions_display, sessions_raw = ui.get_verification_sessions()
            return sessions_display, sessions_raw

        def get_session_details_and_update(session_id):
            """Get session details"""
            if not session_id or not session_id.strip():
                return "🔍 Please enter a session ID", "{}"
            
            details_display, details_raw = ui.get_session_details(session_id.strip())
            return details_display, details_raw

        def show_warnings_guide():
            """Show pipeline warnings and troubleshooting guide"""
            return ui.explain_pipeline_warnings()
        
        # ChatGPT-style conversation event handlers
        

        
        # New chat button
        new_chat_btn.click(
            fn=start_new_chat,
            outputs=[
                chatbot, thread_id_display, conversation_status, chat_history_dropdown,
                conversation_insights, interaction_hints, entity_exploration, technical_terms,
                debug_info, suggestions_group, topics_group, insights_container,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
        )
        
        # Chat history management
        refresh_history_btn.click(
            fn=refresh_chat_history,
            outputs=[chat_history_dropdown]
        )
        
        load_chat_btn.click(
            fn=load_selected_chat,
            inputs=[chat_history_dropdown],
            outputs=[chatbot, thread_id_display, conversation_status, chat_history_dropdown]
        )
        
        delete_chat_btn.click(
            fn=delete_selected_chat,
            inputs=[chat_history_dropdown],
            outputs=[conversation_status, chat_history_dropdown]
        )
        
        # Message sending with enhanced controls
        def send_with_controls(message, thread_id, history, streaming, show_suggestions, show_topics, show_insights):
            return send_message_and_update(message, thread_id, history, streaming, show_suggestions, show_topics, show_insights)
        
        send_button.click(
            fn=send_with_controls,
            inputs=[message_input, thread_id_display, chatbot, streaming_toggle, show_suggestions_toggle, show_topics_toggle, show_insights_toggle],
            outputs=[
                message_input, chatbot, conversation_status, debug_info,
                suggestions_group, topics_group, insights_container,
                conversation_insights, interaction_hints, entity_exploration, technical_terms,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
        )
        
        message_input.submit(
            fn=send_with_controls,
            inputs=[message_input, thread_id_display, chatbot, streaming_toggle, show_suggestions_toggle, show_topics_toggle, show_insights_toggle],
            outputs=[
                message_input, chatbot, conversation_status, debug_info,
                suggestions_group, topics_group, insights_container,
                conversation_insights, interaction_hints, entity_exploration, technical_terms,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
        )
        
        # Checkbox controls for visibility
        show_insights_toggle.change(
            fn=lambda show: gr.update(visible=show),
            inputs=[show_insights_toggle],
            outputs=[insights_container]
        )
        
        show_insights_toggle.change(
            fn=lambda show: gr.update(visible=show),
            inputs=[show_insights_toggle],
            outputs=[debug_accordion]
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

        # Pipeline Verification Tab Event Handlers
        validate_file_btn.click(
            fn=validate_file_and_update,
            inputs=[validate_file_input],
            outputs=[validation_status, validation_details]
        )
        
        test_extraction_btn.click(
            fn=test_extraction_and_update,
            inputs=[extract_file_input],
            outputs=[extraction_status, extraction_details]
        )
        
        test_chunking_btn.click(
            fn=test_chunking_and_update,
            inputs=[chunking_text_input, chunking_method_dropdown],
            outputs=[chunking_status, chunking_details]
        )
        
        full_verify_btn.click(
            fn=full_verification_and_update,
            inputs=[verify_file_input, verify_metadata_input],
            outputs=[verification_status, verification_report, verification_raw]
        )
        
        open_dashboard_btn.click(
            fn=open_dashboard,
            outputs=[]
        )
        
        # Enhanced Pipeline Verification Event Handlers
        pipeline_health_btn.click(
            fn=refresh_pipeline_health,
            outputs=[pipeline_health_status]
        )
        
        pipeline_stages_btn.click(
            fn=refresh_pipeline_stages,
            outputs=[pipeline_stages_status]
        )
        
        sessions_refresh_btn.click(
            fn=refresh_sessions,
            outputs=[sessions_display, sessions_raw]
        )
        
        session_details_btn.click(
            fn=get_session_details_and_update,
            inputs=[session_id_input],
            outputs=[session_details_display, session_details_raw]
        )
        
        warnings_guide_btn.click(
            fn=show_warnings_guide,
            outputs=[warnings_guide_display]
        )

        # Vector Management Tab Event Handlers
        vectors_browse_btn.click(
            fn=ui.get_vectors_paginated,
            inputs=[vectors_page_input, vectors_page_size_input, vectors_include_content_checkbox, 
                    vectors_doc_filter_input, vectors_source_filter_input],
            outputs=[vectors_display]
        )
        
        vector_details_btn.click(
            fn=ui.get_vector_details,
            inputs=[vector_id_input, vector_include_embedding_checkbox],
            outputs=[vector_details_display]
        )
        
        vector_search_btn.click(
            fn=ui.search_vectors_advanced,
            inputs=[search_query_input, search_k_input, search_threshold_input, search_doc_filter_input],
            outputs=[vector_search_display]
        )

        # Performance Monitoring Tab Event Handlers
        query_analytics_btn.click(
            fn=ui.get_query_performance_metrics,
            inputs=[perf_time_range_input, perf_limit_input],
            outputs=[query_analytics_display]
        )
        
        performance_test_btn.click(
            fn=ui.test_query_performance,
            inputs=[test_query_input, test_max_results_input],
            outputs=[performance_test_display]
        )
        
        system_monitor_btn.click(
            fn=ui.get_system_performance,
            outputs=[system_performance_display]
        )

        # Initialize connection status and auto-start conversation on load
        def initialize_interface():
            """Initialize the interface with connection check and auto-start conversation"""
            # Check connection
            connection_result = ui.check_api_connection()
            
            # Auto-start conversation
            conversation_results = auto_start_conversation()
            
            # Return connection status + conversation initialization results
            return (connection_result,) + conversation_results
        
        interface.load(
            fn=initialize_interface,
            outputs=[
                connection_status,
                chatbot, thread_id_display, conversation_status, chat_history_dropdown,
                conversation_insights, interaction_hints, entity_exploration, technical_terms,
                debug_info, suggestions_group, topics_group, insights_container,
                suggestion_btn_1, suggestion_btn_2, suggestion_btn_3, suggestion_btn_4,
                topic_chip_1, topic_chip_2, topic_chip_3, topic_chip_4, topic_chip_5, topic_chip_6
            ]
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