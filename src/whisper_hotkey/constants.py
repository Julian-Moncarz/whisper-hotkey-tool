# src/whisper_hotkey/constants.py
"""
Constant values used throughout the application.
"""
import os
import pathlib

# Application info
APP_NAME = "Whisper Hotkey"
APP_VERSION = "0.1.0"
APP_AUTHOR = "User"  # Replace with your name

# Default configuration
DEFAULT_START_RECORDING_HOTKEY = "Control-R"
DEFAULT_STOP_RECORDING_HOTKEY = "Control-S"
DEFAULT_WHISPER_MODEL = "base"  # Options: "tiny", "base", "small", "medium", "large-v2"
DEFAULT_SPEED_FACTOR = 1.5  # Speed factor for audio processing
DEFAULT_INITIAL_PROMPT = ""  # Default initial prompt for Whisper transcription

# File paths
APP_DATA_DIR = os.path.join(
    os.path.expanduser("~/Library/Application Support"), 
    APP_NAME
)
MODELS_DIR = os.path.join(APP_DATA_DIR, "models")
RECORDINGS_DIR = os.path.join(APP_DATA_DIR, "recordings")
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
LOG_FILE = os.path.join(APP_DATA_DIR, "app.log")

# Audio recording settings
SAMPLE_RATE = 16000  # Hz, required by Whisper
CHANNELS = 1  # Mono recording
AUDIO_FORMAT = "wav"  # Audio format to save recordings

# UI settings
MENU_ICON_IDLE = None  # Will use a default icon (customize later)
MENU_ICON_RECORDING = None  # Will use a default icon (customize later)

# Create necessary directories if they don't exist
for directory in [APP_DATA_DIR, MODELS_DIR, RECORDINGS_DIR]:
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
