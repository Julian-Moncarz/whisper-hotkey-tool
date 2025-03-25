#!/usr/bin/env python3
import sys
import platform
import subprocess
import pkg_resources

def check_environment():
    """Verify the development environment is correctly set up."""
    print("Environment Test Results:")
    print("-----------------------")
    
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")
    version_parts = python_version.split('.')
    major, minor = int(version_parts[0]), int(version_parts[1])
    
    if major != 3 or minor < 8 or minor > 9:
        print("⚠️ WARNING: Python version should be 3.8 or 3.9 for best PyTorch compatibility")
    else:
        print("✅ Python version is compatible")
    
    # Check OS version
    mac_os_version = platform.mac_ver()[0]
    print(f"macOS version: {mac_os_version}")
    if mac_os_version == '':
        print("❌ Not running on macOS")
        return False
    else:
        print("✅ Running on macOS")
    
    # Check if running in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    print(f"Virtual environment: {'✅ Active' if in_venv else '❌ Not active'}")
    
    # Check Homebrew
    try:
        brew_version = subprocess.check_output(['brew', '--version']).decode().strip().split('\n')[0]
        print(f"Homebrew: {brew_version}")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ Homebrew not found")
        return False
    
    return True

if __name__ == "__main__":
    if check_environment():
        print("\nEnvironment setup successful! ✨")
    else:
        print("\nEnvironment setup incomplete. Please address the issues above.")
        sys.exit(1)
