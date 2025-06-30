# ========== Quick Setup Script (setup_garden_project.py) ==========
#!/usr/bin/env python3
"""
Quick setup script for Chicago Garden Planner
Run this after creating the virtual environment and installing Django
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and print status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"   ✅ Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {description}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    print("🌱 Chicago Garden Planner - Quick Setup")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: No virtual environment detected!")
        print("   Please activate your virtual environment first:")
        print("   source garden_env/bin/activate  # or garden_env\\Scripts\\activate on Windows")
        return
    