"""Custom exceptions for Air Guitar application."""

class AirGuitarException(Exception):
    """Base exception for all Air Guitar errors."""
    pass

class SerialConnectionError(AirGuitarException):
    """Raised when serial connection fails."""
    pass

class SensorCalibrationError(AirGuitarException):
    """Raised when sensor calibration fails."""
    pass

class AudioEngineError(AirGuitarException):
    """Raised when audio engine initialization fails."""
    pass

class ConfigurationError(AirGuitarException):
    """Raised when configuration is invalid."""
    pass
