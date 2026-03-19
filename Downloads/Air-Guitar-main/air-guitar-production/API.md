# API Reference

Complete API documentation for all modules.

## Core Modules

### AudioEngine

**Purpose**: Manages voice synthesis, mixing, and effects processing.

#### Initialization

```python
from core.audio_engine import AudioEngine
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

engine = AudioEngine(
    config=config,
    sample_rate=config['audio']['sample_rate'],
    max_voices=config['audio']['max_voices'],
    decay_rate=config['audio']['decay_rate']
)
```

#### Voice Management

```python
# Add voice (starts synthesis immediately)
voice_id = engine.add_voice(
    frequency=440.0,      # Hz (A4)
    velocity=0.7,         # 0-1 (force-based)
    duration=3.0          # seconds (will continue until removed)
)

# Remove voice by ID
engine.remove_voice(voice_id)

# Remove all voices
engine.clear_all_voices()
```

#### Instrument Control

```python
# Get current instrument
current = engine.get_instrument()

# Switch instrument
engine.set_instrument('electric_guitar')

# Available: 'classic_guitar', 'acoustic_guitar', 'electric_guitar', 
#            'bass_guitar', 'synth_string'
```

#### Recording Control

```python
# Start recording
path = engine.start_recording(session_name='jam_1')

# Stop recording (returns file path)
file_path = engine.stop_recording()

# Check if recording
status = engine.is_recording()
```

#### Effects Chain

```python
# Enable/disable specific effect
engine.effects_chain.enable_effect('reverb', True)
engine.effects_chain.enable_effect('delay', False)

# Adjust effect parameter
engine.effects_chain.set_parameter('reverb', 'wet_level', 0.3)
engine.effects_chain.set_parameter('distortion', 'amount', 0.5)

# Get current parameter value
value = engine.effects_chain.get_parameter('reverb', 'room_size')
```

#### State Query

```python
# Get active voice count
num_voices = engine.get_voice_count()

# Get active notes (frequencies)
notes = engine.get_active_notes()
# Returns: [440.0, 554.4, 659.3, ...]

# Get system state dictionary
state = engine.get_state()
# Returns: {
#   'voice_count': 3,
#   'active_notes': [440.0, ...],
#   'instrument': 'acoustic_guitar',
#   'recording': False,
#   'effects': {'reverb': True, 'delay': False, ...}
# }
```

#### Starting/Stopping

```python
# Start audio stream
engine.start()

# Stop cleanly
engine.stop()

# Check if running
if engine.is_running():
    print("Audio stream active")
```

---

### SensorHandler

**Purpose**: Reads IMU data from Arduino via serial port.

#### Initialization

```python
from core.sensor_handler import SensorHandler

handler = SensorHandler(
    port='COM3',          # Windows
    baudrate=115200,
    timeout=1.0
)
handler.start()  # Starts background thread
```

#### Calibration

```python
# Set zero-point (neutral position)
handler.calibrate()

# Adjust offset manually
handler.zero_x = 1000
handler.zero_y = 2000
```

#### Data Reading

```python
# Get latest sensor reading (non-blocking)
data = handler.read_sensor()
if data:
    acX, acY, acZ = data
else:
    print("No new data available")

# Get calibrated angle
angle = handler.get_angle()  # 0-360 degrees

# Get force (acceleration magnitude)
force = handler.get_force()  # Raw acceleration magnitude
```

#### Cleanup

```python
handler.stop()  # Closes serial port, stops thread
```

---

### ChordEngine

**Purpose**: Gesture recognition and chord detection.

#### Initialization

```python
from core.chord_engine import ChordEngine

engine = ChordEngine(
    num_strings=6,
    base_frequency=82.4,   # Low E
    string_spacing=10.0    # Degrees between strings
)
```

#### Single Note Detection

```python
# Detect trigger (string pluck)
trigger = engine.detect_trigger(
    angle=45.3,
    force_magnitude=100.0,
    valid_samples_history=90  # From sensor queue
)

if trigger:
    string, velocity = trigger
    frequency = string.frequency
    print(f"Triggered: {string.note_name} with velocity {velocity}")
```

#### Chord Detection

```python
# Get currently held strings (simultaneous notes)
held_notes = engine.get_held_notes(
    angle=45.3,
    angle_tolerance=4.0
)

if len(held_notes) >= 2:
    print(f"Chord detected: {[s.note_name for s in held_notes]}")
```

#### Dynamic Parameter Adjustment

```python
# Change minimum notes for chord detection
engine.simultaneous_notes_min = 3  # Now requires 3+ strings

# Adjust angle tolerance
engine.angle_tolerance_chord = 5.0  # Wider range
```

---

### NoteGenerator (Synthesizer)

**Purpose**: Generates audio samples using Karplus-Strong algorithm.

#### Basic Synthesis

