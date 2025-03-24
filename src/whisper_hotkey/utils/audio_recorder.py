# src/whisper_hotkey/utils/audio_recorder.py
"""
Handles audio recording functionality.
"""
import os
import time
import threading
import wave
from typing import Callable, Optional

import numpy as np
import pyaudio
import soundfile as sf

from ..constants import SAMPLE_RATE, CHANNELS, RECORDINGS_DIR, AUDIO_FORMAT

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
        self.current_filename: Optional[str] = None
    
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
        Stop recording audio and save to file.
        
        Returns:
            Optional[str]: Path to the saved audio file, or None if recording failed
        """
        if not self.recording:
            return None
            
        try:
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
            
            # Save the recording
            if self.frames and self.current_filename:
                # Convert frames to numpy array
                audio_data = np.frombuffer(b''.join(self.frames), dtype=np.int16)
                
                # Save as WAV
                with sf.SoundFile(
                    self.current_filename,
                    'w',
                    SAMPLE_RATE,
                    CHANNELS,
                    format='WAV',
                    subtype='PCM_16'
                ) as f:
                    f.write(audio_data)
                
                # Notify listeners
                if self.on_recording_stopped:
                    self.on_recording_stopped(self.current_filename)
                
                return self.current_filename
                
            return None
            
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return None
        finally:
            self._cleanup()
    
    def is_recording(self) -> bool:
        """Check if recording is in progress."""
        return self.recording
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream to process incoming audio data."""
        if self.recording:
            self.frames.append(in_data)
            return (in_data, pyaudio.paContinue)
        else:
            return (in_data, pyaudio.paComplete)
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        self.recording = False
        
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
