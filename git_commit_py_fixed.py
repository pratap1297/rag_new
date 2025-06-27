#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Git Auto-Commit Script for Python Files - Fixed Version
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime
from typing import List, Tuple, Optional

class GitAutoCommit:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def log(self, message: str, is_error: bool = False):
        """Print log message"""
        if is_error:
            print(f"❌ {message}", file=sys.stderr)
        elif self.verbose:
            print(f"📍 {message}")
    
    def run_git_command(self, command: List[str], timeout: int = 30) -> Tuple[bool, str]:
        """Run a git command and return success status and output"""
        try:
            self.log(f"Running: git {' '.join(command)}")
            result = subprocess.run(
                ['git'] + command,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout
            )
            return True, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
        except Exception as e:
            return False, str(e)
    
    def get_changed_files(self, pattern: str = "*.py", include_untracked: bool = True) -> List[str]:
        """Get list of changed files matching pattern"""
        success, output = self.run_git_command(['status', '--porcelain'])
        if not success:
            self.log(f"Error getting git status: {output}", is_error=True)
            return []
        
        changed_files = []
        for line in output.split('\n'):
            if line.strip():
                status = line[:2]
                filename = line[3:].strip()
                
                # Check file pattern
                if pattern == "*.py" and not filename.endswith('.py'):
                    continue
                elif pattern != "*" and not filename.endswith(pattern.replace("*", "")):
                    continue
                
                # Check status
                is_modified = status[1] == 'M' or status[0] == 'M'
                is_new = status[1] == '?'
                is_added = status[0] == 'A'
                
                if is_modified or is_added or (is_new and include_untracked):
                    changed_files.append(filename)
        
        return changed_files
    
    def add_files(self, files: List[str]) -> bool:
        """Add files to git staging area"""
        if not files:
            return True
        
        success, output = self.run_git_command(['add'] + files)
        if not success:
            self.log(f"Error adding files: {output}", is_error=True)
            return False
        
        print(f"✓ Added {len(files)} file(s) to staging area")
        return True
    
    def commit_changes(self, message: str) -> bool:
        """Commit staged changes with better error handling"""
        # First check if there are any staged changes
        success, output = self.run_git_command(['diff', '--cached', '--name-only'])
        if not success:
            self.log(f"Error checking staged changes: {output}", is_error=True)
            return False
        
        if not output.strip():
            print("⚠️  No staged changes to commit")
            return True
        
        # Commit with timeout
        success, output = self.run_git_command(['commit', '-m', message], timeout=60)
        if not success:
            self.log(f"Error committing changes: {output}", is_error=True)
            return False
        
        print(f"✓ Committed changes: {message}")
        return True
    
    def push_changes(self, branch: Optional[str] = None, force: bool = False) -> bool:
        """Push changes to remote"""
        cmd = ['push']
        if force:
            cmd.append('--force-with-lease')
        
        if branch:
            cmd.extend(['origin', branch])
        
        success, output = self.run_git_command(cmd, timeout=120)
        if not success:
            self.log(f"Error pushing changes: {output}", is_error=True)
            return False
        
        print("✓ Pushed changes to remote")
        return True
    
    def get_current_branch(self) -> str:
        """Get current git branch name"""
        success, output = self.run_git_command(['branch', '--show-current'])
        return output if success else "main"
    
    def generate_commit_message(self, files: List[str]) -> str:
        """Generate automatic commit message based on changed files"""
        if len(files) == 1:
            file = files[0]
            parts = file.split('/')
            if 'src' in parts:
                idx = parts.index('src')
                relevant_parts = parts[idx+1:]
                module = '/'.join(relevant_parts[:-1]) if len(relevant_parts) > 1 else relevant_parts[0]
                return f"update: {module} - {parts[-1]}"
            return f"update: {file}"
        else:
            dirs = set()
            for file in files:
                dir_path = os.path.dirname(file)
                if dir_path:
                    dirs.add(dir_path.split('/')[-1])
            
            if len(dirs) == 1:
                return f"update: {list(dirs)[0]} module - {len(files)} files"
            elif len(dirs) <= 3:
                return f"update: {', '.join(sorted(dirs))} - {len(files)} files"
            else:
                return f"update: {len(files)} files across multiple modules"

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Git Auto-Commit Script - Fixed Version')
    parser.add_argument('-m', '--message', help='Commit message')
    parser.add_argument('-p', '--push', action='store_true', help='Push after commit')
    parser.add_argument('-f', '--force-push', action='store_true', help='Force push')
    parser.add_argument('-a', '--all', action='store_true', help='Include all file types, not just .py')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--no-untracked', action='store_true', help='Ignore untracked files')
    
    args = parser.parse_args()
    
    print("🔍 Git Auto-Commit Script - Fixed Version")
    print("-" * 50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Error: Not in a git repository!")
        sys.exit(1)
    
    # Initialize git handler
    git = GitAutoCommit(verbose=args.verbose)
    
    # Get changed files
    pattern = "*" if args.all else "*.py"
    changed_files = git.get_changed_files(pattern, not args.no_untracked)
    
    if not changed_files:
        print(f"✅ No changed {'files' if args.all else 'Python files'} found.")
        return
    
    print(f"\n📋 Found {len(changed_files)} changed file(s):")
    for i, file in enumerate(changed_files, 1):
        print(f"   {i}. {file}")
    
    # Ask for confirmation
    print(f"\n❓ Commit these {len(changed_files)} file(s)? (y/n): ", end="")
    try:
        if input().lower() != 'y':
            print("❌ Aborted.")
            return
    except KeyboardInterrupt:
        print("\n❌ Aborted by user.")
        return
    
    # Get commit message
    if args.message:
        commit_message = args.message
    else:
        print("\n📝 Enter commit message (or press Enter for auto-generated): ")
        try:
            commit_message = input().strip()
        except KeyboardInterrupt:
            print("\n❌ Aborted by user.")
            return
        
        if not commit_message:
            commit_message = git.generate_commit_message(changed_files)
            print(f"📝 Auto-generated message: {commit_message}")
    
    # Add files
    print("\n📦 Adding files to staging area...")
    if not git.add_files(changed_files):
        print("❌ Failed to add files. Aborting.")
        return
    
    # Commit
    print("\n💾 Committing changes...")
    if not git.commit_changes(commit_message):
        print("❌ Failed to commit changes. Aborting.")
        return
    
    # Push if requested
    if args.push or args.force_push:
        current_branch = git.get_current_branch()
        print(f"\n📤 Pushing to branch: {current_branch}")
        if not git.push_changes(current_branch, args.force_push):
            print("❌ Failed to push changes.")
            return
    else:
        print("\n💡 Tip: Use -p flag to auto-push changes")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
