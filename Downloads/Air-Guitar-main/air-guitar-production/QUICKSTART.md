# Quick Start Guide

Get Air Guitar running in 5 minutes.

## Prerequisites

- Python 3.8+
- Arduino Uno with uploaded `arduino_code.ino`
- MPU6050 sensor wired to Arduino
- USB cable to connect Arduino to PC

## Step 1: Install Dependencies (1 minute)

```bash
cd c:\Users\hardi\Downloads\Air-Guitar-main\air-guitar-production

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install all required packages
pip install -r requirements.txt

# Takes ~2 minutes. Watch for any errors about missing packages.
```

### Verify Installation

```bash
python -c "import numpy, sounddevice, yaml; print('✓ All dependencies installed')"
```

---

## Step 2: Find Your Arduino COM Port (2 minutes)

### Windows

1. Plug in Arduino via USB
2. Open **Device Manager** (press Windows key + X)
3. Expand **Ports (COM & LPT)**
4. Look for "Arduino Uno (COM#)" or "USB Serial Device (COM#)"
5. Note the COM port number (e.g., COM3, COM7)

### macOS

```bash
ls /dev/cu.usb*
# Should show: /dev/cu.usbserial-14101 or similar
```

### Linux

```bash
ls /dev/ttyUSB*
# Should show: /dev/ttyUSB0 or similar
```

---

## Step 3: Configure Arduino Port (1 minute)

Edit `config.yaml` in the air-guitar-production folder:

```yaml
# config.yaml - Update this line with YOUR Arduino port
serial:
  port: "COM3"                    # Change COM3 to your actual port!
  baudrate: 115200
  timeout: 1.0
```

Test the connection:

```bash
python -c "
from core.sensor_handler import SensorHandler
handler = SensorHandler('COM3', 115200)  # Use YOUR port
handler.start()
import time; time.sleep(2)
data = handler.read_sensor()
print('Sensor reading:', data)
handler.stop()
"
```

Should print something like: `Sensor reading: (512, 2048, 16384)`

---

## Step 4: Start the System (1 minute)

Run the main application:

```bash
python main.py
```

You should see output like:

```
[INFO] Initializing Air Guitar System...
[INFO] Audio engine: 44.1kHz, 8 voices, 0.994 decay
[INFO] Instruments: classic_guitar
[INFO] Effects: reverb, delay
[INFO] MIDI output: enabled
[INFO] Recording: enabled (./recordings/)
[INFO] Web UI: enabled (http://localhost:5000)
[INFO] ✓ System initialized successfully!
[INFO] Ready to play! Move your wrist and press force sensor...
```

---

## Step 5: Access the Dashboard

Open your web browser and go to:

```
http://localhost:5000
```

You should see the Air Guitar dashboard with:
- Real-time sensor readings (angle, force)
- Active notes display
- Recording controls
- Instrument selector
- Effect toggles

---

## First Performance

1. **Calibrate** (hold wrist neutral): Press spacebar in terminal to calibrate sensor zero-point
2. **Strum**:
   - Move wrist left-right across strings
   - Press force sensor to trigger notes
   - Listen to audio output
3. **Control**:
   - Change instrument: Select from dropdown in web UI
   - Toggle effects: Click reverb/delay buttons
   - Record: Click "Start Recording" button
4. **Stop**: Press Ctrl+C in terminal

---

## What You're Actually Hearing

When you trigger a string:

1. **Gesture Recognition** detects your wrist angle (which string)
2. **Synthesis Engine** generates realistic plucked string sound (440Hz = A4)
3. **Effects Pipeline** adds reverb (spacious) and delay (echoes)
4. **Audio Output** plays through your speakers

---

## Troubleshooting

### No Sound

**Check 1: Python is running**
```bash
# Should show no errors
python main.py
```

