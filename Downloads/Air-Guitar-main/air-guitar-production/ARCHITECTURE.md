# Architecture & Implementation Details

Deep dive into the production system architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   SENSOR LAYER                          │
│  Arduino (IMU) ──[Serial @ 115200] ──> Python          │
│  • Accelerometer (acX, acY, acZ)                        │
│  • Frequency: 60Hz                                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              SENSOR PROCESSING LAYER                    │
│  • Calibration (zero-point offset)                      │
│  • Background thread with queue                         │
│  • Non-blocking reads                                   │
│  • Data validation                                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│            GESTURE RECOGNITION LAYER                    │
│  • Angle crossing detection (string triggering)         │
│  • Force threshold checking                             │
│  • Debouncing (prevent double-triggers)                 │
│  • Velocity calculation                                 │
│  • Chord detection (simultaneous notes)                 │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              SYNTHESIS & EFFECTS LAYER                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Instrument Models                                │  │
│  │ • Classic Guitar (Karplus-Strong)               │  │
│  │ • Acoustic (with resonance)                     │  │
│  │ • Electric (bright sustain)                     │  │
│  │ • Bass (deep/warm)                             │  │
│  │ • Synth (sine wave)                            │  │
│  └──────────────────────────────────────────────────┘  │
│                        ↓                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Voice Management & Mixing                        │  │
│  │ • Up to 8 simultaneous voices                    │  │
│  │ • Voice stealing (oldest removed)               │  │
│  │ • Real-time mixing with lock-free queue         │  │
│  └──────────────────────────────────────────────────┘  │
│                        ↓                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Effects Chain                                    │  │
│  │ ├─ Reverb (Freeverb algorithm)                 │  │
│  │ ├─ Delay (feedback echo)                       │  │
│  │ └─ Distortion (soft-clipping tanh)             │  │
│  └──────────────────────────────────────────────────┘  │
│                        ↓                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Output Routing                                   │  │
│  │ ├─ Audio Output (sounddevice @ 44.1kHz)         │  │
│  │ ├─ MIDI Output (to DAW)                         │  │
│  │ └─ WAV Recording (soundfile)                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              OUTPUT LAYER                               │
│  • Speakers (audio playback)                            │
│  • DAW (MIDI notes)                                     │
│  • Disk (WAV files)                                     │
│  • Web Dashboard (monitoring)                           │
└─────────────────────────────────────────────────────────┘
```

## File Structure

```
core/
├── audio_engine.py         (250 lines) - Voice management, mixing, effects integration
├── sensor_handler.py       (220 lines) - Serial I/O, calibration, background thread
├── chord_engine.py         (200 lines) - Gesture recognition, chord detection
├── note_generator.py       (180 lines) - Karplus-Strong synthesis, pitch bending
├── effects.py              (300 lines) - Reverb, delay, distortion chains
├── instrument_models.py    (350 lines) - 5 instrument algorithms with parameters
├── midi_output.py          (200 lines) - MIDI protocol interface
├── recorder.py             (120 lines) - WAV file I/O
└── exceptions.py           (20 lines)  - Custom exception hierarchy

utils/
├── logger.py               (40 lines)  - Logging configuration
├── validators.py           (50 lines)  - Input validation utilities
└── constants.py            (20 lines)  - Global constants

web/
├── controller.py           (200 lines) - Flask application, REST API
├── templates/
│   └── index.html          (400 lines) - Dashboard UI
└── static/                 - CSS/JS (future expansion)

main.py                      (200 lines) - System controller, event loop
config.yaml                  - User configuration (instruments, effects, etc.)
```

## Key Design Patterns

### 1. **Thread Safety**

All shared state uses threading locks:

```python
with self.voice_lock:
    # Modify self.voices safely
    self.voices[voice_id] = voice
```

### 2. **Non-Blocking I/O**

Sensor data read in background thread, main loop consumes from queue:

```
[Sensor Thread] ──> [Queue (size=1)] ──> [Main Loop]
                  (drops old data)
```

### 3. **Voice Stealing**

When max voices exceeded, remove oldest voice:

```python
if len(self.voices) >= self.max_voices:
    oldest_id = next(iter(self.voices))  # OrderedDict!
    del self.voices[oldest_id]
