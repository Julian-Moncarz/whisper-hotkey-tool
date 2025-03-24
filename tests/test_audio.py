#!/usr/bin/env python3
import os
import sys
import time
import shutil
import tempfile
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Temporarily modify the RECORDINGS_DIR for testing
import src.whisper_hotkey.constants as constants
original_recordings_dir = constants.RECORDINGS_DIR
test_recordings_dir = os.path.join(tempfile.gettempdir(), "whisper_hotkey_test_recordings")
constants.RECORDINGS_DIR = test_recordings_dir

# Make sure the test directory exists
os.makedirs(test_recordings_dir, exist_ok=True)

# Import the module to test
from src.whisper_hotkey.utils.audio_recorder import AudioRecorder

class TestAudioRecorder(unittest.TestCase):
    """Tests for the AudioRecorder class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.recorder = AudioRecorder()
        self.callback_data = {
            "recording_started": False,
            "recording_stopped": False,
            "filename": None
        }
        
        # Set up callbacks
        self.recorder.on_recording_started = lambda: self._on_started()
        self.recorder.on_recording_stopped = lambda filename: self._on_stopped(filename)
    
    def tearDown(self):
        """Clean up after tests."""
        # Make sure recording is stopped
        if self.recorder.is_recording():
            self.recorder.stop_recording()
        
        # Remove the test recordings directory
        if os.path.exists(test_recordings_dir):
            shutil.rmtree(test_recordings_dir)
            
        # Restore original constant
        constants.RECORDINGS_DIR = original_recordings_dir
    
    def _on_started(self):
        """Callback for when recording starts."""
        self.callback_data["recording_started"] = True
    
    def _on_stopped(self, filename):
        """Callback for when recording stops."""
        self.callback_data["recording_stopped"] = True
        self.callback_data["filename"] = filename
    
    def test_start_stop_recording(self):
        """Test starting and stopping recording."""
        # Start recording
        result = self.recorder.start_recording()
        
        # Check if recording started successfully
        # This might fail if no audio input device is available
        if not result:
            self.skipTest("No audio input device available")
        
        # Check recording state
        self.assertTrue(self.recorder.is_recording())
        self.assertTrue(self.callback_data["recording_started"])
        
        # Record for a short time
        time.sleep(1)
        
        # Stop recording
        filename = self.recorder.stop_recording()
        
        # Check recording state
        self.assertFalse(self.recorder.is_recording())
        self.assertTrue(self.callback_data["recording_stopped"])
        self.assertEqual(self.callback_data["filename"], filename)
        
        # Verify that the file exists
        self.assertTrue(os.path.exists(filename))
        
        # Check file size (should be non-zero)
        self.assertGreater(os.path.getsize(filename), 0)
    
    def test_stop_when_not_recording(self):
        """Test stopping when not recording."""
        # Should return None
        self.assertIsNone(self.recorder.stop_recording())
    
    def test_start_when_already_recording(self):
        """Test starting when already recording."""
        # Start recording
        result = self.recorder.start_recording()
        
        # Check if recording started successfully
        if not result:
            self.skipTest("No audio input device available")
        
        # Try to start again (should return False)
        self.assertFalse(self.recorder.start_recording())
        
        # Clean up
        self.recorder.stop_recording()

if __name__ == "__main__":
    unittest.main()
