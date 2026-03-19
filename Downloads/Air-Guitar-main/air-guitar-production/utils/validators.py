"""Input validation utilities."""

def validate_port(port: str) -> bool:
    """
    Validate serial port format.
    
    Args:
        port: Port string (e.g., "COM3" on Windows, "/dev/ttyUSB0" on Linux)
    
    Returns:
        True if port is valid
    """
    return port and isinstance(port, str) and len(port) > 0

def validate_frequency(freq: float) -> bool:
    """
    Validate audio frequency range (20Hz - 20kHz).
    Valid human hearing range is 20Hz to 20kHz.
    
    Args:
        freq: Frequency in Hz
    
    Returns:
        True if frequency is within valid range
    """
    return 20 <= freq <= 20000

def validate_angle(angle: float) -> bool:
    """
    Validate roll angle range (-180 to +180 degrees).
    
    Args:
        angle: Angle in degrees
    
    Returns:
        True if angle is valid
    """
    return -180 <= angle <= 180

def validate_force(force: int) -> bool:
    """
    Validate force reading range (0-1000).
    This is the accelerometer magnitude from the Arduino.
    
    Args:
        force: Force magnitude
    
    Returns:
        True if force is within valid range
    """
    return 0 <= force <= 1000
