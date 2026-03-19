"""Different instrument synthesis models."""
import numpy as np
from typing import Dict, Callable
import logging

from utils.logger import setup_logger

logger = setup_logger(__name__)

class InstrumentModel:
    """Base class for different synthesis models."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.name = "generic"
    
    def generate_note(
        self, 
        freq: float, 
        duration_samples: int, 
        velocity: float = 0.8
    ) -> np.ndarray:
        """Generate audio using this instrument model."""
        raise NotImplementedError

class ClassicGuitarModel(InstrumentModel):
    """
    Classic nylon string guitar with warm decay.
    Uses Karplus-Strong with high damping.
    """
    
    def __init__(self, sample_rate: int = 44100, config: dict = None):
        super().__init__(sample_rate)
        self.name = "classic_guitar"
        self.config = config or {}
        
        self.decay_rate = self.config.get('decay_rate', 0.994)
        self.brightness = self.config.get('brightness', 0.8)  # 0-1, higher = brighter
        self.resonance = self.config.get('resonance', 0.2)  # 0-1, body resonance
    
    def generate_note(self, freq: float, duration_samples: int, velocity: float = 0.8) -> np.ndarray:
        """Generate classic guitar note."""
        period = int(self.sample_rate / freq)
        
        # Initialize with noise, scaled by velocity and brightness
        buf = (np.random.randn(period) * velocity * self.brightness).astype(np.float32)
        
        # Karplus-Strong with damping
        samples = np.zeros(duration_samples, dtype=np.float32)
        for i in range(duration_samples):
            buf[i % period] = (buf[i % period] + buf[(i + 1) % period]) * self.decay_rate
            samples[i] = buf[i % period]
        
        return samples

class AcousticGuitarModel(InstrumentModel):
    """
    Acoustic guitar with more body resonance.
    Slower decay, warmer tone.
    """
    
    def __init__(self, sample_rate: int = 44100, config: dict = None):
        super().__init__(sample_rate)
        self.name = "acoustic_guitar"
        self.config = config or {}
        
        self.decay_rate = self.config.get('decay_rate', 0.992)
        self.brightness = self.config.get('brightness', 0.7)
        self.resonance = self.config.get('resonance', 0.4)
    
    def generate_note(self, freq: float, duration_samples: int, velocity: float = 0.8) -> np.ndarray:
        """Generate acoustic guitar note with body resonance."""
        period = int(self.sample_rate / freq)
        
        # Warm initialization with less brightness
        buf = (np.random.randn(period) * velocity * self.brightness).astype(np.float32)
        
        # Add body resonance (secondary frequency component)
        resonance_freq = freq * (1 + self.resonance * 0.3)  # Slightly higher resonance
        resonance_period = int(self.sample_rate / resonance_freq)
        resonance_buf = (np.random.randn(resonance_period) * 0.1).astype(np.float32)
        
        # Generate with both fundamental and resonance
        samples = np.zeros(duration_samples, dtype=np.float32)
        for i in range(duration_samples):
            buf[i % period] = (buf[i % period] + buf[(i + 1) % period]) * self.decay_rate
            resonance_buf[i % resonance_period] = (resonance_buf[i % resonance_period] + resonance_buf[(i + 1) % resonance_period]) * 0.993
            
            # Mix fundamental with resonance
            samples[i] = buf[i % period] + resonance_buf[i % resonance_period] * self.resonance
        
        return samples

class ElectricGuitarModel(InstrumentModel):
    """
    Electric guitar with fast attack and longer sustain.
    Bright tone with less natural damping.
    """
    
    def __init__(self, sample_rate: int = 44100, config: dict = None):
        super().__init__(sample_rate)
        self.name = "electric_guitar"
        self.config = config or {}
        
        self.decay_rate = self.config.get('decay_rate', 0.985)
        self.brightness = self.config.get('brightness', 0.95)
        self.resonance = self.config.get('resonance', 0.1)
    
    def generate_note(self, freq: float, duration_samples: int, velocity: float = 0.8) -> np.ndarray:
        """Generate electric guitar note with bright tone."""
        period = int(self.sample_rate / freq)
        
        # Bright, punchy attack
        buf = (np.random.randn(period) * velocity).astype(np.float32)
        
        # Add harmonics for electric brightness
        samples = np.zeros(duration_samples, dtype=np.float32)
        for i in range(duration_samples):
            buf[i % period] = (buf[i % period] + buf[(i + 1) % period]) * self.decay_rate
            
            # Add slight harmonic brightening
            harmonic = np.sin(2 * np.pi * (i / self.sample_rate) * freq * 2) * 0.05
            samples[i] = buf[i % period] * self.brightness + harmonic
        
        return samples

class BassGuitarModel(InstrumentModel):
    """
    Bass guitar with deep, long sustain.
    Lower fundamental frequency focus.
    """
    
    def __init__(self, sample_rate: int = 44100, config: dict = None):
        super().__init__(sample_rate)
        self.name = "bass_guitar"
        self.config = config or {}
        
        self.decay_rate = self.config.get('decay_rate', 0.996)  # Longer decay
        self.brightness = self.config.get('brightness', 0.6)
        self.resonance = self.config.get('resonance', 0.5)
    
    def generate_note(self, freq: float, duration_samples: int, velocity: float = 0.8) -> np.ndarray:
        """Generate deep bass note."""
        period = int(self.sample_rate / freq)
        
        # Warm, round attack
        buf = (np.random.randn(period) * velocity * 0.9).astype(np.float32)
        
        samples = np.zeros(duration_samples, dtype=np.float32)
        for i in range(duration_samples):
            buf[i % period] = (buf[i % period] + buf[(i + 1) % period]) * self.decay_rate
            samples[i] = buf[i % period]
        
        return samples

class SynthStringModel(InstrumentModel):
    """
    Synthesized string with fully controllable tone.
    Useful for electronic/synthesizer sounds.
    """
    
    def __init__(self, sample_rate: int = 44100, config: dict = None):
        super().__init__(sample_rate)
        self.name = "synth_string"
        self.config = config or {}
    
    def generate_note(self, freq: float, duration_samples: int, velocity: float = 0.8) -> np.ndarray:
        """Generate synthesized string using sine wave."""
        t = np.arange(duration_samples) / self.sample_rate
        
        # Pure sine wave with exponential decay envelope
        decay_envelope = np.exp(-t * 2)  # Fast decay
        oscillation = np.sin(2 * np.pi * freq * t)
        
        return (oscillation * decay_envelope * velocity).astype(np.float32)

class InstrumentFactory:
    """Factory for creating instrument models."""
    
    MODELS = {
        'classic_guitar': ClassicGuitarModel,
        'acoustic_guitar': AcousticGuitarModel,
        'electric_guitar': ElectricGuitarModel,
        'bass_guitar': BassGuitarModel,
        'synth_string': SynthStringModel,
    }
    
    @classmethod
    def create(cls, model_name: str, sample_rate: int = 44100, config: dict = None) -> InstrumentModel:
        """
        Factory method to create instrument models.
        
        Args:
            model_name: Name of instrument ('classic_guitar', etc.)
            sample_rate: Audio sample rate
            config: Instrument configuration dictionary
        
        Returns:
            Initialized InstrumentModel instance
        """
        if model_name not in cls.MODELS:
            logger.warning(f"Unknown model '{model_name}', using classic_guitar")
            model_name = 'classic_guitar'
        
        model_class = cls.MODELS[model_name]
        return model_class(sample_rate=sample_rate, config=config)
    
    @classmethod
    def list_models(cls) -> list:
        """List available instrument models."""
        return list(cls.MODELS.keys())
