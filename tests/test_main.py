#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from src.whisper_hotkey.main import main

class TestMainApp(unittest.TestCase):
    """Tests for the main application entry point."""
    
    @patch('src.whisper_hotkey.main.WhisperHotkeyApp')
    def test_main_success(self, mock_app_class):
        """Test successful execution of the main function."""
        # Set up mock
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app
        
        # Call the main function
        result = main()
        
        # Verify that the app was created and run
        mock_app_class.assert_called_once()
        mock_app.run.assert_called_once()
        
        # Verify the return code
        self.assertEqual(result, 0)
    
    @patch('src.whisper_hotkey.main.WhisperHotkeyApp')
    @patch('src.whisper_hotkey.main.rumps.alert')
    def test_main_error(self, mock_alert, mock_app_class):
        """Test error handling in the main function."""
        # Set up mock to raise an exception
        mock_app_class.side_effect = Exception("Test error")
        
        # Call the main function
        result = main()
        
        # Verify that an error alert was shown
        mock_alert.assert_called_once()
        
        # Verify the return code
        self.assertEqual(result, 1)

if __name__ == "__main__":
    unittest.main()
