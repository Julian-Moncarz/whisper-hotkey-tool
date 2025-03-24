#!/usr/bin/env python3
import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
with patch('AppKit.NSEvent') as mock_nsevent, \
     patch('AppKit.NSApplication') as mock_nsapp:
    from src.whisper_hotkey.utils.hotkey_manager import HotkeyManager

class TestHotkeyManager(unittest.TestCase):
    """Tests for the HotkeyManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.hotkey_manager = HotkeyManager()
    
    def tearDown(self):
        """Clean up after tests."""
        self.hotkey_manager.stop()
    
    def test_hotkey_parsing(self):
        """Test that hotkey strings are correctly parsed."""
        # Test valid hotkey strings
        key_code, modifiers = self.hotkey_manager._parse_hotkey_string("Command-Shift-R")
        self.assertEqual(key_code, self.hotkey_manager.KEY_CODES['r'])
        self.assertEqual(modifiers, self.hotkey_manager.MODIFIERS['Command'] | self.hotkey_manager.MODIFIERS['Shift'])
        
        # Test invalid hotkey string (no modifiers)
        with self.assertRaises(ValueError):
            self.hotkey_manager._parse_hotkey_string("R")
        
        # Test invalid hotkey string (unknown modifier)
        with self.assertRaises(ValueError):
            self.hotkey_manager._parse_hotkey_string("Super-R")
        
        # Test invalid hotkey string (unknown key)
        with self.assertRaises(ValueError):
            self.hotkey_manager._parse_hotkey_string("Command-F12")
    
    def test_register_unregister(self):
        """Test registering and unregistering hotkeys."""
        # Register a hotkey
        callback = lambda: None
        self.assertTrue(self.hotkey_manager.register_hotkey("Command-Shift-R", callback))
        
        # Key should be in the dictionary
        self.assertIn("Command-Shift-R", self.hotkey_manager.hotkeys)
        
        # Unregister the hotkey
        self.assertTrue(self.hotkey_manager.unregister_hotkey("Command-Shift-R"))
        
        # Key should be removed from the dictionary
        self.assertNotIn("Command-Shift-R", self.hotkey_manager.hotkeys)
        
        # Unregistering again should fail
        self.assertFalse(self.hotkey_manager.unregister_hotkey("Command-Shift-R"))
    
    @patch('threading.Thread')
    def test_start_stop(self, mock_thread):
        """Test starting and stopping the hotkey manager."""
        # Mock thread to avoid actual threading
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Register a hotkey
        self.hotkey_manager.register_hotkey("Command-Shift-R", lambda: None)
        
        # Start the manager
        self.hotkey_manager.start()
        self.assertTrue(self.hotkey_manager.running)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Stop the manager
        self.hotkey_manager.stop()
        self.assertFalse(self.hotkey_manager.running)
        mock_thread_instance.join.assert_called_once()

if __name__ == "__main__":
    unittest.main()
