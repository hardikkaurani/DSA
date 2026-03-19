"""Audio recording to WAV files."""
import soundfile as sf
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional

from utils.logger import setup_logger

logger = setup_logger(__name__)

class AudioRecorder:
    """Records audio to WAV files with automatic timestamped naming."""
    
    def __init__(self, sample_rate: int = 44100, output_folder: str = "./recordings"):
        """
        Args:
            sample_rate: Audio sample rate in Hz
            output_folder: Folder to save recordings
        """
        self.sample_rate = sample_rate
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        self.is_recording = False
        self.buffer = []
        self.current_filename: Optional[str] = None
        
        logger.info(f"AudioRecorder initialized, output: {self.output_folder}")
    
    def start_recording(self, session_name: str = "air_guitar") -> str:
        """
        Start recording session.
        
        Args:
            session_name: Base name for recording file
        
        Returns:
            Filename of the recording
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return self.current_filename or ""
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_filename = f"{session_name}_{timestamp}.wav"
        self.is_recording = True
        self.buffer = []
        
        logger.info(f"Recording started: {self.current_filename}")
        return self.current_filename
    
    def add_samples(self, samples: np.ndarray) -> None:
        """
        Add audio samples to recording buffer.
        
        Args:
            samples: Audio samples as numpy array
        """
        if not self.is_recording:
            return
        
        # Convert to mono if needed
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1)
        
        self.buffer.extend(samples)
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and save to file.
        
        Returns:
            Full path to the saved file, or None if not recording
        """
        if not self.is_recording:
            logger.warning("Not recording")
            return None
        
        self.is_recording = False
        
        if not self.buffer:
            logger.warning("No samples recorded")
            return None
        
        # Convert buffer to numpy array
        audio_data = np.array(self.buffer, dtype=np.float32)
        
        # Save to WAV file
        output_path = self.output_folder / self.current_filename
        try:
            sf.write(str(output_path), audio_data, self.sample_rate)
            duration = len(audio_data) / self.sample_rate
            logger.info(f"Recording saved: {output_path} ({duration:.1f}s)")
            return str(output_path)
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")
            return None
    
    def list_recordings(self) -> list:
        """List all recordings in output folder."""
        return sorted([f.name for f in self.output_folder.glob("*.wav")])
    
    def get_recording_duration(self, filename: str) -> float:
        """
        Get duration of a recording file.
        
        Args:
            filename: Recording filename
        
        Returns:
            Duration in seconds
        """
        try:
            path = self.output_folder / filename
            data, sr = sf.read(str(path))
            return len(data) / sr
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            return 0.0
