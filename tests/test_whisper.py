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
        
    def transcribe(self, audio_file, beam_size=5, vad_filter=True, vad_parameters=None, initial_prompt=None):
        # Store the initial_prompt for test verification if needed
        self.last_initial_prompt = initial_prompt
        return mock_segments, mock_info

# Mock AudioSegment for testing
class MockAudioSegment:
    def __init__(self, raw_data=b"test_data", frame_rate=44100):
        self.raw_data = raw_data
        self.frame_rate = frame_rate
        self._length = 2000  # 2 seconds in milliseconds
    
    def __len__(self):
        return self._length
    
    @staticmethod
    def from_file(file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        return MockAudioSegment()
    
    def _spawn(self, raw_data, overrides=None):
        mock = MockAudioSegment(raw_data, overrides.get("frame_rate", self.frame_rate))
        # Make the sped up audio shorter to simulate speed up
        mock._length = int(self._length / (overrides.get("frame_rate", self.frame_rate) / self.frame_rate))
        return mock
    
    def export(self, out_file, format="wav"):
        with open(out_file, "wb") as f:
            f.write(self.raw_data)

@patch('src.whisper_hotkey.models.whisper_transcriber.WhisperModel', MockWhisperModel)
@patch('src.whisper_hotkey.models.whisper_transcriber.AudioSegment', MockAudioSegment)
class TestWhisperTranscriber(unittest.TestCase):
    """Tests for the WhisperTranscriber class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a config manager with test settings
        self.config_manager = MagicMock()
        self.config_manager.get.return_value = ""
        
        # Create the transcriber
        self.transcriber = WhisperTranscriber(self.config_manager)
        
        # Create a temporary test file
        self.test_audio_file = os.path.join(tempfile.gettempdir(), "test_audio.wav")
        with open(self.test_audio_file, "wb") as f:
            f.write(b"test audio data")
        
        # Reset mock
        mock_model.reset_mock()
        
        # Set up mock segments for transcription tests
        global mock_segments
        mock_segments = [MagicMock(text="This is a test transcription")]
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the test directories and files
        if os.path.exists(test_models_dir):
            shutil.rmtree(test_models_dir)
        if os.path.exists(self.test_audio_file):
            os.unlink(self.test_audio_file)
            
        # Clean up any remaining temporary files
        self.transcriber._cleanup_temp_files()
            
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
    
    def test_speed_up_audio(self):
        """Test audio speed-up functionality."""
        # Test successful speed-up
        output_file, success = self.transcriber._speed_up_audio(self.test_audio_file, 1.5)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_file))
        self.assertNotEqual(output_file, self.test_audio_file)
        
        # Test with invalid file
        output_file, success = self.transcriber._speed_up_audio("nonexistent.wav", 1.5)
        self.assertFalse(success)
        self.assertEqual(output_file, "nonexistent.wav")
    
    def test_transcribe_with_speed_up(self):
        """Test transcription with audio speed-up."""
        # Load model first
        self.transcriber.load_model("base")
        
        # Wait for loading to complete
        start_time = time.time()
        while self.transcriber.is_loading and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Mock the model's transcribe method to ensure it returns our expected result
        self.transcriber.model.last_initial_prompt = None  # Reset this value
        
        # Create a proper mock for the result
        mock_result = {
            "text": "This is a test transcription",
            "duration": 2.5,
            "elapsed": 0.5
        }
        
        # Test transcription with speed-up (monkeypatch the returned result)
        with patch.object(self.transcriber, 'model') as mock_model:
            # Set up the mock return value
            mock_segments = [MagicMock(text="This is a test transcription")]
            mock_info = MagicMock(duration=2.5)
            mock_model.transcribe.return_value = (mock_segments, mock_info)
            
            # Call the transcribe method
            result = self.transcriber.transcribe(self.test_audio_file, speed_factor=1.5)
            
            # Verify the result
            self.assertIn("text", result)
            self.assertEqual(result["text"], "This is a test transcription")
            
            # Verify the model was called with correct parameters
            mock_model.transcribe.assert_called_once()
        
        # Verify no temporary files are left
        self.assertEqual(len(self.transcriber._temp_files), 0)
    
    def test_cleanup_temp_files(self):
        """Test temporary file cleanup."""
        # Create some temporary files
        temp_files = [
            self.transcriber._generate_temp_file() for _ in range(3)
        ]
        
        # Verify files exist
        for temp_file in temp_files:
            self.assertTrue(os.path.exists(temp_file))
        
        # Clean up
        self.transcriber._cleanup_temp_files()
        
        # Verify files are deleted
        for temp_file in temp_files:
            self.assertFalse(os.path.exists(temp_file))
        self.assertEqual(len(self.transcriber._temp_files), 0)
    
    def test_initial_prompt(self):
        """Test getting and setting the initial prompt."""
        # Check default value
        self.assertEqual(self.transcriber.get_initial_prompt(), "")
        
        # Set a new prompt
        test_prompt = "This is a test context for transcription"
        self.transcriber.set_initial_prompt(test_prompt)
        
        # Verify the prompt was set
        self.assertEqual(self.transcriber.get_initial_prompt(), test_prompt)
        
        # Verify it was saved to config
        self.config_manager.set.assert_called_with("initial_prompt", test_prompt)
        
        # Test setting an empty prompt
        self.transcriber.set_initial_prompt("")
        self.assertEqual(self.transcriber.get_initial_prompt(), "")
    
    def test_transcribe_with_initial_prompt(self):
        """Test transcription with an initial prompt."""
        # Test with a non-empty prompt
        # Set an initial prompt
        test_prompt = "This is a meeting about software development"
        self.transcriber.set_initial_prompt(test_prompt)
        
        # Load model
        self.transcriber.load_model("base")
        
        # Wait for loading to complete
        start_time = time.time()
        while self.transcriber.is_loading and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Transcribe with the prompt
        with patch.object(self.transcriber, 'model') as mock_model:
            # Set up the mock return value
            mock_segments = [MagicMock(text="This is a test transcription")]
            mock_info = MagicMock(duration=2.5)
            mock_model.transcribe.return_value = (mock_segments, mock_info)
            
            # Call the transcribe method
            self.transcriber.transcribe(self.test_audio_file)
            
            # Verify the model was called with correct parameters
            mock_model.transcribe.assert_called_once()
            call_args = mock_model.transcribe.call_args[1]  # Get keyword arguments
            self.assertIn("initial_prompt", call_args)
            self.assertEqual(call_args["initial_prompt"], test_prompt)
        
        # Test with an empty prompt
        self.transcriber.set_initial_prompt("")
        
        # Transcribe with empty prompt
        with patch.object(self.transcriber, 'model') as mock_model:
            # Set up the mock return value
            mock_segments = [MagicMock(text="This is a test transcription")]
            mock_info = MagicMock(duration=2.5)
            mock_model.transcribe.return_value = (mock_segments, mock_info)
            
            # Call the transcribe method
            self.transcriber.transcribe(self.test_audio_file)
            
            # Verify the model was called without initial_prompt
            mock_model.transcribe.assert_called_once()
            call_args = mock_model.transcribe.call_args[1]  # Get keyword arguments
            self.assertNotIn("initial_prompt", call_args)
            
        # Test with whitespace-only prompt
        self.transcriber.set_initial_prompt("   ")
        
        # Transcribe with whitespace prompt
        with patch.object(self.transcriber, 'model') as mock_model:
            # Set up the mock return value
            mock_segments = [MagicMock(text="This is a test transcription")]
            mock_info = MagicMock(duration=2.5)
            mock_model.transcribe.return_value = (mock_segments, mock_info)
            
            # Call the transcribe method
            self.transcriber.transcribe(self.test_audio_file)
            
            # Verify the model was called without initial_prompt
            mock_model.transcribe.assert_called_once()
            call_args = mock_model.transcribe.call_args[1]  # Get keyword arguments
            self.assertNotIn("initial_prompt", call_args)

if __name__ == "__main__":
    unittest.main()
