#!/usr/bin/env python3
import os
import sys
import json
import shutil
import tempfile
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Store original paths before importing constants
original_app_data_dir = os.path.join(
    os.path.expanduser("~/Library/Application Support"),
    "Whisper Hotkey"
)
original_config_file = os.path.join(original_app_data_dir, "config.json")

# Create test paths
test_app_data_dir = os.path.join(tempfile.gettempdir(), "whisper_hotkey_test")
test_config_file = os.path.join(test_app_data_dir, "config.json")

# Back up and remove the real config if it exists
has_backup = False
if os.path.exists(original_config_file):
    has_backup = True
    backup_config = os.path.join(tempfile.gettempdir(), "config.json.bak")
    shutil.copy2(original_config_file, backup_config)
    os.remove(original_config_file)

# Now import and modify constants
import src.whisper_hotkey.constants as constants
constants.APP_DATA_DIR = test_app_data_dir
constants.CONFIG_FILE = test_config_file

# Now import the modules to test
from src.whisper_hotkey.utils.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """Tests for the ConfigManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create temporary test directory
        os.makedirs(test_app_data_dir, exist_ok=True)
        
        # Remove any existing config file
        if os.path.exists(constants.CONFIG_FILE):
            os.remove(constants.CONFIG_FILE)
            
        self.config_manager = ConfigManager()
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove the test directory
        if os.path.exists(test_app_data_dir):
            shutil.rmtree(test_app_data_dir)
        
        # Restore original constants
        constants.APP_DATA_DIR = original_app_data_dir
        constants.CONFIG_FILE = original_config_file
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Restore the original config if it was backed up
        if has_backup:
            backup_config = os.path.join(tempfile.gettempdir(), "config.json.bak")
            if os.path.exists(backup_config):
                os.makedirs(original_app_data_dir, exist_ok=True)
                shutil.copy2(backup_config, original_config_file)
                os.remove(backup_config)
    
    def test_default_config(self):
        """Test that default configuration is loaded correctly."""
        # Remove any existing config file and directory
        if os.path.exists(test_app_data_dir):
            shutil.rmtree(test_app_data_dir)
            
        # Create the directory structure
        os.makedirs(test_app_data_dir)
            
        # Create a new config manager
        config_manager = ConfigManager()
        
        self.assertEqual(
            config_manager.get("start_recording_hotkey"),
            constants.DEFAULT_START_RECORDING_HOTKEY
        )
        self.assertEqual(
            config_manager.get("stop_recording_hotkey"),
            constants.DEFAULT_STOP_RECORDING_HOTKEY
        )
        self.assertEqual(
            config_manager.get("whisper_model"),
            constants.DEFAULT_WHISPER_MODEL
        )
        self.assertTrue(config_manager.is_first_run())
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        # Modify and save config
        test_hotkey = "Command-Shift-R"
        self.config_manager.set("start_recording_hotkey", test_hotkey)
        self.config_manager.set("whisper_model", "medium")
        
        # Create new instance which should load from the saved file
        new_config_manager = ConfigManager()
        
        # Verify loaded values
        self.assertEqual(new_config_manager.get("start_recording_hotkey"), test_hotkey)
        self.assertEqual(new_config_manager.get("whisper_model"), "medium")
    
    def test_first_run_flag(self):
        """Test first run flag functionality."""
        # Initially should be True
        self.assertTrue(self.config_manager.is_first_run())
        
        # Mark first run as complete
        self.config_manager.mark_first_run_complete()
        
        # Should now be False
        self.assertFalse(self.config_manager.is_first_run())
        
        # Create new instance to test persistence
        new_config_manager = ConfigManager()
        self.assertFalse(new_config_manager.is_first_run())

if __name__ == "__main__":
    unittest.main()
