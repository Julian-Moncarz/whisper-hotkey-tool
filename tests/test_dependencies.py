#!/usr/bin/env python3
import importlib
import sys

def check_dependencies():
    """Verify that all required dependencies are correctly installed."""
    required_modules = [
        "objc",  # PyObjC
        "Cocoa",  # pyobjc-framework-Cocoa
        "Carbon",  # pyobjc-framework-Carbon
        "Quartz",  # pyobjc-framework-Quartz
        "rumps",  # Menu bar framework
        "pyaudio",  # Audio recording
        "numpy",  # Numerical processing
        "soundfile",  # Audio file handling
        "torch",  # PyTorch
        "whisper",  # OpenAI Whisper
    ]

    missing_modules = []
    installed_modules = []

    print("Dependency Test Results:")
    print("-----------------------")

    for module_name in required_modules:
        try:
            # Attempt to import the module
            module = importlib.import_module(module_name)
            
            # Get module version if available
            version = getattr(module, "__version__", "unknown version")
            print(f"✅ {module_name} ({version})")
            installed_modules.append(module_name)
        except ImportError as e:
            print(f"❌ {module_name} - NOT FOUND")
            missing_modules.append(module_name)
        except Exception as e:
            print(f"⚠️ {module_name} - IMPORT ERROR: {str(e)}")
            missing_modules.append(module_name)

    # Check PyTorch CUDA availability if PyTorch is installed
    if "torch" in installed_modules:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            print(f"ℹ️ PyTorch CUDA: Available (device count: {torch.cuda.device_count()})")
        else:
            print(f"ℹ️ PyTorch CUDA: Not available (CPU only)")
    
    return len(missing_modules) == 0

if __name__ == "__main__":
    if check_dependencies():
        print("\nAll dependencies successfully installed! ✨")
    else:
        print("\nSome dependencies are missing. Please install them using:")
        print("pip install -r requirements.txt")
        sys.exit(1)
