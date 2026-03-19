# Production Deployment Guide

Deploy Air Guitar for real-world use.

## Pre-Deployment Checklist

### Hardware
- [ ] Arduino Uno flashed with `arduino_code.ino`
- [ ] MPU6050 sensor properly calibrated
- [ ] Force sensor (FSR) connected and working
- [ ] USB cable tested for stability
- [ ] Power supply provides stable 5V
- [ ] All connections soldered (no breadboard flakes)

### Software
- [ ] Python 3.8+ installed with venv
- [ ] All dependencies installed via pip
- [ ] `config.yaml` has correct COM port
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] QUICKSTART.md verified manually
- [ ] Audio output tested (speakers/headphones)

### Performance
- [ ] CPU usage < 30% with 8 voices + reverb
- [ ] Memory usage < 200MB
- [ ] Audio latency < 100ms
- [ ] No buffer underruns or glitches

---

## Deployment Strategies

### Strategy 1: Single Machine (Development/Practice)

**Best for**: Personal use, bedroom playing, testing

```
Laptop/Desktop
├── Python runtime
├── Arduino (USB)
└── Speakers/Headphones
```

**Setup:**
```bash
python main.py
# Web UI at http://localhost:5000
```

**Pros:** Simple, no networking
**Cons:** Limited portability

---

### Strategy 2: Standalone App (Windows/Mac)

**Best for**: Distribution, performances without Python

Use PyInstaller to create executable:

```bash
pip install pyinstaller

# Create standalone executable
pyinstaller --onefile \
  --add-data "config.yaml:." \
  --add-data "templates:templates" \
  --hidden-import=rtmidi \
  main.py

# Creates: dist/main.exe
```

Users run: `main.exe` (no Python installation needed)

---

### Strategy 3: Network Deployment (Multi-Device)

**Best for**: Live performances with band, venue setup

```
┌──────────────────┐         WiFi       ┌──────────────────┐
│ Air Guitar Box   │◄──────────────────►│ Control Laptop   │
│ (Python + Uno)   │                    │ (Web Browser)    │
│ port: 5000       │                    │ http://192.x.x.x │
└──────────────────┘                    └──────────────────┘
       ▼
   Speakers
```

**Setup:**

1. On Air Guitar machine:
```yaml
# config.yaml
web:
  host: "0.0.0.0"        # Accept all connections
  port: 5000
```

2. On control machine:
Open browser to: `http://192.168.1.100:5000`

3. Network:
- WiFi router (5GHz recommended for low latency)
- Ethernet if possible (directly wired)

---

### Strategy 4: Cloud Streaming (Remote Performance)

**Best for**: YouTube/Twitch streaming, remote collaboration

**OBS Setup:**
```
Air Guitar Audio Output
    ↓
OBS Audio Input (line-in)
    ↓
OBS → YouTube/Twitch Live Stream
```

**Low-latency streaming:**
- Bitrate: 48kHz audio, 320kbps
- Platform: YouTube (15-20s latency)
- Latency: Accept 2-5 seconds for streaming

---

## Configuration for Production

### High-Reliability Config

```yaml
# config.yaml - Production
audio:
  sample_rate: 44100      # CD quality
  buffer_frames: 4096     # Stable, less glitchy
  max_voices: 8

serial:
  port: "COM3"
  baudrate: 115200
  timeout: 1.0

instruments:
  default: "acoustic_guitar"

effects:
  reverb:
    enabled: true
    room_size: 0.5        # Conservative
    wet_level: 0.25
  delay:
    enabled: false        # Optional for production
  distortion:
    enabled: false

midi:
  enabled: true           # For DAW integration

recording:
  enabled: true
  output_folder: "./recordings"
  sample_rate: 44100

web:
  enabled: true
  host: "0.0.0.0"        # Accept external connections
  port: 5000
  debug: false            # Disable debug info in production
```

### High-Performance Config (Low Latency)

