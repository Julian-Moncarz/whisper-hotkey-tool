#!/usr/bin/env python3
import os
import sys
import unittest
import ast

class TestSetupScript(unittest.TestCase):
    """Tests for the setup.py script."""
    
    def test_setup_script_exists(self):
        """Test that the setup script exists."""
        # Get the path to setup.py
        setup_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../setup.py'))
        
        # Check if the file exists
        self.assertTrue(os.path.exists(setup_path), "setup.py file not found")
    
    def test_setup_script_contents(self):
        """Test that the setup script contains expected configuration."""
        # Get the path to setup.py
        setup_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../setup.py'))
        
        # Read the file content
        with open(setup_path, 'r') as f:
            content = f.read()
        
        # Check for key strings that should be in the setup.py file
        self.assertIn("APP = ['src/whisper_hotkey/main.py']", content)
        self.assertIn("'CFBundleName': 'Whisper Hotkey'", content)
        self.assertIn("'LSUIElement': True", content)  # Menu bar app
        self.assertIn("'whisper',", content)  # Whisper package
        self.assertIn("'torch',", content)  # PyTorch package
        
        # Check version presence
        self.assertIn("version='0.1.0'", content)
        
        # Check Python requirement
        self.assertIn("python_requires='>=3.8,<3.10'", content)

if __name__ == "__main__":
    unittest.main()
