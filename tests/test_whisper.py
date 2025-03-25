#!/usr/bin/env python3
import os
import sys
import time
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Temporarily modify the directories for testing
import src.whisper_hotkey.constants as constants
original_models_dir = constants.MODELS_DIR
test_models_dir = os.path.join(tempfile.gettempdir(), "whisper_hotkey_test_models")
constants.MODELS_DIR = test_models_dir

# Create test directories
os.makedirs(test_models_dir, exist_ok=True)

# Import the module to test
from src.whisper_hotkey.models.whisper_transcriber import WhisperTranscriber
from src.whisper_hotkey.utils.config_manager import ConfigManager

# Mock the WhisperModel class
mock_model = MagicMock()
mock_segments = [MagicMock(text="This is a test transcription")]
mock_info = MagicMock(duration=2.5, transcription_time=0.5)
mock_model.transcribe.return_value = (mock_segments, mock_info)

class MockWhisperModel:
    def __init__(self, model_name, device, compute_type, download_root):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root
        
    def transcribe(self, audio_file, beam_size=5, vad_filter=True, vad_parameters=None):
        return mock_segments, mock_info

@patch('src.whisper_hotkey.models.whisper_transcriber.WhisperModel', MockWhisperModel)
class TestWhisperTranscriber(unittest.TestCase):
    """Tests for the WhisperTranscriber class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a config manager with test settings
        self.config_manager = ConfigManager()
        
        # Create the transcriber
        self.transcriber = WhisperTranscriber(self.config_manager)
        
        # Reset mock
        mock_model.reset_mock()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the test directories
        if os.path.exists(test_models_dir):
            shutil.rmtree(test_models_dir)
            
        # Restore original constants
        constants.MODELS_DIR = original_models_dir
    
    def test_load_model(self):
        """Test loading a Whisper model."""
        # Set up a callback to know when the model is loaded
        model_loaded = [False]
        self.transcriber.on_model_loaded = lambda: model_loaded.__setitem__(0, True)
        
        # Load the model
        result = self.transcriber.load_model("base")
        self.assertTrue(result)
        
        # Wait for loading to complete
        start_time = time.time()
        while self.transcriber.is_loading and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Verify that the model was loaded with correct parameters
        self.assertEqual(self.transcriber.model.model_name, "base")
        self.assertEqual(self.transcriber.model.device, self.transcriber.device)
        self.assertEqual(self.transcriber.model.compute_type, self.transcriber.compute_type)
        self.assertEqual(self.transcriber.model.download_root, constants.MODELS_DIR)
        self.assertTrue(model_loaded[0])
    
    def test_invalid_model_name(self):
        """Test loading with an invalid model name."""
        result = self.transcriber.load_model("invalid_model")
        self.assertFalse(result)
    
    def test_transcribe_without_model(self):
        """Test transcribing without a loaded model."""
        # Since we're patching the actual model loading,
        # we need to simulate the model loading process
        self.transcriber.model = None
        self.transcriber.is_loading = True
        
        # Attempt to transcribe
        result = self.transcriber.transcribe("nonexistent_file.wav")
        
        # Should report an error
        self.assertIn("error", result)
        self.assertEqual(result["text"], "")
    
    def test_transcribe_nonexistent_file(self):
        """Test transcribing a non-existent file."""
        # Simulate a loaded model
        self.transcriber.model = MockWhisperModel("base", "cpu", "int8", constants.MODELS_DIR)
        self.transcriber.model_name = "base"
        self.transcriber.is_loading = False
        
        # Attempt to transcribe a non-existent file
        result = self.transcriber.transcribe("nonexistent_file.wav")
        
        # Should report an error
        self.assertIn("error", result)
        self.assertEqual(result["text"], "")
    
    @patch('os.path.exists', return_value=True)
    def test_transcribe_success(self, mock_exists):
        """Test successful transcription."""
        # Simulate a loaded model
        self.transcriber.model = MockWhisperModel("base", "cpu", "int8", constants.MODELS_DIR)
        self.transcriber.model_name = "base"
        self.transcriber.is_loading = False
        
        # Transcribe
        result = self.transcriber.transcribe("test_audio.wav")
        
        # Verify the result
        self.assertEqual(result["text"], "This is a test transcription")
        self.assertEqual(result["duration"], 2.5)
        self.assertIn("elapsed", result)
        
        # No need to verify call parameters since we're using the actual MockWhisperModel class
    
    @patch('os.path.exists', return_value=True)
    def test_transcribe_error(self, mock_exists):
        """Test error during transcription."""
        # Create a mock model that raises an exception
        error_model = MagicMock()
        error_model.transcribe.side_effect = Exception("Test error")
        
        # Simulate a loaded model
        self.transcriber.model = error_model
        self.transcriber.model_name = "base"
        self.transcriber.is_loading = False
        
        # Transcribe
        result = self.transcriber.transcribe("test_audio.wav")
        
        # Verify the error result
        self.assertIn("error", result)
        self.assertEqual(result["text"], "")

if __name__ == "__main__":
    unittest.main()