```yaml
# config.yaml - Gaming/VR
audio:
  sample_rate: 44100
  buffer_frames: 512      # Low latency (~12ms)
  max_voices: 4           # Fewer = less CPU

effects:
  reverb:
    enabled: false        # Disable for lowest latency
  delay:
    enabled: false

recording:
  enabled: false          # Disable if not needed

web:
  host: "127.0.0.1"      # Local only
  port: 5000
  debug: false
```

---

## Containerization (Docker)

Deploy in container for consistency:

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose web port
EXPOSE 5000

# Run main application
CMD ["python", "main.py"]
```

**Build & Run:**
```bash
docker build -t air-guitar:1.0 .
docker run -it --device /dev/ttyUSB0 air-guitar:1.0
```

---

## Error Handling & Recovery

### Auto-Restart on Crash

**Windows Batch Script** (auto_restart.bat):
```batch
@echo off
:restart
python main.py
if errorlevel 1 (
    echo Error detected, restarting in 5 seconds...
    timeout /t 5
    goto restart
)
```

Run once, restarts forever.

### Graceful Shutdown

Main loop catches Ctrl+C:
```python
try:
    while True:
        # Main loop
        pass
except KeyboardInterrupt:
    print("Shutting down gracefully...")
    audio_engine.stop()
    sensor_handler.stop()
    recorder.finalize()
    web_controller.stop()
    print("Goodbye!")
```

### Log File Rotation

Logs grow. Prevent disk full:

```python
# main.py - Use RotatingFileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'air_guitar.log',
    maxBytes=10*1024*1024,  # 10MB per file
    backupCount=5           # Keep 5 old files
)
```

---

## Monitoring in Production

### Simple Health Check

Create endpoint to verify system is alive:

```python
# In web/controller.py
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'uptime_seconds': time.time() - start_time,
        'voice_count': engine.get_voice_count(),
        'recording': engine.is_recording()
    })
```

Check from external monitor:
```bash
curl http://localhost:5000/health
```

### Automated Monitoring Script

```python
# monitor.py
import requests
import time

HEALTH_CHECK_URL = 'http://localhost:5000/health'
CHECK_INTERVAL = 60  # Every minute

while True:
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        data = response.json()
        
        if data['status'] == 'healthy':
            print(f"✓ System healthy | Voices: {data['voice_count']}")
        else:
            print(f"✗ System unhealthy!")
            # Send alert/email
            
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        # Send alert/email
        # Optionally restart
        # os.system('restart_air_guitar.bat')
    
    time.sleep(CHECK_INTERVAL)
```

---

## Backup & Recovery

### Configuration Backup

```bash
# Backup before deployment
cp config.yaml config.yaml.backup.$(date +%Y%m%d_%H%M%S)

# Restore if needed
cp config.yaml.backup.20240319_120530 config.yaml
```

### Recording Backup

```bash
# Regular backup to external drive
robocopy ./recordings D:\recordings /MIR

# Or cloud:
rclone sync ./recordings dropbox:air_guitar_backups
```

### Full System Backup

```sh
# Create version snapshot
tar -czf air_guitar_$(date +%Y%m%d).tar.gz \
  main.py core/ web/ config.yaml requirements.txt
```

---

## Security Considerations

### Web UI Access Control

**Restrict to local network only:**
```yaml
web:
  host: "192.168.1.100"  # Your machine's IP, not 0.0.0.0
  port: 5000
```

**Add password protection** (future enhancement):
```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    return credentials.get(username) == password

@app.route('/api/state')
@auth.login_required
def get_state():
    ...
```

### Serial Communication

Validate Arduino data:
```python
def validate_sensor_data(acX, acY, acZ):
    # Check ranges
    assert -32768 <= acX <= 32767, "Invalid acX"
    assert -32768 <= acY <= 32767, "Invalid acY"
    assert -32768 <= acZ <= 32767, "Invalid acZ"
    return True
```

---

## Performance Tuning

### CPU Optimization

**Profile the code:**
```bash
pip install py-spy
py-spy record -o profile.svg -- python main.py

