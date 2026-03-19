"""Sensor data acquisition from Arduino via serial communication."""
import serial
import time
import threading
import logging
from typing import Callable, Optional
from queue import Queue

from .exceptions import SerialConnectionError, SensorCalibrationError
from utils.logger import setup_logger
from utils.validators import validate_port, validate_angle, validate_force

logger = setup_logger(__name__)

class SensorData:
    """Container for IMU sensor readings with timestamp."""
    
    def __init__(self, roll: float, force: int):
        self.roll = roll  # Wrist angle in degrees
        self.force = force  # Acceleration magnitude
        self.timestamp = time.time()
    
    def __repr__(self):
        return f"SensorData(roll={self.roll:.1f}°, force={self.force})"

class SensorHandler:
    """
    Thread-safe serial communication handler for Arduino IMU data.
    
    Features:
    - Automatic serial port connection/reconnection
    - Sensor calibration (zero-point offset)
    - Background reading thread with queue (non-blocking)
    - Data validation and filtering
    - Graceful error handling
    
    The Arduino sends data in format: ROLL:FORCE
    where ROLL is wrist angle in degrees, FORCE is acceleration magnitude.
    """
    
    def __init__(self, port: str, baud_rate: int = 115200, timeout: float = 0.01):
        if not validate_port(port):
            raise SerialConnectionError(f"Invalid port: {port}")
        
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_port = None
        
        # Calibration offset (zero point)
        self.roll_offset = 0.0
        self.is_calibrated = False
        
        # Background reading thread with queue
        # Queue size=1 means we keep only the latest data (drops old data if slow)
        self.data_queue = Queue(maxsize=1)
        self.reading_thread = None
        self._stop_reading = threading.Event()
        
        logger.info(f"SensorHandler initialized for {port} @ {baud_rate} baud")
    
    def connect(self) -> None:
        """Establish serial connection to Arduino."""
        try:
            self.serial_port = serial.Serial(
                self.port, 
                self.baud_rate, 
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for Arduino to reset and initialize
            logger.info(f"Connected to {self.port}")
        except serial.SerialException as e:
            logger.error(f"Serial connection failed: {e}")
            raise SerialConnectionError(f"Cannot open port {self.port}") from e
    
    def disconnect(self) -> None:
        """Close serial connection."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            logger.info("Disconnected from serial port")
    
    def calibrate(self, duration_seconds: float = 1.5) -> float:
        """
        Calibrate sensor zero point. User must keep hand neutral during calibration.
        
        This measurement is used as an offset to make roll=0 the "hand neutral" position.
        
        Args:
            duration_seconds: Calibration duration in seconds
        
        Returns:
            Calibration offset value
        """
        if not self.serial_port or not self.serial_port.is_open:
            raise SerialConnectionError("Serial port not connected")
        
        print("\n🎸 SENSOR CALIBRATION")
        print("   Hold hand in neutral position...")
        time.sleep(3)
        print(f"   Calibrating for {duration_seconds} seconds...")
        
        roll_readings = []
        start_time = time.time()
        
        # Collect raw sensor readings
        while time.time() - start_time < duration_seconds:
            try:
                data = self._read_raw_data()
                if data:
                    roll, force = data
                    if validate_angle(roll):
                        roll_readings.append(roll)
            except Exception as e:
                logger.debug(f"Calibration read error: {e}")
        
        if not roll_readings:
            raise SensorCalibrationError("No valid readings during calibration")
        
        # Calculate median (more robust to outliers than mean)
        roll_readings.sort()
        self.roll_offset = roll_readings[len(roll_readings) // 2]
        self.is_calibrated = True
        
        logger.info(f"Calibration complete. Offset: {self.roll_offset:.2f}°")
        print(f"   ✓ Done! Zero point: {self.roll_offset:.1f}°\n")
        return self.roll_offset
    
    def _read_raw_data(self) -> Optional[tuple]:
        """
        Read raw sensor data from serial port.
        Expected format: "ROLL:FORCE\n" where ROLL is float, FORCE is int.
        
        Returns:
            Tuple of (roll, force) or None if no valid data available
        """
        if not self.serial_port or not self.serial_port.in_waiting:
            return None
        
        try:
            line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
            if ":" in line:
                roll_str, force_str = line.split(":")
                roll = float(roll_str)
                force = int(force_str)
                
                # Validate readings before returning
                if validate_angle(roll) and validate_force(force):
                    return (roll, force)
        except (ValueError, AttributeError) as e:
            logger.debug(f"Parse error: {e}")
        
        return None
    
    def _reading_loop(self) -> None:
        """
        Continuous background reading thread.
        This runs in a separate thread and continuously reads from serial,
        putting the latest data into a queue for the main thread to consume.
        """
        while not self._stop_reading.is_set():
            raw_data = self._read_raw_data()
            if raw_data:
                roll, force = raw_data
                # Apply calibration offset to roll
                calibrated_roll = roll - self.roll_offset
                
                # Put latest data in queue (drops old unprocessed data)
                try:
                    self.data_queue.put_nowait(
                        SensorData(calibrated_roll, force)
                    )
                except:
                    pass  # Queue full, drop old data (OK for real-time)
            else:
                time.sleep(0.001)  # Small sleep to avoid busy-loop
    
    def start_reading(self) -> None:
        """Start background sensor reading thread."""
        if not self.reading_thread or not self.reading_thread.is_alive():
            self._stop_reading.clear()
            self.reading_thread = threading.Thread(
                target=self._reading_loop, 
                daemon=True
            )
            self.reading_thread.start()
            logger.info("Sensor reading thread started")
    
    def stop_reading(self) -> None:
        """Stop background sensor reading."""
        self._stop_reading.set()
        if self.reading_thread:
            self.reading_thread.join(timeout=1.0)
        logger.info("Sensor reading thread stopped")
    
    def get_latest_data(self) -> Optional[SensorData]:
        """
        Get latest sensor data (non-blocking).
        Returns None if no new data available.
        
        This is called in the main loop to get the current sensor state.
        """
        try:
            return self.data_queue.get_nowait()
        except:
            return None
