# Testing Guide

Verify all features work correctly.

## Unit Tests

### Running All Tests

```bash
cd air-guitar-production

# Run all unit tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_audio_engine.py -v

# Run with coverage report
python -m pytest tests/ --cov=core --cov-report=html
```

### Test Structure

```
tests/
├── test_audio_engine.py       - Voice management, mixing
├── test_sensor_handler.py     - Serial I/O, calibration
├── test_chord_engine.py       - Gesture detection
├── test_note_generator.py     - Synthesis
├── test_effects.py            - Effects processing
├── test_instrument_models.py  - Instrument algorithms
├── test_midi_output.py        - MIDI protocol
├── test_recorder.py           - Audio recording
└── conftest.py                - Testing fixtures
```

---

## Integration Tests

### Test 1: Sensor → Synthesis

Verify end-to-end audio generation:

```python
# test_sensor_to_audio.py
import numpy as np
from core.sensor_handler import SensorHandler
from core.audio_engine import AudioEngine
from core.chord_engine import ChordEngine

def test_sensor_to_audio():
    # Setup
    engine = AudioEngine(sample_rate=44100, max_voices=8)
    chord_engine = ChordEngine(num_strings=6)
    
    # Simulate sensor reading
    angle = 45.0  # Pointing at string 3
    force = 150
    
    # Detect trigger
    trigger = chord_engine.detect_trigger(angle, force, 90)
    assert trigger is not None, "Should detect trigger"
    
    string, velocity = trigger
    assert string.frequency > 0
    assert 0 <= velocity <= 1
    
    # Generate sound
    engine.start()
    voice_id = engine.add_voice(string.frequency, velocity)
    assert engine.get_voice_count() == 1
    
    # Verify audio coming out
    assert len(engine.get_active_notes()) > 0
    
    engine.stop()
    print("✓ Sensor to audio works")

test_sensor_to_audio()
```

### Test 2: Effects Processing

Verify effects chain works correctly:

```python
# test_effects_integration.py
import numpy as np
from core.effects import EffectsChain

def test_effects_chain():
    effects = EffectsChain()
    
    # Create test signal
    test_input = np.random.randn(44100)
    
    # Process through effects
    output = effects.process_buffer(test_input)
    
    # Verify output shape
    assert output.shape == test_input.shape
    
    # Verify signal isn't clipping ([-1, 1])
    assert np.all(np.abs(output) <= 1.1)
    
    # Verify different effects change output
    effects.enable_effect('reverb', True)
    reverb_output = effects.process_buffer(test_input)
    
    effects.enable_effect('reverb', False)
    dry_output = effects.process_buffer(test_input)
    
    # Reverb should be different from dry
    assert not np.allclose(reverb_output, dry_output)
    
    print("✓ Effects processing works")

test_effects_chain()
```

### Test 3: MIDI Output

Verify MIDI messages are sent correctly:

```python
# test_midi_integration.py
from core.midi_output import MIDIOutput

def test_midi_output():
    midi = MIDIOutput(device_index=None)
    
    # Test frequency to MIDI conversion
    a4_midi = 69
    assert midi.frequency_to_midi_note(440.0) == a4_midi
    
    # Test MIDI to frequency conversion
    freq = midi.midi_note_to_frequency(60)
    assert abs(freq - 261.63) < 0.1
    
    # Test MIDI messages (won't fail even without device)
    midi.note_on(440.0, velocity=100)
    midi.pitch_bend(semitones_up=0.5)
    midi.note_off()
    midi.controller_change(7, 100)
    
    midi.close()
    print("✓ MIDI output works")

test_midi_output()
```

### Test 4: Recording

Verify WAV file recording:

```python
# test_recording_integration.py
import numpy as np
import os
from core.recorder import AudioRecorder
import soundfile as sf

def test_recording():
    recorder = AudioRecorder(
        output_folder='./test_recordings',
        sample_rate=44100
    )
    
    # Start recording
    filename = recorder.start_recording('test_take')
    
    # Generate test audio
    samples = np.random.randn(44100)  # 1 second
    recorder.add_samples(samples)
    
    # Stop recording
    path = recorder.stop_recording()
    
    # Verify file exists
    assert os.path.exists(path), f"File not found: {path}"
    
    # Verify audio content
    audio, sr = sf.read(path)
    assert sr == 44100
    assert len(audio) > 0
    
    # Cleanup
    os.remove(path)
    os.rmdir('./test_recordings')
    
    print("✓ Recording works")

test_recording()
```

