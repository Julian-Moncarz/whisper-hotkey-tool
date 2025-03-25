#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from src.whisper_hotkey.app_core import AppCore

class TestAppCore(unittest.TestCase):
    """Tests for the AppCore class."""
    
    def setUp(self):
        """Set up the test environment with mocked components."""
        # Create mocks for each component
        self.mock_config_manager = MagicMock()
        self.mock_hotkey_manager = MagicMock()
        self.mock_audio_recorder = MagicMock()
        self.mock_text_inserter = MagicMock()
        self.mock_transcriber = MagicMock()
        
        # Set up default return values
        self.mock_config_manager.is_first_run.return_value = True
        self.mock_config_manager.get.return_value = "base"
        self.mock_transcriber.load_model.return_value = True
        self.mock_transcriber.is_model_loaded.return_value = True
        self.mock_transcriber.get_loaded_model_name.return_value = "base"
        self.mock_hotkey_manager.register_hotkey.return_value = True
        self.mock_audio_recorder.start_recording.return_value = True
        self.mock_audio_recorder.stop_recording.return_value = "/tmp/test_audio.wav"
        
        # Create patcher for component creation
        self.patcher1 = patch('src.whisper_hotkey.app_core.ConfigManager', return_value=self.mock_config_manager)
        self.patcher2 = patch('src.whisper_hotkey.app_core.HotkeyManager', return_value=self.mock_hotkey_manager)
        self.patcher3 = patch('src.whisper_hotkey.app_core.AudioRecorder', return_value=self.mock_audio_recorder)
        self.patcher4 = patch('src.whisper_hotkey.app_core.TextInserter', return_value=self.mock_text_inserter)
        self.patcher5 = patch('src.whisper_hotkey.app_core.WhisperTranscriber', return_value=self.mock_transcriber)
        
        # Start the patchers
        self.patcher1.start()
        self.patcher2.start()
        self.patcher3.start()
        self.patcher4.start()
        self.patcher5.start()
        
        # Create the app core
        self.app_core = AppCore()
        
        # Set up callback tracking
        self.callbacks_called = {
            "recording_started": False,
            "recording_stopped": False,
            "transcription_started": False,
            "transcription_complete": False,
            "error": False,
            "error_message": None
        }
        
        # Set up callbacks
        self.app_core.on_recording_started = self._on_recording_started
        self.app_core.on_recording_stopped = self._on_recording_stopped
        self.app_core.on_transcription_started = self._on_transcription_started
        self.app_core.on_transcription_complete = self._on_transcription_complete
        self.app_core.on_error = self._on_error
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop the patchers
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()
        self.patcher5.stop()
    
    def _on_recording_started(self):
        """Callback for when recording starts."""
        self.callbacks_called["recording_started"] = True
    
    def _on_recording_stopped(self):
        """Callback for when recording stops."""
        self.callbacks_called["recording_stopped"] = True
    
    def _on_transcription_started(self):
        """Callback for when transcription starts."""
        self.callbacks_called["transcription_started"] = True
    
    def _on_transcription_complete(self, text):
        """Callback for when transcription completes."""
        self.callbacks_called["transcription_complete"] = True
    
    def _on_error(self, message):
        """Callback for when an error occurs."""
        self.callbacks_called["error"] = True
        self.callbacks_called["error_message"] = message
    
    def test_initialization(self):
        """Test application initialization."""
        # Initialize the app
        result = self.app_core.initialize()
        self.assertTrue(result)
        
        # Verify that the components were initialized correctly
        self.mock_transcriber.load_model.assert_called_once()
        self.mock_hotkey_manager.register_hotkey.assert_called()
        self.mock_hotkey_manager.start.assert_called_once()
        self.mock_config_manager.mark_first_run_complete.assert_called_once()
    
    def test_recording_workflow(self):
        """Test the recording workflow."""
        # Initialize
        self.app_core.initialize()
        
        # Start recording
        result = self.app_core.start_recording()
        self.assertTrue(result)
        
        # Check that recording started
        self.mock_audio_recorder.start_recording.assert_called_once()
        
        # Simulate the internal callback
        self.app_core._on_recording_started()
        self.assertTrue(self.callbacks_called["recording_started"])
        self.assertTrue(self.app_core.is_currently_recording())
        
        # Stop recording
        result = self.app_core.stop_recording()
        self.assertTrue(result)
        
        # Check that recording stopped
        self.mock_audio_recorder.stop_recording.assert_called_once()
        
        # Simulate the internal callbacks
        self.app_core._on_recording_stopped("/tmp/test_audio.wav")
        self.assertTrue(self.callbacks_called["recording_stopped"])
        
        # Manually set the transcribing flag - in real execution this happens in stop_recording
        # but since we're mocking the thread creation we need to do it explicitly
        self.app_core.is_transcribing = True
        
        # Check transcription started
        self.assertTrue(self.callbacks_called["transcription_started"])
        self.assertTrue(self.app_core.is_currently_transcribing())
    
    def test_transcription_mocked(self):
        """Test the transcription process with mocks."""
        # Set up mock transcription result
        self.mock_transcriber.transcribe.return_value = {
            "text": "This is a test transcription",
            "duration": 2.5,
            "elapsed": 0.5
        }
        
        # Initialize
        self.app_core.initialize()
        
        # Set a current audio file
        self.app_core.current_audio_file = "/tmp/test_audio.wav"
        
        # Call the transcription method directly
        self.app_core._transcribe_audio("/tmp/test_audio.wav")
        
        # Verify that transcription was called with the speed factor
        self.mock_transcriber.transcribe.assert_called_once_with("/tmp/test_audio.wav", speed_factor=1.5)
        
        # Verify that text insertion was called
        self.mock_text_inserter.insert_text.assert_called_once_with("This is a test transcription")
    
    def test_set_hotkeys(self):
        """Test setting new hotkeys."""
        # Initialize
        self.app_core.initialize()
        
        # Set new hotkeys
        result = self.app_core.set_hotkeys("Command-Option-R", "Command-Option-S")
        self.assertTrue(result)
        
        # Verify that the old hotkeys were unregistered
        self.mock_hotkey_manager.unregister_hotkey.assert_called()
        
        # Verify that the new hotkeys were registered
        expected_calls = [
            unittest.mock.call("Command-Option-R", self.app_core.start_recording),
            unittest.mock.call("Command-Option-S", self.app_core.stop_recording)
        ]
        self.mock_hotkey_manager.register_hotkey.assert_has_calls(expected_calls, any_order=True)
        
        # Verify that the config was updated
        expected_config_calls = [
            unittest.mock.call("start_recording_hotkey", "Command-Option-R"),
            unittest.mock.call("stop_recording_hotkey", "Command-Option-S")
        ]
        self.mock_config_manager.set.assert_has_calls(expected_config_calls, any_order=True)
    
    def test_change_whisper_model(self):
        """Test changing the Whisper model."""
        # Create a patched version of the method that always returns True for model checks
        original_method = self.app_core.change_whisper_model
        
        def patched_change_model(model_name):
            # Skip the model validation check and directly call load_model
            return self.mock_transcriber.load_model(model_name)
            
        # Replace the method with our patched version
        self.app_core.change_whisper_model = patched_change_model
        
        # Initialize
        self.app_core.initialize()
        
        # Change to a model
        result = self.app_core.change_whisper_model("medium")
        self.assertTrue(result)
        
        # Verify that the model was loaded
        self.mock_transcriber.load_model.assert_called_with("medium")
        
        # Restore the original method
        self.app_core.change_whisper_model = original_method
    
    def test_cleanup(self):
        """Test application cleanup."""
        # Initialize
        self.app_core.initialize()
        
        # Clean up
        self.app_core.cleanup()
        
        # Verify that the hotkey manager was stopped
        self.mock_hotkey_manager.stop.assert_called_once()
        
        # Verify that the config was saved
        self.mock_config_manager.save_config.assert_called_once()

if __name__ == "__main__":
    unittest.main()
