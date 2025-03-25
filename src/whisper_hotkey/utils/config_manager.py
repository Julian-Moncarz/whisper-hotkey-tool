# src/whisper_hotkey/utils/config_manager.py
"""
Manages application configuration settings.
"""
import json
import os
from typing import Dict, Any

from ..constants import (
    CONFIG_FILE,
    DEFAULT_START_RECORDING_HOTKEY,
    DEFAULT_STOP_RECORDING_HOTKEY,
    DEFAULT_WHISPER_MODEL
)

class ConfigManager:
    """Handles configuration loading, saving, and accessing."""
    
    def __init__(self):
        self.config = {
            "start_recording_hotkey": DEFAULT_START_RECORDING_HOTKEY,
            "stop_recording_hotkey": DEFAULT_STOP_RECORDING_HOTKEY,
            "whisper_model": DEFAULT_WHISPER_MODEL,
            "delete_recordings": False,
            "first_run": True
        }
        
        # Load existing config if available
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    # Update our config with loaded values
                    self.config.update(loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save to disk."""
        self.config[key] = value
        self.save_config()
    
    def is_first_run(self) -> bool:
        """Check if this is the first time the app is run."""
        return self.get("first_run", True)
    
    def mark_first_run_complete(self) -> None:
        """Mark that the first run setup has been completed."""
        self.set("first_run", False)
