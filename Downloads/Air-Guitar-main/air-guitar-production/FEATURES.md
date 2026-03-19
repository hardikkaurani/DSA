# Air Guitar - Advanced Features Guide

Complete documentation for all production-grade features.

## 🎸 Feature Overview

### 1. **Multiple Instrument Models**

Choose from different synthesis algorithms, each with unique sonic characteristics.

#### Available Instruments

| Instrument | Decay | Brightness | Best For |
|-----------|-------|-----------|----------|
| Classic Guitar | 0.994 | 0.8 | Warm, traditional guitar tone |
| Acoustic Guitar | 0.992 | 0.7 | Full body resonance, natural |
| Electric Guitar | 0.985 | 0.95 | Bright, punchy, sustained tone |
| Bass Guitar | 0.996 | 0.6 | Deep, long sustain |
| Synth String | Variable | 1.0 | Electronic, pure sine wave |

#### Changing Instruments

**Via Web UI:**
- Navigate to http://localhost:5000
- Select instrument from dropdown

**Via Code:**
```python
system.audio_engine.set_instrument('electric_guitar')
```

**Via Config:**
```yaml
instruments:
  default: "acoustic_guitar"
```

### 2. **Audio Effects**

Real-time DSP effects for signal processing.

#### Reverb (Freeverb Algorithm)

Simulates acoustic space with multiple comb and allpass filters.

**Configuration:**
```yaml
effects:
  reverb:
    enabled: true
    room_size: 0.5        # 0-1, larger = longer reverb
    damping: 0.5          # 0-1, lower = duller
    wet_level: 0.3        # Effect volume
    dry_level: 0.7        # Original signal volume
```

#### Delay/Echo

Simple feedback delay for rhythmic effects.

**Configuration:**
```yaml
delay:
  enabled: true
  time_ms: 300            # Delay time
  feedback: 0.4           # 0-1, how much to feed back
```

#### Distortion

Soft-clipping saturation for warmth or aggression.

**Configuration:**
```yaml
distortion:
  enabled: true
  amount: 0.3             # 0-1, amount of coloration
```

#### Using Effects

**Enable/Disable via Web UI:**
- Click effect buttons (Reverb, Delay, Distortion)

**Programmatically:**
```python
engine.effects_chain.set_parameter('reverb', 'wet_level', 0.5)
engine.effects_chain.set_parameter('distortion', 'amount', 0.7)
```

### 3. **MIDI Output (DAW Integration)**

Send MIDI data to Digital Audio Workstations for integration with other synthesizers.

#### Configuration

```yaml
midi:
  enabled: true
  out_device: null        # null = system default
  midi_channel: 0         # 0-15
```

#### MIDI Features

- **Note On/Off**: Automatic when notes are triggered
- **Velocity**: Maps force to MIDI velocity (0-127)
- **Pitch Bend**: For future sliding/bending effects
- **All Notes Off**: Graceful shutdown

#### Setup

1. **Enable MIDI** in config.yaml
2. **Choose Output Device:**
   - Disable on `null` = uses system default
   - Use `LoopBe1` (Windows) or `IAC` (macOS) for DAW routing
3. **In your DAW:**
   - Create MIDI track
   - Set input to Air Guitar MIDI output
   - Route to any synthesizer

### 4. **WAV File Recording**

Record your performances to disk for playback, editing, or sharing.

#### Configuration

```yaml
recording:
  enabled: true
  auto_record: false      # Auto-start on launch
  output_folder: "./recordings"
  sample_rate: 44100
```

#### Recording Features

- **Auto-timestamped filenames**: `air_guitar_20240319_120530.wav`
- **Mono 44.1kHz**: CD-quality audio
- **Start/Stop via Web UI** or API

#### Recording API

```python
# Start recording
filename = engine.start_recording(session_name="jam_session")

# Stop recording
path = engine.stop_recording()

# Check if recording
if engine.is_recording():
    print("Currently recording")

# List all recordings
recordings = engine.recorder.list_recordings()

# Get duration of a recording
duration = engine.recorder.get_recording_duration("jam_20240319_120530.wav")
```

### 5. **Pitch Bending**

Modify note frequencies in real-time for expressive effects.

#### Features

- **Bend Curve**: Smooth frequency changes
- **Vibrato**: Periodic pitch modulation (4-8Hz typical)
- **Portamento**: Slide between notes

#### Example Code

```python
# Generate pitch bend curve (down to up 1 octave)
bend_curve = synthesizer.generate_bend_curve(
    duration_samples = 44100,  # 1 second
    start_mult = 0.5,          # Down 1 octave
    end_mult = 1.0             # Back to original
)

# Generate vibrato for expressive playing
vibrato = synthesizer.generate_vibrato(
    duration_samples = 44100,
    rate_hz = 5.0,             # Typical guitar vibrato
    depth = 0.05               # Subtle modulation
)
```

