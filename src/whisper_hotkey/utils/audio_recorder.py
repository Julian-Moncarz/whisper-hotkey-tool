# src/whisper_hotkey/utils/audio_recorder.py
"""
Handles audio recording functionality.
"""
import os
import time
import threading
import wave
from typing import Callable, List, Optional, Tuple

import numpy as np
import pyaudio
import soundfile as sf

from ..constants import SAMPLE_RATE, CHANNELS, RECORDINGS_DIR, AUDIO_FORMAT, DEFAULT_CHUNK_DURATION, DEFAULT_CHUNKING_ENABLED

class AudioRecorder:
    """Records audio from the default input device."""
    
    def __init__(self):
        self.recording = False
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.frames = []
        self.record_thread: Optional[threading.Thread] = None
        self.on_recording_started: Optional[Callable] = None
        self.on_recording_stopped: Optional[Callable[[str], None]] = None
        self.on_chunk_complete: Optional[Callable[[str], None]] = None
        self.current_filename: Optional[str] = None
        
        # Chunking related attributes
        self.chunking_enabled = DEFAULT_CHUNKING_ENABLED
        self.chunk_duration = DEFAULT_CHUNK_DURATION  # seconds
        self.chunk_frames = []
        self.chunk_start_time = 0
        self.chunk_timer: Optional[threading.Timer] = None
    
    def start_recording(self) -> bool:
        """
        Start recording audio.
        
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if self.recording:
            return False
            
        try:
            # Create PyAudio instance
            self.audio = pyaudio.PyAudio()
            
            # Check for input devices
            if self.audio.get_default_input_device_info() is None:
                print("No default input device found")
                self.audio.terminate()
                self.audio = None
                return False
            
            # Clear previous frames
            self.frames = []
            self.chunk_frames = []
            
            # Generate a filename for this recording
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            self.current_filename = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.{AUDIO_FORMAT}")
            
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=1024,
                stream_callback=self._audio_callback
            )
            
            # Set recording flag
            self.recording = True
            
            # Start the stream
            self.stream.start_stream()
            
            # Start chunk timer if chunking is enabled
            if self.chunking_enabled:
                self.chunk_start_time = time.time()
                self._schedule_chunk_check()
            
            # Notify listeners
            if self.on_recording_started:
                self.on_recording_started()
                
            return True
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            self._cleanup()
            return False
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording audio and return the audio data.
        
        Returns:
            Optional[str]: Path to a temporary audio file, or None if recording failed
        """
        if not self.recording:
            return None
            
        try:
            # Cancel any pending chunk timer
            if self.chunk_timer:
                self.chunk_timer.cancel()
                self.chunk_timer = None
            
            # Stop the stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Terminate PyAudio
            if self.audio:
                self.audio.terminate()
                self.audio = None
            
            # Set recording flag
            self.recording = False
            
            # Convert frames to numpy array and save to temporary file
            if self.frames:
                # Convert frames to numpy array
                audio_data = np.frombuffer(b''.join(self.frames), dtype=np.int16)
                
                # Create a temporary file
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(suffix=f".{AUDIO_FORMAT}", delete=False)
                
                # Save as WAV
                with sf.SoundFile(
                    temp_file.name,
                    'w',
                    SAMPLE_RATE,
                    CHANNELS,
                    format='WAV',
                    subtype='PCM_16'
                ) as f:
                    f.write(audio_data)
                
                # Process any remaining chunk frames if they exist
                if self.chunking_enabled and self.chunk_frames:
                    chunk_file = self._save_chunk()
                    if chunk_file and self.on_chunk_complete:
                        self.on_chunk_complete(chunk_file)
                
                # Notify listeners
                if self.on_recording_stopped:
                    self.on_recording_stopped(temp_file.name)
                
                return temp_file.name
                
            return None
            
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return None
        finally:
            self._cleanup()
    
    def is_recording(self) -> bool:
        """Check if recording is in progress."""
        return self.recording
    
    def set_chunk_duration(self, duration_seconds: int) -> None:
        """
        Set the chunk duration for real-time transcription.
        
        Args:
            duration_seconds: Duration of each chunk in seconds
        """
        self.chunk_duration = max(10, min(300, duration_seconds))  # Between 10s and 5min
    
    def set_chunking_enabled(self, enabled: bool) -> None:
        """
        Enable or disable chunking.
        
        Args:
            enabled: Whether chunking should be enabled
        """
        self.chunking_enabled = enabled
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream to process incoming audio data."""
        if self.recording:
            self.frames.append(in_data)
            if self.chunking_enabled:
                self.chunk_frames.append(in_data)
            return (in_data, pyaudio.paContinue)
        else:
            return (in_data, pyaudio.paComplete)
    
    def _schedule_chunk_check(self) -> None:
        """Schedule a check for chunk completion."""
        if not self.recording:
            return
            
        self.chunk_timer = threading.Timer(1.0, self._check_chunk_duration)
        self.chunk_timer.daemon = True
        self.chunk_timer.start()
    
    def _check_chunk_duration(self) -> None:
        """Check if the current chunk duration has been reached."""
        if not self.recording:
            return
            
        current_time = time.time()
        elapsed = current_time - self.chunk_start_time
        
        if elapsed >= self.chunk_duration and self.chunk_frames:
            # Save the current chunk
            chunk_file = self._save_chunk()
            
            # Reset for next chunk
            self.chunk_frames = []
            self.chunk_start_time = current_time
            
            # Notify listeners
            if chunk_file and self.on_chunk_complete:
                self.on_chunk_complete(chunk_file)
        
        # Schedule next check
        self._schedule_chunk_check()
    
    def _save_chunk(self) -> Optional[str]:
        """
        Save the current chunk frames to a temporary file.
        
        Returns:
            Optional[str]: Path to the temporary chunk file, or None if saving failed
        """
        try:
            if not self.chunk_frames:
                return None
                
            # Convert frames to numpy array
            audio_data = np.frombuffer(b''.join(self.chunk_frames), dtype=np.int16)
            
            # Create a temporary file
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix=f".{AUDIO_FORMAT}", delete=False)
            
            # Save as WAV
            with sf.SoundFile(
                temp_file.name,
                'w',
                SAMPLE_RATE,
                CHANNELS,
                format='WAV',
                subtype='PCM_16'
            ) as f:
                f.write(audio_data)
            
            return temp_file.name
            
        except Exception as e:
            print(f"Error saving chunk: {e}")
            return None
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        self.recording = False
        
        if self.chunk_timer:
            self.chunk_timer.cancel()
            self.chunk_timer = None
            
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
            
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
            self.audio = None
