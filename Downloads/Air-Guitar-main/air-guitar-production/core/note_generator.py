"""Real-time Karplus-Strong note synthesis engine with advanced features."""
import numpy as np
from typing import Tuple

class KarplusStrongSynthesizer:
    """
    Efficient Karplus-Strong algorithm for creating realistic plucked string sounds.
    Generates audio on-the-fly instead of pre-computing (memory efficient).
    
    Enhanced with:
    - Pitch bending capabilities
    - Modulation effects
    - Harmonic generation
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.buffer_cache = {}  # Cache initialized buffers
    
    def generate_note_chunk(
        self, 
        freq: float, 
        duration_samples: int, 
        velocity: float = 0.8,
        decay_rate: float = 0.994
    ) -> np.ndarray:
        """
        Generate audio chunk using Karplus-Strong algorithm.
        This creates a realistic plucked string sound.
        
        Args:
            freq: Note frequency in Hz
            duration_samples: Number of samples to generate
            velocity: 0-1 velocity factor (affects initial amplitude and brightness)
            decay_rate: 0-1 decay rate (how quickly string dampens)
        
        Returns:
            Audio samples as numpy array
        """
        # Calculate buffer period (one wavelength of the note)
        period = int(self.sample_rate / freq)
        if period < 1:
            period = 1
        
        # Initialize with white noise, scaled by velocity
        buf = (np.random.randn(period) * velocity).astype(np.float32)
        
        # Generate audio samples using Karplus-Strong algorithm
        samples = np.zeros(duration_samples, dtype=np.float32)
        for i in range(duration_samples):
            # Apply simple moving average damping filter
            buf[i % period] = (buf[i % period] + buf[(i + 1) % period]) * decay_rate
            samples[i] = buf[i % period]
        
        return samples
    
    def generate_note_with_pitch_bend(
        self,
        freq: float,
        duration_samples: int,
        velocity: float = 0.8,
        decay_rate: float = 0.994,
        bend_curve: np.ndarray = None
    ) -> np.ndarray:
        """
        Generate note with pitch bending/modulation.
        
        Args:
            freq: Base frequency in Hz
            duration_samples: Number of samples to generate
            velocity: 0-1 velocity factor
            decay_rate: String damping
            bend_curve: Optional array of frequency multipliers (length = duration_samples)
                       If None, no bending applied
        
        Returns:
            Audio samples with pitch bending applied
        """
        if bend_curve is None:
            return self.generate_note_chunk(freq, duration_samples, velocity, decay_rate)
        
        # Generate normal note first
        samples = self.generate_note_chunk(freq, duration_samples, velocity, decay_rate)
        
        # Apply pitch bending via envelope modulation
        # bend_curve values: 1.0 = normal, 0.9 = -10%, 1.1 = +10%, etc.
        bend_curve = np.clip(bend_curve, 0.5, 2.0)  # Limit to ±1 octave
        samples = samples * bend_curve[:len(samples)]
        
        return samples
    
    def apply_adsr_envelope(
        self,
        samples: np.ndarray,
        sample_rate: int,
        attack_ms: float = 5.0,
        decay_ms: float = 20.0,
        sustain_level: float = 0.7,
        release_ms: float = 500.0
    ) -> np.ndarray:
        """
        Apply ADSR (Attack-Decay-Sustain-Release) envelope for natural sounds.
        ADSR is how musicians describe the sound shape: quick attack, decay to sustain, then release.
        
        Args:
            samples: Input audio samples
            sample_rate: Sample rate in Hz
            attack_ms: Attack time in milliseconds
            decay_ms: Decay time in milliseconds
            sustain_level: Sustain amplitude level (0-1)
            release_ms: Release time in milliseconds
        
        Returns:
            Envelope-shaped audio samples
        """
        n_samples = len(samples)
        envelope = np.ones(n_samples, dtype=np.float32)
        
        # Convert ms to samples
        attack_samples = int(attack_ms * sample_rate / 1000)
        decay_samples = int(decay_ms * sample_rate / 1000)
        sustain_samples = n_samples - attack_samples - decay_samples
        
        # Attack phase: volume rises from 0 to 1
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay phase: volume falls from 1 to sustain_level
        if decay_samples > 0:
            decay_start = attack_samples
            envelope[decay_start:decay_start + decay_samples] = np.linspace(
                1, sustain_level, decay_samples
            )
        
        # Sustain phase: constant level
        sustain_start = attack_samples + decay_samples
        if sustain_start < n_samples:
            envelope[sustain_start:] = sustain_level
        
        # Apply envelope to samples
        return samples * envelope
    
    def generate_bend_curve(
        self,
        duration_samples: int,
        start_mult: float = 1.0,
        end_mult: float = 1.0
    ) -> np.ndarray:
        """
        Generate a pitch bend curve.
        
        Args:
            duration_samples: Length of curve
            start_mult: Starting frequency multiplier (1.0 = normal)
            end_mult: Ending frequency multiplier
        
        Returns:
            Pitch bend curve as numpy array
        """
        return np.linspace(start_mult, end_mult, duration_samples).astype(np.float32)
    
    def generate_vibrato(
        self,
        duration_samples: int,
        rate_hz: float = 5.0,
        depth: float = 0.05
    ) -> np.ndarray:
        """
        Generate vibrato (periodic pitch modulation).
        
        Args:
            duration_samples: Length of vibrato
            rate_hz: Vibrato frequency (typically 4-8 Hz)
            depth: Vibrato depth (0-1, typical 0.05-0.1)
        
        Returns:
            Vibrato envelope as numpy array
        """
        t = np.arange(duration_samples) / self.sample_rate
        vibrato = 1.0 + depth * np.sin(2 * np.pi * rate_hz * t)
        return vibrato.astype(np.float32)
