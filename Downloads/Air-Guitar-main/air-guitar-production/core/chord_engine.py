"""Chord detection and multi-note voice management."""
import time
import logging
from typing import List, Set

from utils.logger import setup_logger

logger = setup_logger(__name__)

class VirtualString:
    """
    Represents a virtual string on the air guitar.
    Each string is defined by an angle (wrist position) and a musical note frequency.
    """
    
    def __init__(self, angle: float, note_name: str, frequency: float):
        self.angle = angle  # Wrist angle where this string is located
        self.note_name = note_name  # Human-readable name (e.g., "E2")
        self.frequency = frequency  # Note frequency in Hz
        self.last_triggered = 0.0  # Timestamp for debouncing
    
    def is_in_range(self, angle: float, tolerance: float = 2.0) -> bool:
        """Check if current angle is within string's range."""
        return abs(angle - self.angle) <= tolerance
    
    def __repr__(self):
        return f"{self.note_name}({self.angle}°, {self.frequency:.1f}Hz)"

class ChordEngine:
    """
    Intelligent chord and note detection engine.
    
    Handles:
    - Single note triggering when wrist angle crosses a string
    - Multi-note chord detection (future feature)
    - Debouncing to prevent double-triggering
    - Force-based dynamics (velocity)
    
    The core detection mechanism: as you rotate your wrist, it "strums"
    across the virtual strings. When the angle crosses a string's position,
    that note is triggered.
    """
    
    def __init__(
        self, 
        strings: List[dict],
        min_force: int = 140,
        debounce_ms: float = 100.0,
        angle_tolerance: float = 2.0
    ):
        """
        Args:
            strings: List of string dicts with 'angle', 'note', 'freq'
            min_force: Minimum force threshold to trigger a note
            debounce_ms: Debounce time in milliseconds (prevent rapid re-triggers)
            angle_tolerance: Angle tolerance range for string detection
        """
        # Create VirtualString objects from config
        self.strings = [
            VirtualString(s['angle'], s['note'], s['freq'])
            for s in strings
        ]
        # Sort by angle for efficient crossing detection
        self.strings.sort(key=lambda s: s.angle)
        
        self.min_force = min_force
        self.debounce_ms = debounce_ms
        self.angle_tolerance = angle_tolerance
        
        # State tracking for angle crossing detection
        self.prev_angle = None
        
        logger.info(f"ChordEngine initialized with {len(self.strings)} strings")
        for string in self.strings:
            logger.debug(f"  {string}")
    
    def detect_trigger(self, current_angle: float, force: int) -> List[tuple]:
        """
        Detect if any strings should be triggered based on wrist angle and force.
        
        The algorithm:
        1. Check if force is above minimum threshold (insufficient force = no trigger)
        2. Check if wrist angle has crossed any string positions
        3. Apply debouncing to prevent double-triggers
        4. Calculate velocity based on force magnitude
        
        Args:
            current_angle: Current wrist angle in degrees
            force: Force/acceleration magnitude
        
        Returns:
            List of (VirtualString, velocity) tuples to trigger
        """
        triggers = []
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # If force is too low, we're not "strumming" - no triggers
        if force < self.min_force:
            self.prev_angle = current_angle
            return triggers
        
        # First reading - no previous angle to compare
        if self.prev_angle is None:
            self.prev_angle = current_angle
            return triggers
        
        # Check each string for crossing
        for string in self.strings:
            # Has this string been triggered recently? (debounce)
            if current_time - string.last_triggered < self.debounce_ms:
                continue
            
            # Did angle cross this string's position since last reading?
            crossing = self._detect_angle_crossing(
                self.prev_angle, 
                current_angle, 
                string.angle
            )
            
            if crossing:
                # Calculate velocity based on force (0-1 range)
                # Higher force = brighter, louder attack
                velocity = min(force / 500.0, 1.0)
                triggers.append((string, velocity))
                
                # Update debounce timestamp
                string.last_triggered = current_time
                logger.debug(f"Triggered {string} with velocity {velocity:.2f}")
        
        # Save current angle for next iteration
        self.prev_angle = current_angle
        return triggers
    
    def _detect_angle_crossing(self, prev_angle: float, curr_angle: float, threshold: float) -> bool:
        """
        Detect if wrist rotation crossed a string's angle.
        Used for "strumming" detection - determines the order of notes.
        
        Args:
            prev_angle: Previous wrist angle
            curr_angle: Current wrist angle
            threshold: String's angle position
        
        Returns:
            True if angle crossed the threshold
        """
        # Detect crossing in both directions (left-to-right and right-to-left)
        down_cross = (prev_angle > threshold >= curr_angle)  # Rotating right
        up_cross = (prev_angle < threshold <= curr_angle)   # Rotating left
        return down_cross or up_cross
    
    def get_nearby_strings(self, angle: float, tolerance: float = None) -> List[VirtualString]:
        """
        Get all strings within angle tolerance of current position.
        Useful for future multi-note chord features.
        
        Args:
            angle: Current wrist angle
            tolerance: Angle tolerance range (defaults to configured tolerance)
        
        Returns:
            List of nearby VirtualString objects
        """
        if tolerance is None:
            tolerance = self.angle_tolerance
        
        return [s for s in self.strings if s.is_in_range(angle, tolerance)]