### 6. **Chord Detection**

Automatically detect when multiple strings are held simultaneously.

#### Configuration

```yaml
chord_detection:
  enabled: true
  simultaneous_notes_min: 2   # Minimum for chord detection
  angle_tolerance_chord: 4.0  # Wider angle range
```

#### How It Works

1. **Angle Crossing**: Detects string transitions (strumming)
2. **Simultaneous Hold**: Checks which strings are in current angle range
3. **Chord Recognition**: When 2+ strings held, marks as chord

#### API

```python
# Get currently held strings
held_strings = chord_engine.get_held_notes()
for string in held_strings:
    print(f"Holding: {string.note_name}")

# Dynamically change min notes for chord
chord_engine.simultaneous_notes_min = 3  # Require 3 for chord
```

### 7. **Web-Based Remote Control**

Full-featured dashboard for control and monitoring.

#### Features

✓ Real-time sensor monitoring  
✓ Instrument selection  
✓ Effect control  
✓ Recording start/stop  
✓ MIDI enable/disable  
✓ Active notes display  

#### Accessing Web UI

1. **Enable in config.yaml:**
   ```yaml
   web:
     enabled: true
     host: "127.0.0.1"
     port: 5000
     debug: false
   ```

2. **Open browser:**
   - http://localhost:5000
   - Or http://192.168.x.x:5000 from another machine

#### Customizing Web UI

Edit `web/templates/index.html` to customize:
- Layout and styling
- Control buttons
- Display information
- Theme colors

### Advanced Configuration Examples

#### Production Setup (Full Features)

```yaml
# config.yaml - Full featured setup
audio:
  sample_rate: 44100
  buffer_frames: 2048
  max_voices: 8
  decay_rate: 0.994

effects:
  enabled: true
  reverb:
    enabled: true
    room_size: 0.7
    damping: 0.4
    wet_level: 0.25
  delay:
    enabled: false
  distortion:
    enabled: false

instruments:
  default: "acoustic_guitar"

midi:
  enabled: true
  midi_channel: 0

recording:
  enabled: true
  output_folder: "./recordings"

web:
  enabled: true
  port: 5000
```

#### Performance Optimization (Low Latency)

```yaml
audio:
  buffer_frames: 512        # Smaller buffer = lower latency
  max_voices: 4             # Fewer voices = lower CPU

effects:
  enabled: false            # Disable for minimal latency

midi:
  enabled: false            # Disable if not needed
```

#### Studio Setup (Maximum Quality)

```yaml
audio:
  buffer_frames: 4096       # Larger buffer = better stability
  max_voices: 16            # More voices allowed

instruments:
  default: "classic_guitar"

effects:
  enabled: true
  reverb:
    enabled: true
    room_size: 0.8
    wet_level: 0.4

recording:
  enabled: true
  sample_rate: 44100
```

### Performance Metrics

| Feature | CPU Usage | Memory | Latency |
|---------|-----------|--------|---------|
| Base System | ~10% | 50MB | 50-100ms |
| + Reverb | +5% | +10MB | +5-10ms |
| + Delay | +3% | +5MB | +2-5ms |
| + Distortion | +1% | +1MB | <1ms |
| + MIDI | +2% | +2MB | <1ms |
| + Recording | +3% | variable | <1ms |
| + Web UI | +2% | +5MB | async |

### Troubleshooting

#### No Sound Output

**With Effects:**
1. Check effect parameters aren't muting signal
2. Verify `dry_level` > 0 in all effects
3. Try disabling effects to isolate issue

**With MIDI:**
1. Check MIDI device is selected correctly
2. Verify DAW is receiving MIDI notes
3. Check note velocity isn't 0

**With Recording:**
1. Verify output folder exists and is writable
2. Check disk space available
3. Look for WAV files in output folder

#### Poor Audio Quality

1. **Distortion?** Reduce voice count or disable some effects
2. **Latency?** Reduce buffer size in config (2048→1024→512)
3. **Glitching?** Increase buffer size or close other apps

#### MIDI Not Working

```python
# Check available MIDI outputs
import rtmidi
midout = rtmidi.MidiOut()
ports = midout.get_ports()
print(f"Available MIDI outputs: {ports}")

# If no ports, create virtual port
# Windows: Install LoopBe1
# macOS: Use IAC Driver (in Audio MIDI Setup)
# Linux: timidity -iAw (starts virtual port)
```

---

**All features working? Time to make some music!** 🎵

