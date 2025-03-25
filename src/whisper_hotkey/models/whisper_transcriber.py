# src/whisper_hotkey/models/whisper_transcriber.py
"""
Handles transcription of audio using Faster Whisper model.
"""
import os
import time
import threading
import logging
import tempfile
from typing import Callable, Dict, Optional, Union, Tuple

from faster_whisper import WhisperModel
import torch
from pydub import AudioSegment

from ..constants import MODELS_DIR, DEFAULT_WHISPER_MODEL, DEFAULT_SPEED_FACTOR
from ..utils.config_manager import ConfigManager

class WhisperTranscriber:
    """Transcribes audio using Faster Whisper model."""
    
    # Available Whisper models and their approximate sizes
    AVAILABLE_MODELS = {
        "tiny": "39M",
        "base": "142M",
        "small": "466M",
        "medium": "1.5G",
        "large-v2": "3G"  # Updated to use large-v2
    }
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.model = None
        self.model_name = None
        self.config_manager = config_manager or ConfigManager()
        self.is_loading = False
        self.load_thread: Optional[threading.Thread] = None
        self.on_model_loaded: Optional[Callable] = None
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Determine device and compute type
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        # Temporary file tracking
        self._temp_files = set()

    def _generate_temp_file(self, suffix: str = ".wav") -> str:
        """Generate a temporary file path."""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        self._temp_files.add(temp_file.name)
        return temp_file.name

    def _speed_up_audio(self, audio_file: str, speed_factor: float = DEFAULT_SPEED_FACTOR) -> Tuple[str, bool]:
        """
        Speed up the audio file by the given factor.
        
        Args:
            audio_file: Path to the input audio file
            speed_factor: Factor by which to speed up the audio (e.g., 1.5 for 50% faster)
            
        Returns:
            Tuple[str, bool]: (Path to processed file, Success flag)
        """
        try:
            # Load the audio file
            audio = AudioSegment.from_file(audio_file)
            
            # Speed up by modifying frame rate
            faster_audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed_factor)
            })
            
            # Export to new temporary file
            output_file = self._generate_temp_file()
            faster_audio.export(output_file, format="wav")
            
            return output_file, True
            
        except Exception as e:
            self.logger.error(f"Error speeding up audio: {e}")
            return audio_file, False

    def _cleanup_temp_files(self) -> None:
        """Clean up any temporary files created during processing."""
        for temp_file in self._temp_files.copy():
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                self._temp_files.remove(temp_file)
            except Exception as e:
                self.logger.error(f"Error cleaning up temporary file {temp_file}: {e}")

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """
        Load a Whisper model.
        
        Args:
            model_name: Name of the model to load (tiny, base, small, medium, large-v2)
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
            self.logger.error(f"Invalid model name: {model_name}")
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
    
    def transcribe(self, audio_file: str, speed_factor: Optional[float] = None) -> Dict[str, Union[str, float]]:
        """
        Transcribe the given audio file.
        
        Args:
            audio_file: Path to the audio file to transcribe
            speed_factor: Optional speed factor for audio processing
            
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
            
            # Speed up audio if requested
            if speed_factor is not None:
                processed_audio, success = self._speed_up_audio(audio_file, speed_factor)
                if not success:
                    self.logger.warning("Failed to speed up audio, using original file")
                    processed_audio = audio_file
            else:
                processed_audio = audio_file
            
            # Transcribe the audio with VAD
            segments, info = self.model.transcribe(
                processed_audio,
                beam_size=5,
                vad_filter=True,
                vad_parameters={"threshold": 0.5, "min_speech_duration_ms": 250, "max_speech_duration_s": 30}
            )
            
            # Combine segments into a single text
            transcribed_text = " ".join([segment.text for segment in segments])
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            return {
                "text": transcribed_text.strip(),
                "duration": info.duration,
                "elapsed": elapsed_time
            }
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return {"text": "", "error": str(e), "duration": 0, "elapsed": 0}
        finally:
            # Clean up any temporary files
            self._cleanup_temp_files()

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
            self.logger.info(f"Loading Faster Whisper model: {model_name}")
            
            # Load the model with optimal parameters for the device
            self.model = WhisperModel(
                model_name,
                device=self.device,
                compute_type=self.compute_type,
                download_root=MODELS_DIR
            )
            self.model_name = model_name
            
            # Update config
            self.config_manager.set("whisper_model", model_name)
            
            self.logger.info(f"Model {model_name} loaded successfully")
            
            # Notify listeners
            if self.on_model_loaded:
                self.on_model_loaded()
                
        except Exception as e:
            self.logger.error(f"Error loading Faster Whisper model: {e}")
            self.model = None
            self.model_name = None
            
        finally:
            self.is_loading = False

    def __del__(self):
        """Cleanup on object destruction."""
        self._cleanup_temp_files()
