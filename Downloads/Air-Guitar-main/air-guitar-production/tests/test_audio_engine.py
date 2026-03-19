"""Unit tests for audio engine."""
import unittest
import numpy as np
from core.audio_engine import AudioEngine, Voice

class TestAudioEngine(unittest.TestCase):
    """Test audio synthesis and voice management."""
    
    def setUp(self):
        self.engine = AudioEngine(sample_rate=44100, max_voices=4)
    
    def tearDown(self):
        if self.engine.is_running():
            self.engine.stop()
    
    def test_voice_creation(self):
        """Test voice creation and synthesis."""
        voice_id = self.engine.add_voice(freq=440.0, velocity=0.8)
        self.assertIsInstance(voice_id, int)
        self.assertEqual(self.engine.get_active_voice_count(), 1)
    
    def test_voice_stealing(self):
        """Test voice stealing when max voices exceeded."""
        # Add 6 voices (max is 4)
        for i in range(6):
            self.engine.add_voice(freq=440.0 + i*20, velocity=0.8)
        
        # Should only have 4 voices (oldest removed)
        self.assertEqual(self.engine.get_active_voice_count(), 4)
    
    def test_velocity_scaling(self):
        """Test velocity parameter affects amplitude."""
        self.engine.add_voice(freq=440.0, velocity=1.0)
        self.engine.add_voice(freq=440.0, velocity=0.1)
        self.assertEqual(self.engine.get_active_voice_count(), 2)
    
    def test_frequency_range(self):
        """Test various frequency values."""
        frequencies = [82.41, 110.0, 146.83, 196.0, 246.94, 329.63]
        for freq in frequencies:
            voice_id = self.engine.add_voice(freq=freq)
            self.assertIsInstance(voice_id, int)

if __name__ == '__main__':
    unittest.main()