# Open profile.svg in browser
```

**Hot spots typically are:**
1. Audio synthesis → Optimize Karplus-Strong
2. Effect processing → Use numpy vectorization
3. Voice mixing → Reduce max_voices

### Memory Optimization

```python
# Pre-allocate buffers outside callback
synthesis_buffer = np.zeros(44100 * 3)  # 3 seconds

# In callback, reuse without allocation
voice.get_sample(synthesis_buffer)  # Fill in-place
```

### Network Optimization

If using remote web UI:

```python
# Reduce state broadcast frequency
web_controller.broadcast_interval = 1.0  # 1 second instead of 0.5
```

---

## Scaling Beyond Single Device

### Multiple Sensors (Multiple Musicians)

```
Musician 1: Air Guitar 1 (COM3)
Musician 2: Air Guitar 2 (COM5)
Musician 3: Air Guitar 3 (COM7)
    ↓
Central Control PC
    ├─ Master mixer
    ├─ MIDI router  
    └─ Recorder
```

Would require:
1. Multiple SensorHandler instances
2. Central MIDIRouter to combine notes
3. Web UI showing all 3 musicians

### Live Performance Setup

```
┌──────────────┐
│ Air Guitar   │─ Audio output → PA System
│ (on stage)   │─ MIDI output → Band members' keyboards
└──────────────┘
       ↑
WiFi connection
       ↑
┌──────────────────┐
│ Control Laptop   │
│ (monitor/lights) │─ Web UI for effects/recording
└──────────────────┘
```

---

## Troubleshooting Production Issues

### System Crash on Startup

**Check logs:**
```bash
# Look for errors
type air_guitar.log | tail -50
```

**Common causes:**
- Wrong COM port → Update config.yaml
- Missing dependency → pip install -r requirements.txt
- Arduino not connected → Check USB cable

### Audio Dropout/Glitching

**Diagnosis:**
1. Is CPU >50%? → Reduce max_voices or buffer size
2. Is buffer underrunning? → Increase buffer_frames
3. Is other software blocking audio? → Close Chrome, Discord, etc.

**Fix priority:**
1. Increase buffer_frames (4096+)
2. Disable reverb/delay if not needed
3. Reduce max_voices
4. Upgrade PC hardware

### Memory Leak

**Detect:**
```python
# In monitoring script
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

**Common causes:**
- Event queue growing unbounded
- Recordings not cleared
- Web subscribers not cleaned up

**Fix:**
- Add max_size to queue
- Implement log rotation
- Add unsubscribe mechanism

---

## Version Management

### Semantic Versioning

Use format: `MAJOR.MINOR.PATCH`

```
1.0.0  - Initial release
1.0.1  - Bug fixes
1.1.0  - New features (backward compatible)
2.0.0  - Breaking changes
```

### Version File

```python
# core/version.py
__version__ = '1.0.0'
__release_date__ = '2024-03-19'
__author__ = 'Your Name'
```

### Changelog

```markdown
# Changelog

## [1.0.0] - 2024-03-19
### Added
- Multi-instrument support (5 models)
- MIDI output integration
- WAV recording
- Web dashboard
- Audio effects (reverb, delay, distortion)

### Fixed
- Serial communication stability
- Voice stealing algorithm
```

---

## Updating in Production

### Zero-Downtime Update (Future Enhancement)

1. Have backup Air Guitar instance
2. Upgrade one while other handles requests
3. Switch router/DNS when ready

For now: Scheduled maintenance window needed

### Rollback Procedure

```bash
# If new version has critical issue
git log --oneline                 # See previous versions
git checkout v1.0.0              # Go back to previous version
python main.py                    # Run old version
```

---

## Support & Maintenance

### Monthly Maintenance

- [ ] Check disk space (recordings folder)
- [ ] Review logs for errors
- [ ] Test MIDI with DAW
- [ ] Backup config.yaml
- [ ] Update dependencies: `pip list --outdated`

### Quarterly Reviews

- [ ] Run full test suite
- [ ] Profile CPU/memory usage
- [ ] Check GitHub for security updates
- [ ] Review user feedback
- [ ] Plan feature updates

---

**Your Air Guitar is now production-ready!**

Questions? Refer to README.md or open an issue on GitHub.

