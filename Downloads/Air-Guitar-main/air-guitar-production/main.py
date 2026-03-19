"""
Production-grade Air Guitar System
Real-time gesture-to-audio synthesis with advanced features
"""
import time
import signal
import yaml
import sys
from pathlib import Path

from core.audio_engine import AudioEngine
from core.sensor_handler import SensorHandler
from core.chord_engine import ChordEngine
from core.exceptions import (
    AirGuitarException, 
    SerialConnectionError, 
    SensorCalibrationError,
    ConfigurationError
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AirGuitarSystem:
    """
    Main application controller - complete production system.
    Coordinates sensor input, chord detection, audio synthesis, and advanced features.
    
    Features:
    - Real-time gesture recognition
    - Multiple instrument models
    - Audio effects (reverb, delay, distortion)
    - MIDI output for DAW integration
    - WAV file recording
    - Web-based remote control
    - Chord detection
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the system from config file."""
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.sensor = None
        self.audio_engine = None
        self.chord_engine = None
        self.web_controller = None
        
        self._running = False
        self._setup_signal_handlers()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            raise ConfigurationError(f"Config file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML: {e}")
    
    def initialize(self) -> bool:
        """
        Initialize all system components in dependency order.
        
        Order:
        1. Audio engine (no dependencies)
        2. Sensor handler (needs working connection)
        3. Chord engine (uses config)
        4. Web controller (optional, needs callbacks)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Audio Engine - with all advanced features
            logger.info("Initializing audio engine...")
            self.audio_engine = AudioEngine(
                sample_rate=self.config['audio']['sample_rate'],
                max_voices=self.config['audio']['max_voices'],
                config=self.config  # Pass full config for features
            )
            self.audio_engine.start()
            
            # Sensor Handler
            logger.info("Initializing sensor...")
            self.sensor = SensorHandler(
                port=self.config['serial']['port'],
                baud_rate=self.config['serial']['baud_rate'],
                timeout=self.config['serial']['timeout']
            )
            self.sensor.connect()
            self.sensor.calibrate()
            self.sensor.start_reading()
            
            # Chord Engine with advanced detection
            logger.info("Initializing chord engine...")
            chord_config = self.config.get('chord_detection', {})
            self.chord_engine = ChordEngine(
                strings=self.config['tuning']['strings'],
                min_force=self.config['sensor']['min_force_threshold'],
                angle_tolerance=self.config['tuning']['angle_tolerance'],
                chord_detection_enabled=chord_config.get('enabled', True),
                simultaneous_notes_min=chord_config.get('simultaneous_notes_min', 2)
            )
            
            # Web Controller (optional)
            if self.config.get('web', {}).get('enabled', False):
                logger.info("Initializing web controller...")
                from web.controller import WebController
                web_config = self.config['web']
                self.web_controller = WebController(
                    host=web_config.get('host', '127.0.0.1'),
                    port=web_config.get('port', 5000),
                    debug=web_config.get('debug', False)
                )
                self._setup_web_callbacks()
                self.web_controller.start()
            
            logger.info("✓ All systems initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.cleanup()
            return False
    
    def _setup_web_callbacks(self) -> None:
        """Setup callbacks for web controller."""
        if not self.web_controller:
            return
        
        # Recording callbacks
        self.web_controller.register_callback(
            'on_start_recording',
            lambda: self.audio_engine.start_recording()
        )
        self.web_controller.register_callback(
            'on_stop_recording',
            lambda: self.audio_engine.stop_recording()
        )
        
        # Instrument change callback
        self.web_controller.register_callback(
            'on_instrument_change',
            lambda name: self.audio_engine.set_instrument(name)
        )
        
        # Effect change callbacks
        self.web_controller.register_callback(
            'on_effect_change',
            lambda name, enabled: self.audio_engine.effects_chain.set_parameter(
                name, 'enabled', enabled
            ) if hasattr(self.audio_engine.effects_chain, 'set_parameter') else None
        )
        
        # MIDI toggle callback
        self.web_controller.register_callback(
            'on_midi_change',
            lambda enabled: setattr(self.audio_engine.midi, 'enabled', enabled)
        )
        
        logger.info("Web controller callbacks registered")
    
    def run(self) -> None:
        """
        Main event loop.
        Continuous cycle: read sensor -> detect notes -> trigger synthesis -> repeat
        """
        self._running = True
        logger.info("🎸 Ready! Move wrist to play.\n")
        
        frame_count = 0
        last_print_time = time.time()
        
        try:
            while self._running:
                # Get latest sensor reading
                sensor_data = self.sensor.get_latest_data()
                if not sensor_data:
                    time.sleep(0.001)
                    continue
                
                # Detect note triggers with chord detection
                triggers = self.chord_engine.detect_trigger(
                    sensor_data.roll, 
                    sensor_data.force
                )
                
                # Synthesize triggered notes
                for string, velocity in triggers:
                    self.audio_engine.add_voice(string.frequency, velocity)
                    print(f"🎵 {string.note_name} ({string.frequency:.1f}Hz) | velocity={velocity:.2f}")
                
                # Update web controller state (if enabled)
                if self.web_controller:
                    held_notes = [s.note_name for s in self.chord_engine.get_held_notes()]
                    self.web_controller.update_state({
                        'recording': self.audio_engine.is_recording(),
                        'active_voices': self.audio_engine.get_active_voice_count(),
                        'current_instrument': self.audio_engine.current_instrument,
                        'held_notes': held_notes,
                        'sensor_roll': sensor_data.roll,
                        'sensor_force': sensor_data.force
                    })
                
                # Periodic logging
                frame_count += 1
                current_time = time.time()
                if current_time - last_print_time >= 5.0:
                    voice_count = self.audio_engine.get_active_voice_count()
                    recording_status = "🔴 Recording" if self.audio_engine.is_recording() else "⊙"
                    logger.debug(f"{recording_status} | Voices: {voice_count} | Instrument: {self.audio_engine.current_instrument}")
                    last_print_time = current_time
        
        except KeyboardInterrupt:
            logger.info("\nShutdown requested...")
        except Exception as e:
            logger.error(f"Runtime error: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Cleanup and shutdown all components gracefully."""
        logger.info("Cleaning up...")
        self._running = False
        
        # Stop recording if active
        if self.audio_engine and self.audio_engine.is_recording():
            filename = self.audio_engine.stop_recording()
            logger.info(f"Recording saved: {filename}")
        
        # Shutdown audio engine
        if self.audio_engine:
            self.audio_engine.stop()
        
        # Shutdown sensor
        if self.sensor:
            self.sensor.stop_reading()
            self.sensor.disconnect()
        
        logger.info("Shutdown complete ✓")
    
    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown on CTRL+C."""
        def signal_handler(sig, frame):
            self._running = False
        
        signal.signal(signal.SIGINT, signal_handler)

def print_banner():
    """Print welcome banner."""
    banner = """
    ╔═══════════════════════════════════════════════════╗
    ║     🎸 AIR GUITAR - PRODUCTION SYSTEM 🎸         ║
    ║  Gesture-Controlled Real-Time Audio Synthesis    ║
    ║                                                   ║
    ║  Features:                                        ║
    ║  ✓ Multiple Instruments    ✓ Chord Detection    ║
    ║  ✓ Audio Effects           ✓ MIDI Output        ║
    ║  ✓ WAV Recording           ✓ Web Controller     ║
    ╚═══════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Entry point."""
    print_banner()
    
    system = AirGuitarSystem(config_path="config.yaml")
    
    if not system.initialize():
        print("\n❌ Initialization failed. Check:")
        print("   - Arduino is connected and on correct COM port")
        print("   - config.yaml exists and has correct settings")
        print("   - All sensors are calibrated")
        sys.exit(1)
    
    # Print features status
    print("\n📋 SYSTEM STATUS:")
    print(f"   Instruments: {list(system.audio_engine.instrument_models.keys())}")
    print(f"   Effects: {'Enabled' if system.audio_engine.effects_chain.enabled else 'Disabled'}")
    print(f"   MIDI: {'Enabled' if system.audio_engine.midi.enabled else 'Disabled'}")
    print(f"   Recording: {'Enabled' if system.config.get('recording', {}).get('enabled') else 'Disabled'}")
    print(f"   Web UI: {'http://{0}:{1}'.format(system.config['web']['host'], system.config['web']['port']) if system.config.get('web', {}).get('enabled') else 'Disabled'}")
    print()
    
    system.run()

if __name__ == "__main__":
    main()