**Check 2: Arduino is connected**
```bash
# Verify sensor data
python -c "
from core.sensor_handler import SensorHandler
h = SensorHandler('COM3')
h.start()
import time; time.sleep(1)
print(h.read_sensor())  # Should print (x, y, z) values
h.stop()
"
```

**Check 3: Audio output** is selected
```bash
# List audio devices
python -c "
import sounddevice as sd
print(sd.query_devices())  # Find your speaker/headphones
"
```

### Arduino Not Responding

1. Unplug Arduino
2. Wait 5 seconds
3. Plug back in
4. Check COM port in Device Manager
5. Update config.yaml if port changed

### Web Dashboard Not Loading

1. Check that Flask is running (no errors in terminal)
2. Try: http://127.0.0.1:5000 instead of localhost
3. Some firewalls block port 5000—try port 8000:
   ```yaml
   web:
     port: 8000  # In config.yaml
   ```

---

## Next Steps

Once playing:

### Record Your Performance

```yaml
# In config.yaml
recording:
  auto_record: false
  output_folder: "./recordings"
```

Then click "Start Recording" in web UI. Files save with timestamps:
- `air_guitar_20240319_120530.wav` (44.1kHz mono)

### Use Different Instruments

Switch in web UI or config.yaml:
- **Classic Guitar** (warm, traditional)
- **Acoustic Guitar** (full body)
- **Electric Guitar** (bright, punchy)
- **Bass Guitar** (deep, sustained)
- **Synth String** (pure electronic tone)

### Send MIDI to DAW

Enable in config.yaml:
```yaml
midi:
  enabled: true
```

In your DAW (Ableton, FL Studio, etc.):
1. Create MIDI track
2. Set input to "Air Guitar OUT"
3. Arm track
4. Play on Air Guitar—sees MIDI notes

### Adjust Decay Rate

For longer sustain:
```yaml
audio:
  decay_rate: 0.996  # Higher = longer (default 0.994)
```

---

## Common Customizations

### Reduce Latency (for gaming/VR)

```yaml
audio:
  buffer_frames: 512    # Smaller = faster response (default 2048)
```

**Trade-off**: CPU usage increases slightly, audio may glitch on slow computers.

### Improve Sound Quality

Add more voices:
```yaml
audio:
  max_voices: 16        # Allow more playing simultaneously (default 8)
```

### Enable All Effects

```yaml
effects:
  reverb:
    enabled: true
    room_size: 0.7
    wet_level: 0.3
  delay:
    enabled: true
    feedback: 0.4
  distortion:
    enabled: true
    amount: 0.2
```

### Access From Phone/Laptop

Instead of localhost, find your PC's IP:

```bash
# Windows
ipconfig

# macOS/Linux
ifconfig
```

Look for `192.168.x.x` IPv4 address, then visit:
```
http://192.168.1.100:5000
```

---

## Performance Optimization

If you hear glitching or dropout:

1. **Close other apps** (Chrome, Discord, etc.)
2. **Increase buffer size**:
   ```yaml
   audio:
     buffer_frames: 4096
   ```
3. **Reduce voices**:
   ```yaml
   audio:
     max_voices: 4
   ```
4. **Disable effects**:
   ```yaml
   effects:
     enabled: false
   ```

---

## Next Level

Once comfortable:

1. Read [FEATURES.md](FEATURES.md) for advanced features
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
3. Read [API.md](API.md) for programming examples
4. Check [README.md](README.md) for full documentation

---

## Command Reference

| Goal | Command |
|------|---------|
| Start | `python main.py` |
| Stop | Ctrl+C |
| Test Sensor | `python -c "from core.sensor_handler import SensorHandler; ..."` |
| Test Audio | `python -c "from core.audio_engine import AudioEngine; ..."` |
| List Ports | `python -m serial.tools.list_ports` |
| View Config | `cat config.yaml` |

---

**Done! You're now ready to jam. 🎸**

Need help? Check [README.md](README.md) or [FEATURES.md](FEATURES.md).

