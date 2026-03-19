"""Real-time audio synthesis and voice management engine."""
import numpy as np
import sounddevice as sd
import threading
import sys
from collections import OrderedDict
from typing import Callable, Optional
import logging

from .note_generator import KarplusStrongSynthesizer
from .effects import EffectsChain
from .instrument_models import InstrumentFactory
from .midi_output import MIDIOutput
from .recorder import AudioRecorder
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Voice:
    """Represents a single active note being played."""
    
    def __init__(self, freq: float, velocity: float = 0.8, instrument=None):
        self.freq = freq
        self.velocity = velocity
        self.position = 0  # Current sample position
        self.samples = None  # Generated samples
        self.is_active = True
        self.created_at = 0  # Timestamp for voice priority
        self.instrument = instrument  # Instrument model
    
    def get_sample(self) -> float:
        """Get next sample from this voice."""
        if not self.is_active or self.samples is None:
            return 0.0
        
        if self.position >= len(self.samples):
            self.is_active = False
            return 0.0
        
        sample = self.samples[self.position]
        self.position += 1
        return sample

class AudioEngine:
    """
    Production-grade real-time audio engine with:
    - Real-time synthesis (multiple instrument models)
    - Voice management and intelligent prioritization
    - Effects processing (reverb, delay, distortion)
    - MIDI output for DAW integration
    - WAV file recording
    - Smooth mixing without clipping/distortion
    """
    
    def __init__(
        self, 
        sample_rate: int = 44100, 
        max_voices: int = 8,
        config: dict = None
    ):
        self.sample_rate = sample_rate
        self.max_voices = max_voices
        self.config = config or {}
        
        # Extract audio configuration
        audio_config = self.config.get('audio', {})
        self.decay_rate = audio_config.get('decay_rate', 0.994)
        
        # Voice management
        self.voices = OrderedDict()
        self.voice_lock = threading.Lock()
        self.voice_counter = 0
        
        # Synthesis
        self.synthesizer = KarplusStrongSynthesizer(sample_rate)
        
        # Instrument models
        instruments_config = self.config.get('instruments', {})
        self.current_instrument = instruments_config.get('default', 'classic_guitar')
        self.instrument_models = {}
        self._initialize_instruments(instruments_config)
        
        # Effects
        effects_config = self.config.get('effects', {})
        self.effects_chain = EffectsChain(sample_rate, effects_config)
        
        # MIDI output
        midi_config = self.config.get('midi', {})
        self.midi = MIDIOutput(
            out_device=midi_config.get('out_device'),
            channel=midi_config.get('midi_channel', 0),
            enabled=midi_config.get('enabled', False)
        )
        
        # Recording
        recording_config = self.config.get('recording', {})
        self.recorder = AudioRecorder(
            sample_rate=sample_rate,
            output_folder=recording_config.get('output_folder', './recordings')
        )
        
        # Audio stream
        self.stream = None
        self._is_running = False
        
        logger.info(f"AudioEngine initialized: {sample_rate}Hz, max {max_voices} voices")
        logger.info(f"Instruments: {list(self.instrument_models.keys())}")
    
    def _initialize_instruments(self, instruments_config: dict) -> None:
        """Initialize all instrument models."""
        models_config = instruments_config.get('models', {})
        
        for model_name, model_params in models_config.items():
            try:
                self.instrument_models[model_name] = InstrumentFactory.create(
                    model_name,
                    sample_rate=self.sample_rate,
                    config=model_params
                )
            except Exception as e:
                logger.warning(f"Failed to load instrument {model_name}: {e}")
    
    def set_instrument(self, instrument_name: str) -> None:
        """Change the current instrument model."""
        if instrument_name in self.instrument_models:
            self.current_instrument = instrument_name
            logger.info(f"Instrument changed to: {instrument_name}")
        else:
            logger.warning(f"Unknown instrument: {instrument_name}")
    
    def add_voice(self, freq: float, velocity: float = 0.8) -> int:
        """
        Add a new voice (note) using current instrument.
        
        Args:
            freq: Frequency in Hz
            velocity: 0-1 velocity factor
        
        Returns:
            Voice ID
        """
        with self.voice_lock:
            # Voice stealing if at max capacity
            if len(self.voices) >= self.max_voices:
                oldest_id = next(iter(self.voices))
                del self.voices[oldest_id]
                if self.midi.enabled:
                    self.midi.note_off(oldest_id)
                logger.debug(f"Voice stealing: removed voice {oldest_id}")
            
            # Create new voice with current instrument
            instrument = self.instrument_models.get(self.current_instrument)
            voice = Voice(freq, velocity, instrument)
            
            # Generate samples using current instrument
            if instrument:
                voice.samples = instrument.generate_note(
                    freq,
                    int(3.0 * self.sample_rate),  # 3-second note
                    velocity
                )
            else:
                # Fallback to basic synthesis if instrument not available
                voice.samples = self.synthesizer.generate_note_chunk(
                    freq,
                    int(3.0 * self.sample_rate),
                    velocity,
                    self.decay_rate
                )
            
            voice.created_at = self.voice_counter
            
            voice_id = self.voice_counter
            self.voices[voice_id] = voice
            self.voice_counter += 1
            
            # Send MIDI note on
            if self.midi.enabled:
                midi_note = self.midi.frequency_to_midi_note(freq)
                midi_velocity = int(velocity * 127)
                self.midi.note_on(midi_note, midi_velocity, voice_id)
            
            logger.debug(f"Voice added: {voice_id} @ {freq:.2f}Hz using {self.current_instrument}")
            return voice_id
    
    def remove_voice(self, voice_id: int) -> None:
        """Remove a voice immediately."""
        with self.voice_lock:
            if voice_id in self.voices:
                del self.voices[voice_id]
                if self.midi.enabled:
                    self.midi.note_off(voice_id)
    
    def add_pitch_bend(self, voice_id: int, bend_amount: float) -> None:
        """Apply pitch bend to a voice."""
        if self.midi.enabled:
            self.midi.pitch_bend(bend_amount, voice_id)
    
    def _audio_callback(self, outdata: np.ndarray, frames: int, time_info, status):
        """Real-time audio callback."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Mix all active voices
        mixed_audio = np.zeros(frames, dtype=np.float32)
        
        with self.voice_lock:
            inactive_voices = []
            
            for voice_id, voice in self.voices.items():
                for i in range(frames):
                    sample = voice.get_sample()
                    mixed_audio[i] += sample
                
                if not voice.is_active:
                    inactive_voices.append(voice_id)
            
            # Clean up inactive voices
            for voice_id in inactive_voices:
                if self.midi.enabled:
                    self.midi.note_off(voice_id)
                del self.voices[voice_id]
        
        # Apply effects chain
        if self.effects_chain.enabled:
            mixed_audio = self.effects_chain.process_buffer(mixed_audio)
        
        # Apply limiter
        mixed_audio = np.tanh(mixed_audio) * 0.9
        
        # Normalize
        max_val = np.max(np.abs(mixed_audio))
        if max_val > 1.0:
            mixed_audio = mixed_audio / (max_val * 1.01)
        
        # Record if enabled
        if self.recorder.is_recording:
            self.recorder.add_samples(mixed_audio)
        
        # Output
        outdata[:, 0] = mixed_audio
    
    def start_recording(self, session_name: str = "session") -> str:
        """Start recording session."""
        return self.recorder.start_recording(session_name)
    
    def stop_recording(self) -> Optional[str]:
        """Stop recording and save file."""
        return self.recorder.stop_recording()
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recorder.is_recording
    
    def start(self):
        """Start the audio stream."""
        try:
            self.stream = sd.OutputStream(
                channels=1,
                samplerate=self.sample_rate,
                callback=self._audio_callback,
                blocksize=2048
            )
            self.stream.start()
            self._is_running = True
            logger.info("Audio stream started")
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            raise
    
    def stop(self):
        """Stop the audio stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self._is_running = False
            if self.midi.enabled:
                self.midi.all_notes_off()
                self.midi.close()
            logger.info("Audio stream stopped")
    
    def is_running(self) -> bool:
        """Check if audio engine is running."""
        return self._is_running
    
    def get_active_voice_count(self) -> int:
        """Get number of currently active voices."""
        with self.voice_lock:
            return len(self.voices)