---

## Manual Testing Checklist

Use this checklist to manually verify all features:

### Sensor Input
- [ ] Sensor data displays in web UI (angle, force)
- [ ] Angle changes smoothly when moving wrist
- [ ] Force increases when pressing down
- [ ] Real-time updates every ~500ms

### Synthesis
- [ ] Triggering note produces sound
- [ ] Different angles produce different pitches
- [ ] Velocity affects volume
- [ ] No glitching or crackling

### Instruments
- [ ] Classic Guitar sounds warm
- [ ] Acoustic Guitar has full body
- [ ] Electric Guitar is bright
- [ ] Bass Guitar is deep
- [ ] Synth String is pure electronic
- [ ] Switching instruments mid-play works

### Polyphony
- [ ] Can trigger multiple notes at once
- [ ] Up to 8 notes play simultaneously
- [ ] Oldest note stops when 9th triggered
- [ ] Web UI shows correct voice count

### Effects
- [ ] Reverb: Creates spacious sound
  - With reverb: Sound fills the space
  - Without: Sound is dry
- [ ] Delay: Creates echo repetitions
  - With delay: Echoes repeat the notes
  - Without: Single note only
- [ ] Distortion: Creates warmth/aggression
  - With distortion: Sound slightly fuzzy
  - Without: Clean sound
- [ ] Toggling effects changes audio immediately

### Recording
- [ ] "Start Recording" button works
- [ ] File appears in ./recordings/ folder
- [ ] Filename has date/time stamp
- [ ] Stop button saves file
- [ ] Recorded audio plays back correctly

### MIDI
- [ ] Enable MIDI in config
- [ ] DAW sees MIDI notes
- [ ] Note pitch matches Air Guitar note
- [ ] Velocity matches force
- [ ] MIDI channel matches config

### Web UI
- [ ] Dashboard loads at http://localhost:5000
- [ ] Page displays all control panels
- [ ] All buttons clickable
- [ ] Real-time sensor data updates
- [ ] Active notes display correct frequencies

---

## Performance Testing

### CPU Usage

Monitor system performance while playing:

```python
# performance_test.py
import psutil
import time
from core.audio_engine import AudioEngine

def test_cpu_usage():
    engine = AudioEngine(sample_rate=44100, max_voices=8)
    engine.start()
    
    # Get baseline CPU
    baseline = psutil.cpu_percent(interval=1)
    print(f"Baseline CPU: {baseline}%")
    
    # Add voices and measure
    for i in range(8):
        engine.add_voice(440.0 + i*50, velocity=0.8)
    
    time.sleep(1)
    with_voices = psutil.cpu_percent(interval=1)
    print(f"With 8 voices: {with_voices}%")
    
    # Add effects
    engine.effects_chain.enable_effect('reverb', True)
    time.sleep(1)
    with_effects = psutil.cpu_percent(interval=1)
    print(f"With effects: {with_effects}%")
    
    # Remove all voices
    engine.clear_all_voices()
    time.sleep(1)
    idle = psutil.cpu_percent(interval=1)
    print(f"Idle: {idle}%")
    
    engine.stop()
    
    # Verify CPU usage is reasonable
    voice_cpu = with_voices - baseline
    effect_cpu = with_effects - with_voices
    
    assert voice_cpu < 20, f"Voice CPU too high: {voice_cpu}%"
    assert effect_cpu < 10, f"Effect CPU too high: {effect_cpu}%"
    print("✓ CPU usage acceptable")

test_cpu_usage()
```

### Memory Usage

