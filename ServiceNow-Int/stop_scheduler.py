#!/usr/bin/env python3
"""
Stop ServiceNow Scheduler Script
Simple script to stop all running ServiceNow schedulers and related processes.
"""

import psutil
import os
import sys
import time

def find_scheduler_processes():
    """Find all processes that might be schedulers"""
    scheduler_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's a Python process running scheduler-related scripts
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline.lower() for keyword in [
                    'servicenow_scheduler', 'start_integration', 'backend_integration'
                ]):
                    scheduler_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return scheduler_processes

def stop_schedulers():
    """Stop all scheduler processes"""
    processes = find_scheduler_processes()
    
    if not processes:
        print("✅ No scheduler processes found running")
        return
    
    print(f"🔍 Found {len(processes)} scheduler process(es):")
    
    for proc in processes:
        try:
            cmdline = ' '.join(proc.cmdline())
            print(f"   PID {proc.pid}: {cmdline}")
            
            # Terminate the process
            proc.terminate()
            print(f"   ✅ Terminated PID {proc.pid}")
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"   ❌ Failed to terminate PID {proc.pid}: {e}")
    
    # Wait a moment for graceful shutdown
    time.sleep(2)
    
    # Force kill if still running
    remaining = find_scheduler_processes()
    if remaining:
        print("🔧 Force killing remaining processes...")
        for proc in remaining:
            try:
                proc.kill()
                print(f"   ✅ Force killed PID {proc.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"   ❌ Failed to force kill PID {proc.pid}: {e}")

def check_api_connections():
    """Check if there are still connections to the API"""
    connections = []
    for conn in psutil.net_connections():
        if conn.laddr and conn.laddr.port == 8000:
            connections.append(conn)
    
    if connections:
        print(f"⚠️  Still {len(connections)} connections to port 8000")
        print("   These should clear automatically in a few seconds")
    else:
        print("✅ No active connections to port 8000")

def main():
    """Main function"""
    print("🛑 ServiceNow Scheduler Stop Script")
    print("=" * 40)
    
    # Stop schedulers
    stop_schedulers()
    
    # Check connections
    print("\n🔍 Checking API connections...")
    check_api_connections()
    
    print("\n✅ Scheduler stop process completed")
    print("💡 To prevent auto-restart, check for:")
    print("   - Windows Task Scheduler entries")
    print("   - System services")
    print("   - Startup scripts")

if __name__ == "__main__":
    main() 