```python
from core.note_generator import KarplusStrongSynthesizer

synth = KarplusStrongSynthesizer(
    sample_rate=44100,
    decay_rate=0.994
)

# Generate 3 seconds of a 440Hz A4 note
duration_samples = 44100 * 3
samples = synth.generate_note(
    frequency=440.0,
    duration_samples=duration_samples,
    velocity=0.8
)
# Returns: numpy array of shape (132300,)
```

#### Advanced: Pitch Bending

```python
# Generate bend curve (frequency multipliers)
bend_curve = synth.generate_bend_curve(
    duration_samples=44100,
    start_mult=0.5,    # Down 1 octave at start
    end_mult=1.0       # Back to normal by end
)
# Returns: numpy array of shape (44100,) with values 0.5→1.0

# Apply pitch bend to samples
bent_samples = synth.generate_note_with_pitch_bend(
    frequency=440.0,
    duration_samples=44100,
    velocity=0.8,
    bend_curve=bend_curve
)
```

#### Vibrato (Periodic Modulation)

```python
# Generate vibrato effect (wobbling pitch)
vibrato = synth.generate_vibrato(
    duration_samples=44100,
    rate_hz=5.0,       # Oscillation frequency
    depth=0.05         # ±5% pitch variation
)
# Returns: addition signal to apply to samples
```

---

### EffectsChain

**Purpose**: Audio effects processing pipeline.

#### Initialization

```python
from core.effects import EffectsChain

effects = EffectsChain()
# Automatically includes Reverb, Delay, Distortion
```

#### Processing Audio

```python
# Process a buffer of samples
input_buffer = np.random.randn(2048)  # 2048 samples
output_buffer = effects.process_buffer(input_buffer)
# Returns: numpy array of shape (2048,) with effects applied
```

#### Individual Effect Control

```python
# Get effect state
is_enabled = effects.get_effect_enabled('reverb')

# Toggle effect
effects.enable_effect('reverb', True)

# Adjust parameters (real-time)
effects.set_parameter('reverb', 'room_size', 0.8)
effects.set_parameter('reverb', 'wet_level', 0.4)
effects.set_parameter('delay', 'feedback', 0.3)
effects.set_parameter('distortion', 'amount', 0.6)

# Get parameter value
wet_level = effects.get_parameter('reverb', 'wet_level')
```

#### Effect Parameters

**Reverb:**
- `room_size`: 0-1 (larger = longer decay)
- `damping`: 0-1 (lower = duller)
- `wet_level`: 0-1 (dry signal amount)
- `dry_level`: 0-1 (original signal amount)

**Delay:**
- `time_ms`: Delay time in milliseconds
- `feedback`: 0-1 (echo feedback)

**Distortion:**
- `amount`: 0-1 (saturation level)

---

### InstrumentModels

**Purpose**: Multiple synthesis algorithms with different timbres.

#### Using Factory Pattern

```python
from core.instrument_models import InstrumentFactory

# Create instrument by name
instrument = InstrumentFactory.create(
    model_name='electric_guitar',
    sample_rate=44100
)

# Generate note with specific model characteristics
samples = instrument.generate_note(
    frequency=440.0,
    duration_samples=132300,
    velocity=0.8
)
```

#### Available Models

```python
for model in ['classic_guitar', 'acoustic_guitar', 'electric_guitar', 
              'bass_guitar', 'synth_string']:
    instr = InstrumentFactory.create(model, 44100)
    samples = instr.generate_note(440.0, 44100*3, 0.8)
```

#### Model Characteristics

```python
# Each model has adjustable parameters
classic = InstrumentFactory.create('classic_guitar', 44100)
classic.decay_rate = 0.994      # Slower decay (longer sustain)
classic.brightness = 0.85       # Brighter tone

# Slower decay = longer sustain
# Higher brightness = more high-frequency content
```

---

### MIDIOutput

**Purpose**: Send MIDI data to DAW or synthesizer.

#### Initialization

```python
from core.midi_output import MIDIOutput

midi = MIDIOutput(
    device_index=None,    # None = default system output
    midi_channel=0        # 0-15 (channel 1-16)
)
```

#### Sending MIDI Notes

```python
# Send Note On (start playing)
midi.note_on(
    frequency=440.0,      # Converts to MIDI note
    velocity=100          # 0-127 (80 typical)
)

# Send Note Off (stop playing)
midi.note_off()
```

#### Pitch Bending

```python
# Send pitch bend in semitones
midi.pitch_bend(
    semitones_up=0.5      # +0.5 semitones (quarter-tone up)
)

# Or in ratio
midi.pitch_bend(
    semitones_up=-12      # Down 1 octave
)
```

#### Controller Changes

```python
# Send continuous controller (CC) message
midi.controller_change(
    controller=7,         # 7 = volume
    value=100             # 0-127
)

# Useful controllers:
# 1   = Modulation
# 7   = Volume
# 10  = Pan
# 64  = Sustain pedal
```

#### Utility Functions

```python
# Convert frequency to MIDI note
midi_note = midi.frequency_to_midi_note(440.0)
# Returns: 69 (A4)

# Convert MIDI note to frequency
freq = midi.midi_note_to_frequency(60)
# Returns: 261.63 (C3)
```

