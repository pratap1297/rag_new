#!/usr/bin/env python3
"""
Simple test UI to verify the monitoring start button fix
"""
import gradio as gr
import requests
import json
import os
from datetime import datetime

class SimpleMonitoringTest:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

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
                            else:
                                result += f"\n⚠️ **Note:** No folders are currently configured for monitoring.\n"
                                result += f"Use the folder input above to add folders to monitor.\n"
                    
                    result += f"\n💡 **Note:** Monitoring service is now active and will check for file changes every 30 seconds."
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    if "already running" in error_msg.lower():
                        return f"ℹ️ **Monitoring Already Running**\n\n🟢 The folder monitoring service is already active.\n\n💡 Use 'Refresh Status' to see current monitoring details."
                    else:
                        return f"❌ Failed to start monitoring: {error_msg}"
            else:
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    return f"❌ HTTP {response.status_code}: {error_detail}"
                except:
                    return f"❌ HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def add_folder_to_monitoring(self, folder_path: str) -> str:
        """Add a folder to monitoring"""
        if not folder_path or not folder_path.strip():
            return "❌ Please provide a valid folder path"
        
        folder_path = folder_path.strip()
        
        # Validate folder exists
        if not os.path.exists(folder_path):
            return f"❌ Folder does not exist: {folder_path}"
        
        if not os.path.isdir(folder_path):
            return f"❌ Path is not a directory: {folder_path}"
        
        try:
            # Add folder to monitoring
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
                    
                    return result
                else:
                    error_msg = data.get('error', 'Unknown error')
                    return f"❌ Failed to add folder: {error_msg}"
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
                    
                    # Show monitored folders
                    monitored_folders = status_data.get('monitored_folders', [])
                    if monitored_folders:
                        status_text += f"\n**📂 Monitored Folders:**\n"
                        for folder in monitored_folders:
                            status_text += f"- `{folder}`\n"
                    
                    return status_text
                else:
                    return f"❌ Failed to get status: {data.get('error', 'Unknown error')}"
            else:
                return f"❌ HTTP {response.status_code}: Cannot get monitoring status"
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


def create_test_interface():
    """Create simple test interface for monitoring"""
    ui = SimpleMonitoringTest()
    
    with gr.Blocks(title="Monitoring Start Button Test") as interface:
        gr.Markdown("# 🧪 Monitoring Start Button Test")
        gr.Markdown("This is a simple test to verify the monitoring start button fix works correctly.")
        
        with gr.Row():
            with gr.Column():
                folder_input = gr.Textbox(
                    label="📁 Folder Path (Optional)",
                    placeholder="Enter folder path to add, or leave empty to start service",
                    info="Test both scenarios: empty input (start service) and folder path (add folder)"
                )
                
                with gr.Row():
                    start_btn = gr.Button("🟢 Start/Resume Monitoring", variant="primary")
                    stop_btn = gr.Button("🛑 Stop Monitoring", variant="stop")
                    status_btn = gr.Button("🔄 Get Status", variant="secondary")
                
                result_display = gr.Markdown("Ready to test monitoring start button...")
            
            with gr.Column():
                status_display = gr.Markdown("Click 'Get Status' to see current monitoring status")
        
        # Event handlers
        def start_monitoring_test(folder_path):
            if folder_path and folder_path.strip():
                # Test adding folder
                result = ui.add_folder_to_monitoring(folder_path)
            else:
                # Test starting service
                result = ui.start_monitoring_service()
            
            status = ui.get_monitoring_status()
            return result, status
        
        def stop_monitoring_test():
            result = ui.stop_folder_monitoring()
            status = ui.get_monitoring_status()
            return result, status
        
        def get_status_test():
            status = ui.get_monitoring_status()
            return status
        
        start_btn.click(
            fn=start_monitoring_test,
            inputs=[folder_input],
            outputs=[result_display, status_display]
        )
        
        stop_btn.click(
            fn=stop_monitoring_test,
            outputs=[result_display, status_display]
        )
        
        status_btn.click(
            fn=get_status_test,
            outputs=[status_display]
        )
    
    return interface


def main():
    """Main function"""
    print("🧪 Starting Monitoring Start Button Test...")
    
    interface = create_test_interface()
    
    print("""
🧪 MONITORING START BUTTON TEST
==================================
🎯 Test Cases:
1. Leave folder input EMPTY and click "Start/Resume Monitoring"
   → Should start monitoring service
2. Enter a folder path and click "Start/Resume Monitoring"  
   → Should add folder to monitoring
3. Click "Stop Monitoring"
   → Should stop monitoring service
4. Click "Get Status"
   → Should show current status

🔧 This tests the fix for the stuck "Stopped" state issue
==================================
""")
    
    interface.launch(
        server_port=7870,
        share=False,
        show_error=True,
        inbrowser=True
    )


if __name__ == "__main__":
    main() 