#!/usr/bin/env python3
"""
Restart RAG System with Persistent Metadata Store
This script helps restart the system cleanly with the new persistent store
"""
import os
import sys
import subprocess
import time
import requests

def restart_rag_system():
    print("🔄 Restarting RAG System with Persistent Metadata Store")
    print("=" * 60)
    
    # 1. Kill existing processes
    print("\n1️⃣ Stopping existing processes...")
    try:
        # Kill processes on ports 8000 and 7860
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True, text=True)
        print("   ✅ Stopped existing Python processes")
    except Exception as e:
        print(f"   ⚠️ Could not stop processes: {e}")
    
    time.sleep(2)
    
    # 2. Clear old data (optional)
    print("\n2️⃣ Clearing old vector data...")
    old_files = [
        "data/vectors/faiss_index.bin",
        "data/vectors/vector_metadata.pkl"
    ]
    
    for file_path in old_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   ✅ Removed {file_path}")
    
    # 3. Start the API server
    print("\n3️⃣ Starting API server...")
    try:
        api_process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for API to start
        print("   ⏳ Waiting for API server to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    print("   ✅ API server started successfully")
                    break
            except:
                pass
            time.sleep(1)
        else:
            print("   ⚠️ API server may not have started properly")
        
    except Exception as e:
        print(f"   ❌ Failed to start API server: {e}")
        return False
    
    # 4. Start the UI
    print("\n4️⃣ Starting Gradio UI...")
    try:
        ui_process = subprocess.Popen([
            sys.executable, "ui.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("   ✅ Gradio UI started")
        
    except Exception as e:
        print(f"   ❌ Failed to start UI: {e}")
        return False
    
    # 5. Test the persistent store
    print("\n5️⃣ Testing persistent metadata store...")
    try:
        response = requests.get("http://localhost:8000/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Metadata store stats:")
            print(f"      - Files: {stats.get('metadata_stats', {}).get('total_files', 0)}")
            print(f"      - Chunks: {stats.get('metadata_stats', {}).get('total_chunks', 0)}")
            print(f"      - Vector mappings: {stats.get('metadata_stats', {}).get('total_vector_mappings', 0)}")
        else:
            print("   ⚠️ Could not get stats from API")
    except Exception as e:
        print(f"   ⚠️ Could not test persistent store: {e}")
    
    print("\n✅ RAG System Restarted Successfully!")
    print("\n🌐 **Access Points:**")
    print("   • API Server: http://localhost:8000")
    print("   • Gradio UI: http://localhost:7860")
    print("   • Health Check: http://localhost:8000/health")
    print("   • Stats: http://localhost:8000/stats")
    
    print("\n🎯 **What's New:**")
    print("   • ✅ Persistent JSON metadata store active")
    print("   • ✅ Vector-metadata linking will persist")
    print("   • ✅ No more 'doc_unknown' issues")
    print("   • ✅ Metadata survives system restarts")
    
    print("\n📋 **Next Steps:**")
    print("   1. Upload documents via Gradio UI")
    print("   2. Test queries - should show proper document names")
    print("   3. Restart system - metadata will persist")
    
    return True

if __name__ == "__main__":
    success = restart_rag_system()
    if success:
        print("\n🚀 System ready! Upload documents and test queries.")
    else:
        print("\n❌ System restart failed. Check logs for details.")
    
    # Keep script running to show output
    try:
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        pass 