#### Cleanup

```python
midi.all_notes_off()      # Stop any playing notes
midi.close()              # Close port
```

---

### AudioRecorder

**Purpose**: Record audio to WAV files.

#### Initialization

```python
from core.recorder import AudioRecorder

recorder = AudioRecorder(
    output_folder='./recordings',
    sample_rate=44100
)
```

#### Recording Control

```python
# Start recording
filename = recorder.start_recording(session_name='take_1')
# Returns: 'air_guitar_take_1_20240319_120530.wav'

# Add samples to buffer (call frequently)
audio_samples = np.random.randn(2048)  # From audio callback
recorder.add_samples(audio_samples)

# Stop recording
file_path = recorder.stop_recording()
# Returns: full path to created WAV file
# Writes file to disk

# Check recording status
if recorder.is_recording():
    print("Currently recording")
```

#### File Management

```python
# List all recordings
files = recorder.list_recordings()
# Returns: ['take_1_20240319_120530.wav', 'take_2_20240319_120545.wav', ...]

# Get recording duration
duration_s = recorder.get_recording_duration('take_1_20240319_120530.wav')
# Returns: 47.3 (seconds)

# Get file size
size_bytes = recorder.get_file_size('take_1_20240319_120530.wav')
size_mb = size_bytes / (1024*1024)
```

---

### Web Controller (Flask)

**Purpose**: REST API server for remote control.

#### Running the Server

```python
# In config.yaml:
web:
  enabled: true
  host: "0.0.0.0"         # 0.0.0.0 = accept all external connections
  port: 5000
  debug: false

# In main.py:
web_controller.start()
```

#### API Endpoints

**Get System State:**
```
GET /api/state
→ {
    "voice_count": 3,
    "active_notes": [440.0, 554.4],
    "instrument": "acoustic_guitar",
    "recording": false,
    "effects": {"reverb": true, "delay": false, ...},
    "sensor_angle": 45.3,
    "sensor_force": 150,
    "web_ui": true
  }
```

**Recording Control:**
```
POST /api/control/recording/start
  Parameters: session_name="take_1"
  
POST /api/control/recording/stop
```

**Instrument Selection:**
```
POST /api/control/instrument/<name>
  Parameters: name ∈ [classic_guitar, acoustic_guitar, electric_guitar, 
                       bass_guitar, synth_string]
```

**Effect Control:**
```
POST /api/control/effects/<name>/toggle
  Parameters: name ∈ [reverb, delay, distortion]
  
POST /api/control/effect/<name>/param
  Parameters: param=room_size, value=0.8
```

**MIDI Control:**
```
POST /api/control/midi/enable
POST /api/control/midi/disable

POST /api/control/midi/pitch_bend
  Parameters: semitones_up=0.5
```

**Instrument List:**
```
GET /api/instruments
→ ["classic_guitar", "acoustic_guitar", "electric_guitar", 
    "bass_guitar", "synth_string"]
```

#### Registering Callbacks

```python
# Register callback for feature changes
def on_recording_started(path):
    print(f"Recording saved to: {path}")

web_controller.register_callback(
    'recording_stopped',
    on_recording_started
)

# Available callbacks:
# - 'instrument_changed': (instrument_name)
# - 'effect_toggled': (effect_name, enabled)
# - 'recording_started': (filename)
# - 'recording_stopped': (file_path)
# - 'midi_toggled': (enabled)
```

---

## System Integration Example

Complete example tying all modules together:

```python
import yaml
from core.audio_engine import AudioEngine
from core.sensor_handler import SensorHandler
from core.chord_engine import ChordEngine
from web.controller import WebController

# Load configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize all components
audio_engine = AudioEngine(config)
sensor_handler = SensorHandler(
    port=config['serial']['port'],
    baudrate=115200
)
chord_engine = ChordEngine(num_strings=6)
web_controller = WebController(audio_engine, config)

# Start systems
audio_engine.start()
sensor_handler.start()
web_controller.start()

# Main loop
running = True
while running:
    # 1. Read sensor
    sensor_data = sensor_handler.read_sensor()
    
    # 2. Detect triggers
    if sensor_data:
        acX, acY, acZ = sensor_data
        angle = sensor_handler.get_angle()
        force = sensor_handler.get_force()
        
        trigger = chord_engine.detect_trigger(angle, force, 90)
        if trigger:
            string, velocity = trigger
            voice_id = audio_engine.add_voice(
                frequency=string.frequency,
                velocity=velocity
            )
    
    # 3. Update display
    web_controller.update_state(audio_engine.get_state())
    
    # Check for commands
    if web_controller.was_recording_requested():
        audio_engine.start_recording()
    
    # Cleanup when done
    if quit_requested:
        audio_engine.stop()
        sensor_handler.stop()
        web_controller.stop()
        running = False
```

---

**Full API coverage for all production features.**