```

### 4. **Real-Time Callback Optimization**

Minimize work in audio callback:

```python
def _audio_callback(self, outdata, frames, time_info, status):
    # Fast mixing only
    mixed_audio = np.zeros(frames)
    for voice in self.voices:
        mixed_audio += voice.get_sample()  # O(n) operation
    
    # Effect processing (pre-computed outside callback)
    outdata[:] = self.effects.process(mixed_audio)
```

## Performance Optimization

### Memory

- **Voice Pre-allocation**: Generate 3-second buffers upfront (outside callback)
- **Buffer Reuse**: Use numpy in-place operations
- **Cache Locality**: Keep hot data compact

### CPU

- **Minimal Callback Work**: Only mixing and output
- **Voice Stealing**: Limit to 8 simultaneous notes
- **Effect Pipeline**: GPU-friendly operations (future)

### Latency

- **Buffer Size**: 2048 samples ≈ 46ms (tunable)
- **Thread Priority**: Audio thread runs at elevated priority
- **Queue Depth**: Sensor queue =1 (latest data only)

## Thread Model

```
┌─────────────────────────────────────────────────┐
│ Main Thread (Main Loop)                         │
│ • Event loop cycles ~60Hz (limited by sensor)  │
│ • Reads from sensor queue (non-blocking)        │
│ • Calls add_voice() (thread-safe via lock)     │
│ • Updates web state                             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Sensor Thread (SensorHandler)                   │
│ • Background daemon thread                      │
│ • Reads serial port continuously                │
│ • Puts latest data in queue                     │
│ • Blocks on serial I/O (OK, it's fast)         │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Audio Callback Thread (sounddevice)             │
│ • High-priority OS thread (WASAPI/ALSA/CoreAudio)
│ • Called ~44 times per second (at 44.1kHz)     │
│ • Generates 2048 samples (~46ms worth)         │
│ • Uses lock-free reads from voices OrderedDict│
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Web Server Thread (Flask)                       │
│ • Background daemon thread                      │
│ • Handles HTTP requests asynchronously          │
│ • Reads/writes system_state dict                │
│ • Non-blocking (doesn't affect audio)          │
└─────────────────────────────────────────────────┘
```

## Synthesis Algorithm: Karplus-Strong

The best algorithm for plucked string sounds:

1. **Initialize**: Fill buffer with white noise (pitch is buffer length)
2. **Feedback Loop**: Apply simple moving average damping filter
3. **Decay**: Higher damping factor = slower decay

```python
buf = np.random.randn(period)  # White noise
for i in range(duration):
    buf[i % period] = (buf[i % period] + buf[(i+1) % period]) * decay_rate
    samples[i] = buf[i % period]
```

Why this works:
- Resonant frequency naturally matches buffer period
- Moving average creates natural "string damping"
- Velocity scales initial noise level

## Effects Implementation

### Reverb (Freeverb)

```
Input
  ├─> Comb Filter 1 ─┐
  ├─> Comb Filter 2 ─┤
  ├─> Comb Filter 3 ─┤─> Series Allpass Filters ─> Output
  └─> Comb Filter 4 ─┘
```

### Delay

```
Input ──┬─> Delay Buffer ─┐
        └────────────────> Mixer ─> Output
                 (with feedback loop)
```

### Distortion

```
Input ──> Amplify ──> tanh() (soft-clip) ──> Output
```

## Testing Strategy

Run unit tests:

```bash
python -m pytest tests/test_audio_engine.py -v
```

Manual testing:

```python
# Test instrument models
for model_name in ['classic_guitar', 'electric_guitar', 'bass_guitar']:
    engine.set_instrument(model_name)
    engine.add_voice(440.0, velocity=0.8)  # A4

# Test effects
engine.effects_chain.set_parameter('reverb', 'wet_level', 0.5)
engine.effects_chain.set_parameter('distortion', 'amount', 0.7)

# Test recording
engine.start_recording('test_session')
time.sleep(5)
engine.stop_recording()

# Test MIDI
engine.midi.note_on(60)  # C3
time.sleep(1)
engine.midi.note_off()
```

---

**This architecture scales to thousands of lines of code while maintaining clarity and performance.**