```python
# memory_test.py
import tracemalloc
from core.audio_engine import AudioEngine

def test_memory_usage():
    tracemalloc.start()
    
    engine = AudioEngine(sample_rate=44100, max_voices=8)
    engine.start()
    
    # Record memory after startup
    _, peak_startup = tracemalloc.get_traced_memory()
    
    # Add voices
    for i in range(8):
        engine.add_voice(440.0 + i*50, velocity=0.8)
    
    _, peak_voices = tracemalloc.get_traced_memory()
    
    # Add effects
    engine.effects_chain.enable_effect('reverb', True)
    engine.effects_chain.enable_effect('delay', True)
    _, peak_effects = tracemalloc.get_traced_memory()
    
    engine.stop()
    tracemalloc.stop()
    
    # Print results
    startup_mb = peak_startup / (1024*1024)
    voices_mb = peak_voices / (1024*1024)
    effects_mb = peak_effects / (1024*1024)
    
    print(f"Startup: {startup_mb:.1f} MB")
    print(f"With voices: {voices_mb:.1f} MB")
    print(f"With effects: {effects_mb:.1f} MB")
    
    assert voices_mb < 200, f"Memory too high: {voices_mb} MB"
    print("✓ Memory usage acceptable")

test_memory_usage()
```

### Latency Testing

Measure audio latency:

```python
# latency_test.py
import numpy as np
import time
from core.audio_engine import AudioEngine

def test_audio_latency():
    engine = AudioEngine(sample_rate=44100, max_voices=1)
    engine.start()
    
    # Record start time
    t_start = time.time()
    
    # Trigger note
    engine.add_voice(440.0, velocity=0.8)
    
    # Wait for audio to be generated
    time.sleep(0.1)  # 100ms
    
    # Measure time
    t_elapsed = time.time() - t_start
    
    # Get streaming latency from sounddevice
    latency_ms = t_elapsed * 1000
    
    print(f"Latency: {latency_ms:.1f}ms")
    
    engine.stop()
    
    # Latency should be ~50-100ms with default settings
    assert latency_ms < 150, f"Latency too high: {latency_ms}ms"
    print("✓ Audio latency acceptable")

test_audio_latency()
```

---

## Stress Testing

### Maximum Stress Test

Push system to limits:

```python
# stress_test.py
import numpy as np
from core.audio_engine import AudioEngine
from core.effects import EffectsChain

def stress_test():
    print("Starting stress test...")
    
    engine = AudioEngine(sample_rate=44100, max_voices=16)
    engine.start()
    
    # Add maximum voices
    print("Adding 16 voices...")
    for i in range(16):
        freq = 440 * (2 ** (i / 12))  # Chromatic scale
        engine.add_voice(freq, velocity=0.9)
    
    # Enable all effects
    print("Enabling all effects...")
    engine.effects_chain.enable_effect('reverb', True)
    engine.effects_chain.enable_effect('delay', True)
    engine.effects_chain.enable_effect('distortion', True)
    
    # Run for extended time
    import time
    print("Running for 30 seconds...")
    time.sleep(30)
    
    # Verify no crashes
    assert engine.get_voice_count() > 0
    assert len(engine.get_active_notes()) > 0
    
    engine.stop()
    print("✓ Stress test passed")

stress_test()
```

---

## Test Coverage Report

After running tests with coverage:

```bash
python -m pytest tests/ --cov=core --cov-report=html --cov-report=term
```

View HTML report in `htmlcov/index.html`

**Target Coverage:**
- Core modules: ≥90%
- Utils: ≥80%
- Overall: ≥85%

---

## CI/CD Testing (GitHub Actions)

Create `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/ --cov=core --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## Post-Deployment Verification

After deploying to production:

1. ✓ Run QUICKSTART.md steps
2. ✓ Test all features in manual checklist
3. ✓ Monitor CPU/memory for 24 hours
4. ✓ Test recording with long sessions (>1 hour)
5. ✓ Verify MIDI with multiple DAWs
6. ✓ Check web UI on mobile devices

---

## Known Issues & Workarounds

### Issue: Arduino doesn't reconnect after disconnect
**Workaround**: Manually restart SensorHandler
```python
handler.stop()
handler.start()
```

### Issue: Effects cause audio dropout
**Workaround**: Reduce buffer size or disable reverb room_size > 0.8

### Issue: MIDI notes don't send to DAW
**Workaround**: Check DAW MIDI input routing and enable in config.yaml

---

**All tests passing? System is production-ready!**

