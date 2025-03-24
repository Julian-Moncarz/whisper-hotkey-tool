# src/whisper_hotkey/models/whisper_transcriber.py
"""
Handles transcription of audio using OpenAI's Whisper model.
"""
import os
import time
import threading
from typing import Callable, Dict, Optional, Union

import whisper
import torch

from ..constants import MODELS_DIR, DEFAULT_WHISPER_MODEL
from ..utils.config_manager import ConfigManager

class WhisperTranscriber:
    """Transcribes audio using OpenAI's Whisper model."""
    
    # Available Whisper models and their approximate sizes
    AVAILABLE_MODELS = {
        "tiny": "39M",
        "base": "142M",
        "small": "466M",
        "medium": "1.5G",
        "large": "3G"
    }
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.model = None
        self.model_name = None
        self.config_manager = config_manager or ConfigManager()
        self.is_loading = False
        self.load_thread: Optional[threading.Thread] = None
        self.on_model_loaded: Optional[Callable] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def load_model(self, model_name: Optional[str] = None) -> bool:
        """
        Load a Whisper model.
        
        Args:
            model_name: Name of the model to load (tiny, base, small, medium, large)
                      If None, will use the model specified in config
        
        Returns:
            bool: True if model loading started, False otherwise
        """
        if self.is_loading:
            return False
            
        # Use the specified model or get from config
        if model_name is None:
            model_name = self.config_manager.get("whisper_model", DEFAULT_WHISPER_MODEL)
            
        # Validate model name
        if model_name not in self.AVAILABLE_MODELS:
            print(f"Invalid model name: {model_name}")
            return False
            
        # If the model is already loaded, check if it's the same
        if self.model and self.model_name == model_name:
            return True
            
        # Set loading flag
        self.is_loading = True
        
        # Start loading in a background thread
        self.load_thread = threading.Thread(
            target=self._load_model_thread,
            args=(model_name,),
            daemon=True
        )
        self.load_thread.start()
        
        return True
    
    def transcribe(self, audio_file: str) -> Dict[str, Union[str, float]]:
        """
        Transcribe the given audio file.
        
        Args:
            audio_file: Path to the audio file to transcribe
            
        Returns:
            Dict containing transcription result:
                - 'text': The transcribed text
                - 'duration': Duration of the audio in seconds
                - 'elapsed': Time taken for transcription
        """
        # Make sure model is loaded
        if not self.model:
            if not self.load_model():
                return {"text": "", "error": "Model not loaded", "duration": 0, "elapsed": 0}
                
            # Wait for model to load
            start_time = time.time()
            while self.is_loading and time.time() - start_time < 30:  # 30 second timeout
                time.sleep(0.1)
                
            if self.is_loading:
                return {"text": "", "error": "Model loading timeout", "duration": 0, "elapsed": 0}
        
        try:
            # Check if the audio file exists
            if not os.path.exists(audio_file):
                return {"text": "", "error": "Audio file not found", "duration": 0, "elapsed": 0}
                
            # Time the transcription
            start_time = time.time()
            
            # Transcribe the audio
            result = self.model.transcribe(audio_file)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Extract the text
            transcribed_text = result.get("text", "").strip()
            
            return {
                "text": transcribed_text,
                "duration": result.get("duration", 0),
                "elapsed": elapsed_time
            }
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return {"text": "", "error": str(e), "duration": 0, "elapsed": 0}
    
    def is_model_loaded(self) -> bool:
        """Check if a model is loaded."""
        return self.model is not None and not self.is_loading
    
    def get_loaded_model_name(self) -> Optional[str]:
        """Get the name of the currently loaded model."""
        return self.model_name if self.model else None
    
    def _load_model_thread(self, model_name: str) -> None:
        """
        Thread function for loading the model.
        
        Args:
            model_name: Name of the model to load
        """
        try:
            print(f"Loading Whisper model: {model_name}")
            
            # Load the model
            self.model = whisper.load_model(model_name, download_root=MODELS_DIR, device=self.device)
            self.model_name = model_name
            
            # Update config
            self.config_manager.set("whisper_model", model_name)
            
            print(f"Model {model_name} loaded successfully")
            
            # Notify listeners
            if self.on_model_loaded:
                self.on_model_loaded()
                
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.model = None
            self.model_name = None
            
        finally:
            self.is_loading = False
