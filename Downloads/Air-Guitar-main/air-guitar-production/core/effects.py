"""Audio effects: Reverb, Delay, Distortion."""
import numpy as np
from collections import deque
import logging

from utils.logger import setup_logger

logger = setup_logger(__name__)

class ReverbEffect:
    """Schroeder reverberator - classic reverb using parallel comb/allpass filters."""
    
    def __init__(self, sample_rate: int = 44100, room_size: float = 0.5, damping: float = 0.5):
        """
        Reverb based on Freeverb algorithm.
        
        Args:
            sample_rate: Audio sample rate
            room_size: 0-1, larger = longer reverb
            damping: 0-1, more damping = duller sound
        """
        self.sample_rate = sample_rate
        self.room_size = room_size
        self.damping = damping
        self.wet_level = 0.3
        self.dry_level = 0.7
        
        # Comb filter buffers (parallel)
        self.comb_tunings = [1116, 1188, 1277, 1356]  # Delay in samples
        self.comb_buffers = [deque([0.0] * tuning, maxlen=tuning) for tuning in self.comb_tunings]
        self.comb_filter_stores = [0.0] * len(self.comb_tunings)
        
        # Allpass filter buffers (series)
        self.allpass_tunings = [556, 441, 341, 225]
        self.allpass_buffers = [deque([0.0] * tuning, maxlen=tuning) for tuning in self.allpass_tunings]
        self.allpass_filter_stores = [0.0] * len(self.allpass_tunings)
    
    def process(self, sample: float) -> float:
        """Process single audio sample through reverb."""
        # Comb filters in parallel
        comb_out = 0.0
        for i, comb_buf in enumerate(self.comb_buffers):
            # Get delayed sample
            delayed = comb_buf[0] if len(comb_buf) > 0 else 0.0
            
            # Apply damping filter
            self.comb_filter_stores[i] = delayed * (1 - self.damping) + self.comb_filter_stores[i] * self.damping
            
            # Feedback with room size
            feedback = self.comb_filter_stores[i] * self.room_size
            comb_buf.append(sample + feedback)
            comb_out += delayed
        
        # Allpass filters in series
        allpass_out = comb_out
        for i, allpass_buf in enumerate(self.allpass_buffers):
            delayed = allpass_buf[0] if len(allpass_buf) > 0 else 0.0
            
            # Allpass formula: out = -in + delayed + gain * (in + delayed * gain)
            # Simplified: xn = delayed, yn = -xn + delayed
            allpass_filter_stores = allpass_out
            allpass_out = -allpass_out + delayed
            allpass_buf.append(allpass_filter_stores)
        
        # Mix wet and dry signals
        return sample * self.dry_level + allpass_out * self.wet_level * 0.25

class DelayEffect:
    """Simple echo/delay effect."""
    
    def __init__(self, sample_rate: int = 44100, delay_ms: float = 300, feedback: float = 0.4):
        """
        Args:
            sample_rate: Audio sample rate
            delay_ms: Delay time in milliseconds
            feedback: 0-1, amount of delayed signal to feed back
        """
        self.sample_rate = sample_rate
        self.feedback = feedback
        self.wet_level = 0.3
        self.dry_level = 0.7
        
        # Delay buffer
        self.delay_samples = int(delay_ms * sample_rate / 1000)
        self.buffer = deque([0.0] * self.delay_samples, maxlen=self.delay_samples)
        self.write_index = 0
    
    def process(self, sample: float) -> float:
        """Process single audio sample through delay."""
        # Get delayed sample
        delayed = self.buffer[0] if len(self.buffer) > 0 else 0.0
        
        # Write new sample with feedback
        self.buffer.append(sample + delayed * self.feedback)
        
        # Mix wet and dry
        return sample * self.dry_level + delayed * self.wet_level

class DistortionEffect:
    """Soft-clipping distortion for warm/aggressive tone."""
    
    def __init__(self, amount: float = 0.3):
        """
        Args:
            amount: 0-1, amount of distortion
        """
        self.amount = amount
    
    def process(self, sample: float) -> float:
        """Apply soft-clipping distortion."""
        # Amplify then soft-clip using tanh
        amplified = sample * (1 + self.amount * 5)
        return np.tanh(amplified)

class EffectsChain:
    """Manages multiple audio effects in series."""
    
    def __init__(self, sample_rate: int = 44100, config: dict = None):
        """
        Args:
            sample_rate: Audio sample rate
            config: Effects config dictionary from YAML
        """
        self.sample_rate = sample_rate
        self.config = config or {}
        self.effects = []
        self.enabled = self.config.get('enabled', False)
        
        # Initialize enabled effects
        if self.config.get('reverb', {}).get('enabled'):
            reverb_cfg = self.config['reverb']
            self.reverb = ReverbEffect(
                sample_rate=sample_rate,
                room_size=reverb_cfg.get('room_size', 0.5),
                damping=reverb_cfg.get('damping', 0.5)
            )
            self.reverb.wet_level = reverb_cfg.get('wet_level', 0.3)
            self.reverb.dry_level = reverb_cfg.get('dry_level', 0.7)
            self.effects.append(('reverb', self.reverb))
        
        if self.config.get('delay', {}).get('enabled'):
            delay_cfg = self.config['delay']
            self.delay = DelayEffect(
                sample_rate=sample_rate,
                delay_ms=delay_cfg.get('time_ms', 300),
                feedback=delay_cfg.get('feedback', 0.4)
            )
            self.effects.append(('delay', self.delay))
        
        if self.config.get('distortion', {}).get('enabled'):
            dist_cfg = self.config['distortion']
            self.distortion = DistortionEffect(
                amount=dist_cfg.get('amount', 0.3)
            )
            self.effects.append(('distortion', self.distortion))
        
        logger.info(f"EffectsChain initialized with {len(self.effects)} effects: {[e[0] for e in self.effects]}")
    
    def process(self, sample: float) -> float:
        """Process audio sample through effects chain."""
        if not self.enabled:
            return sample
        
        # Process through each effect in series
        output = sample
        for name, effect in self.effects:
            output = effect.process(output)
        
        return output
    
    def process_buffer(self, buffer: np.ndarray) -> np.ndarray:
        """Process entire audio buffer."""
        if not self.enabled:
            return buffer
        
        processed = np.zeros_like(buffer)
        for i, sample in enumerate(buffer):
            processed[i] = self.process(sample)
        
        return processed
    
    def set_parameter(self, effect_name: str, param: str, value: float) -> None:
        """Dynamically update effect parameter."""
        for name, effect in self.effects:
            if name == effect_name:
                if hasattr(effect, param):
                    setattr(effect, param, value)
                    logger.debug(f"Updated {effect_name}.{param} = {value}")
                break
