#!/usr/bin/env python3
import os
import sys
import time
import unittest
from unittest.mock import MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from src.whisper_hotkey.utils.text_inserter import TextInserter, MacOSPlatform

class TestTextInserter(unittest.TestCase):
    """Tests for the TextInserter class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock platform
        self.mock_platform = MagicMock(spec=MacOSPlatform)
        self.mock_platform.is_available = True
        self.mock_platform.check_accessibility_permissions.return_value = True
        self.mock_platform.get_clipboard_text.return_value = "Original clipboard"
        self.mock_platform.set_clipboard_text.return_value = True
        self.mock_platform.send_keyboard_shortcut.return_value = True
        
        # Create the text inserter with the mock platform
        self.text_inserter = TextInserter(platform=self.mock_platform)
        
        # Reset callback tracking
        self.callback_called = False
        
        # Set up callback
        self.text_inserter.on_insertion_complete = self._on_insertion_complete
    
    def _on_insertion_complete(self):
        """Callback for when insertion is complete."""
        self.callback_called = True

    def test_insert_empty_text(self):
        """Test inserting empty text."""
        # Should return False for empty text
        self.assertFalse(self.text_inserter.insert_text(""))
        
        # Platform methods should not be called
        self.mock_platform.check_accessibility_permissions.assert_not_called()
        self.mock_platform.set_clipboard_text.assert_not_called()
        self.mock_platform.send_keyboard_shortcut.assert_not_called()
    
    def test_insert_text(self):
        """Test inserting text at the cursor position."""
        # Insert text
        result = self.text_inserter.insert_text("Test text")
        self.assertTrue(result)
        
        # Wait for insertion to complete
        start_time = time.time()
        while self.text_inserter.inserting and time.time() - start_time < 3:
            time.sleep(0.1)
        
        # Verify that the platform methods were called correctly
        self.mock_platform.check_accessibility_permissions.assert_called_once()
        self.mock_platform.get_clipboard_text.assert_called_once()
        
        # Check that set_clipboard_text was called at least once
        self.mock_platform.set_clipboard_text.assert_called()
        
        # Check the first call specifically
        args, _ = self.mock_platform.set_clipboard_text.call_args_list[0]
        self.assertEqual(args[0], "Test text")
        
        self.mock_platform.send_keyboard_shortcut.assert_called_with(0x09, with_command=True)
        
        # Platform's set_clipboard_text should be called twice: once to set the text and once to restore
        self.assertEqual(self.mock_platform.set_clipboard_text.call_count, 2)
        
        # Verify that the callback was called
        self.assertTrue(self.callback_called)
    
    def test_insert_without_permissions(self):
        """Test inserting text without accessibility permissions."""
        # Configure the mock to deny permissions
        self.mock_platform.check_accessibility_permissions.return_value = False
        
        # Insert text
        result = self.text_inserter.insert_text("Test text")
        self.assertTrue(result)
        
        # Wait for insertion to complete
        start_time = time.time()
        while self.text_inserter.inserting and time.time() - start_time < 3:
            time.sleep(0.1)
        
        # Verify that the platform methods were called correctly
        self.mock_platform.check_accessibility_permissions.assert_called_once()
        
        # Other methods should not be called when permissions are denied
        self.mock_platform.get_clipboard_text.assert_not_called()
        self.mock_platform.set_clipboard_text.assert_not_called()
        self.mock_platform.send_keyboard_shortcut.assert_not_called()
        
        # Callback should not be called
        self.assertFalse(self.callback_called)
    
    def test_insert_with_error(self):
        """Test error handling during text insertion."""
        # Configure the mock to raise an exception
        self.mock_platform.set_clipboard_text.side_effect = Exception("Test error")
        
        # Insert text
        result = self.text_inserter.insert_text("Test text")
        self.assertTrue(result)
        
        # Wait for insertion to complete
        start_time = time.time()
        while self.text_inserter.inserting and time.time() - start_time < 3:
            time.sleep(0.1)
        
        # Verify that the platform methods were called correctly
        self.mock_platform.check_accessibility_permissions.assert_called_once()
        self.mock_platform.get_clipboard_text.assert_called_once()
        
        # Verify that set_clipboard_text was called twice (once to set text, once to restore)
        self.assertEqual(self.mock_platform.set_clipboard_text.call_count, 2)
        
        # Verify the arguments of the calls
        calls = self.mock_platform.set_clipboard_text.call_args_list
        self.assertEqual(calls[0][0][0], "Test text")
        self.assertEqual(calls[1][0][0], "Original clipboard")
        
        # Other methods should not be called after the exception
        self.mock_platform.send_keyboard_shortcut.assert_not_called()
        
        # Callback should not be called
        self.assertFalse(self.callback_called)
    
    def test_platform_unavailable(self):
        """Test behavior when the platform is not available."""
        # Configure the mock to be unavailable
        self.mock_platform.is_available = False
        self.mock_platform.check_accessibility_permissions.return_value = False
        
        # Insert text
        result = self.text_inserter.insert_text("Test text")
        self.assertTrue(result)
        
        # Wait for insertion to complete
        start_time = time.time()
        while self.text_inserter.inserting and time.time() - start_time < 3:
            time.sleep(0.1)
        
        # Callback should not be called
        self.assertFalse(self.callback_called)

if __name__ == "__main__":
    unittest.main()
