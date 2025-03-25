# src/whisper_hotkey/app_core.py
"""
Core application logic for Whisper Hotkey Tool.
"""
import os
import threading
from typing import Callable, Dict, Optional

from .constants import DEFAULT_START_RECORDING_HOTKEY, DEFAULT_STOP_RECORDING_HOTKEY
from .utils.config_manager import ConfigManager
from .utils.hotkey_manager import HotkeyManager
from .utils.audio_recorder import AudioRecorder
from .utils.text_inserter import TextInserter
from .models.whisper_transcriber import WhisperTranscriber

class AppCore:
    """Core application logic for Whisper Hotkey Tool."""
    
    def __init__(self):
        # Initialize components
        self.config_manager = ConfigManager()
        self.hotkey_manager = HotkeyManager()
        self.audio_recorder = AudioRecorder()
        self.text_inserter = TextInserter()
        self.transcriber = WhisperTranscriber(self.config_manager)
        
        # Set up state
        self.is_recording = False
        self.is_transcribing = False
        self.is_first_run = self.config_manager.is_first_run()
        self.current_audio_file: Optional[str] = None
        
        # Set up callbacks
        self.on_recording_started: Optional[Callable] = None
        self.on_recording_stopped: Optional[Callable] = None
        self.on_transcription_started: Optional[Callable] = None
        self.on_transcription_complete: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Connect internal callbacks
        self.audio_recorder.on_recording_started = self._on_recording_started
        self.audio_recorder.on_recording_stopped = self._on_recording_stopped
        self.transcriber.on_model_loaded = self._on_model_loaded
        self.text_inserter.on_insertion_complete = self._on_insertion_complete
    
    def initialize(self) -> bool:
        """
        Initialize the application.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Start loading the Whisper model
            model_name = self.config_manager.get("whisper_model")
            self.transcriber.load_model(model_name)
            
            # Register hotkeys
            start_hotkey = self.config_manager.get("start_recording_hotkey", DEFAULT_START_RECORDING_HOTKEY)
            stop_hotkey = self.config_manager.get("stop_recording_hotkey", DEFAULT_STOP_RECORDING_HOTKEY)
            
            self.hotkey_manager.register_hotkey(start_hotkey, self.start_recording)
            self.hotkey_manager.register_hotkey(stop_hotkey, self.stop_recording)
            
            # Start the hotkey manager
            self.hotkey_manager.start()
            
            # If this is the first run, mark it as complete
            if self.is_first_run:
                self.config_manager.mark_first_run_complete()
                self.is_first_run = False
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error initializing application: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up resources before exiting."""
        # Stop recording if in progress
        if self.is_recording:
            self.stop_recording()
            
        # Stop the hotkey manager
        self.hotkey_manager.stop()
        
        # Save any pending configuration changes
        self.config_manager.save_config()
    
    def start_recording(self) -> bool:
        """
        Start recording audio.
        
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if self.is_recording:
            return False
            
        # Start the recording
        result = self.audio_recorder.start_recording()
        
        return result
    
    def stop_recording(self) -> bool:
        """
        Stop recording audio and start transcription.
        
        Returns:
            bool: True if recording stopped successfully, False otherwise
        """
        if not self.is_recording:
            return False
            
        # Stop the recording
        audio_file = self.audio_recorder.stop_recording()
        
        if not audio_file:
            if self.on_error:
                self.on_error("Failed to save audio recording.")
            return False
            
        # Store the audio file path
        self.current_audio_file = audio_file
        
        # Start transcription in a background thread
        self.is_transcribing = True
        if self.on_transcription_started:
            self.on_transcription_started()
            
        threading.Thread(
            target=self._transcribe_audio,
            args=(audio_file,),
            daemon=True
        ).start()
        
        return True
    
    def set_hotkeys(self, start_hotkey: str, stop_hotkey: str) -> bool:
        """
        Set new hotkeys for recording control.
        
        Args:
            start_hotkey: Hotkey string for starting recording
            stop_hotkey: Hotkey string for stopping recording
            
        Returns:
            bool: True if hotkeys were set successfully, False otherwise
        """
        try:
            # Unregister existing hotkeys
            old_start = self.config_manager.get("start_recording_hotkey", DEFAULT_START_RECORDING_HOTKEY)
            old_stop = self.config_manager.get("stop_recording_hotkey", DEFAULT_STOP_RECORDING_HOTKEY)
            
            self.hotkey_manager.unregister_hotkey(old_start)
            self.hotkey_manager.unregister_hotkey(old_stop)
            
            # Register new hotkeys
            result1 = self.hotkey_manager.register_hotkey(start_hotkey, self.start_recording)
            result2 = self.hotkey_manager.register_hotkey(stop_hotkey, self.stop_recording)
            
            if not (result1 and result2):
                # Revert to old hotkeys on failure
                self.hotkey_manager.register_hotkey(old_start, self.start_recording)
                self.hotkey_manager.register_hotkey(old_stop, self.stop_recording)
                return False
                
            # Update configuration
            self.config_manager.set("start_recording_hotkey", start_hotkey)
            self.config_manager.set("stop_recording_hotkey", stop_hotkey)
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error setting hotkeys: {e}")
            return False
    
    def change_whisper_model(self, model_name: str) -> bool:
        """
        Change the Whisper model used for transcription.
        
        Args:
            model_name: Name of the model to use (tiny, base, small, medium, large)
            
        Returns:
            bool: True if model change started, False otherwise
        """
        if model_name not in WhisperTranscriber.AVAILABLE_MODELS:
            if self.on_error:
                self.on_error(f"Invalid model name: {model_name}")
            return False
            
        # Start loading the new model
        return self.transcriber.load_model(model_name)
    
    def is_model_loaded(self) -> bool:
        """Check if a Whisper model is loaded."""
        return self.transcriber.is_model_loaded()
    
    def get_current_model(self) -> Optional[str]:
        """Get the currently loaded model name."""
        return self.transcriber.get_loaded_model_name()
    
    def get_available_models(self) -> Dict[str, str]:
        """Get a dictionary of available models and their sizes."""
        return WhisperTranscriber.AVAILABLE_MODELS.copy()
    
    def is_currently_recording(self) -> bool:
        """Check if recording is currently in progress."""
        return self.is_recording
    
    def is_currently_transcribing(self) -> bool:
        """Check if transcription is currently in progress."""
        return self.is_transcribing
    
    def _on_recording_started(self) -> None:
        """Internal callback for when recording starts."""
        self.is_recording = True
        
        if self.on_recording_started:
            self.on_recording_started()
    
    def _on_recording_stopped(self, audio_file: str) -> None:
        """Internal callback for when recording stops."""
        self.is_recording = False
        
        if self.on_recording_stopped:
            self.on_recording_stopped()
    
    def _on_model_loaded(self) -> None:
        """Internal callback for when a model is loaded."""
        # Nothing to do here currently
        pass
    
    def _on_insertion_complete(self) -> None:
        """Internal callback for when text insertion is complete."""
        # Always clean up the temporary audio file
        if self.current_audio_file:
            try:
                if os.path.exists(self.current_audio_file):
                    os.remove(self.current_audio_file)
            except Exception as e:
                print(f"Error removing audio file: {e}")
    
    def _transcribe_audio(self, audio_file: str) -> None:
        """
        Background thread for transcribing audio.
        
        Args:
            audio_file: Path to the audio file to transcribe
        """
        try:
            # Transcribe the audio
            result = self.transcriber.transcribe(audio_file)
            
            if "error" in result:
                if self.on_error:
                    self.on_error(f"Transcription error: {result['error']}")
                return
                
            transcribed_text = result["text"]
            
            # Insert the transcribed text
            self.text_inserter.insert_text(transcribed_text)
            
            # Notify listeners
            if self.on_transcription_complete:
                self.on_transcription_complete(transcribed_text)
                
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error during transcription: {e}")
                
        finally:
            self.is_transcribing = False
