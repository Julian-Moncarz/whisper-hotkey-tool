#!/usr/bin/env python3
import os
import sys
import json
import shutil
import tempfile
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Temporarily modify the APP_DATA_DIR for testing
import src.whisper_hotkey.constants as constants
original_app_data_dir = constants.APP_DATA_DIR
test_app_data_dir = os.path.join(tempfile.gettempdir(), "whisper_hotkey_test")
constants.APP_DATA_DIR = test_app_data_dir
constants.CONFIG_FILE = os.path.join(test_app_data_dir, "config.json")

# Now import the modules to test
from src.whisper_hotkey.utils.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """Tests for the ConfigManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create temporary test directory
        os.makedirs(test_app_data_dir, exist_ok=True)
        self.config_manager = ConfigManager()
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove the test directory
        if os.path.exists(test_app_data_dir):
            shutil.rmtree(test_app_data_dir)
        
        # Restore original constants
        constants.APP_DATA_DIR = original_app_data_dir
        constants.CONFIG_FILE = os.path.join(original_app_data_dir, "config.json")
    
    def test_default_config(self):
        """Test that default configuration is loaded correctly."""
        self.assertEqual(
            self.config_manager.get("start_recording_hotkey"),
            constants.DEFAULT_START_RECORDING_HOTKEY
        )
        self.assertEqual(
            self.config_manager.get("whisper_model"),
            constants.DEFAULT_WHISPER_MODEL
        )
        self.assertTrue(self.config_manager.is_first_run())
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        # Modify and save config
        test_hotkey = "Command-Option-R"
        self.config_manager.set("start_recording_hotkey", test_hotkey)
        self.config_manager.set("whisper_model", "medium")
        
        # Create new instance which should load from the saved file
        new_config_manager = ConfigManager()
        
        # Check that the new instance has the updated values
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
