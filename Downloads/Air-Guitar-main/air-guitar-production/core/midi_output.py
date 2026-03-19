"""MIDI output for DAW integration."""
import rtmidi
import logging
from typing import Optional

from utils.logger import setup_logger

logger = setup_logger(__name__)

class MIDIOutput:
    """
    MIDI output interface for sending note data to DAWs and synthesizers.
    Supports velocity and pitch bending for expressive control.
    """
    
    def __init__(self, out_device: Optional[int] = None, channel: int = 0, enabled: bool = True):
        """
        Args:
            out_device: MIDI output device ID (None = system default)
            channel: MIDI channel (0-15)
            enabled: Whether MIDI output is enabled
        """
        self.enabled = enabled
        self.channel = channel
        self.active_notes = {}  # Mapping of note_id -> note_number
        self.midout = None
        
        if self.enabled:
            try:
                self.midout = rtmidi.MidiOut()
                
                # List available outputs
                available_outputs = self.midout.get_ports()
                
                if available_outputs:
                    if out_device is None or out_device >= len(available_outputs):
                        logger.info(f"Available MIDI outputs: {available_outputs}")
                        self.midout.open_port(0)  # Use first available
                        logger.info(f"Opened MIDI output: {available_outputs[0]}")
                    else:
                        self.midout.open_port(out_device)
                        logger.info(f"Opened MIDI output: {available_outputs[out_device]}")
                else:
                    # Create virtual port if no outputs available
                    self.midout.open_virtual_port("Air Guitar OUT")
                    logger.info("Created virtual MIDI output port: Air Guitar OUT")
            
            except Exception as e:
                logger.error(f"Failed to initialize MIDI output: {e}")
                self.enabled = False
    
    def note_on(self, note_number: int, velocity: int = 100, voice_id: int = 0) -> None:
        """
        Send MIDI Note On message.
        
        Args:
            note_number: MIDI note (0-127)
            velocity: Note velocity (0-127)
            voice_id: Internal voice ID for tracking
        """
        if not self.enabled or not self.midout:
            return
        
        # Clamp values
        note_number = max(0, min(127, note_number))
        velocity = max(0, min(127, velocity))
        
        # Status byte: 0x90 (Note On) + channel
        status = 0x90 + self.channel
        
        try:
            self.midout.write_short(status, note_number, velocity)
            self.active_notes[voice_id] = note_number
            logger.debug(f"MIDI Note On: {note_number} velocity={velocity}")
        except Exception as e:
            logger.error(f"MIDI Note On failed: {e}")
    
    def note_off(self, voice_id: int = 0) -> None:
        """
        Send MIDI Note Off message.
        
        Args:
            voice_id: Internal voice ID to turn off
        """
        if not self.enabled or not self.midout:
            return
        
        if voice_id not in self.active_notes:
            return
        
        note_number = self.active_notes[voice_id]
        
        # Status byte: 0x80 (Note Off) + channel
        status = 0x80 + self.channel
        
        try:
            self.midout.write_short(status, note_number, 0)
            del self.active_notes[voice_id]
            logger.debug(f"MIDI Note Off: {note_number}")
        except Exception as e:
            logger.error(f"MIDI Note Off failed: {e}")
    
    def pitch_bend(self, bend_amount: float = 0.0, voice_id: int = 0) -> None:
        """
        Send MIDI Pitch Bend message.
        
        Args:
            bend_amount: -1.0 to +1.0 (full range)
            voice_id: Internal voice ID (for future multi-voice support)
        """
        if not self.enabled or not self.midout:
            return
        
        # Pitch bend is 14-bit value: 0-16383 (center is 8192)
        bend_amount = max(-1.0, min(1.0, bend_amount))
        bend_value = int(8192 + bend_amount * 8191)
        
        # Split into 14-bit LSB and MSB
        lsb = bend_value & 0x7F
        msb = (bend_value >> 7) & 0x7F
        
        # Status byte: 0xE0 (Pitch Bend) + channel
        status = 0xE0 + self.channel
        
        try:
            self.midout.write_short(status, lsb, msb)
            logger.debug(f"MIDI Pitch Bend: {bend_amount:.2f}")
        except Exception as e:
            logger.error(f"MIDI Pitch Bend failed: {e}")
    
    def controller_change(self, controller: int, value: int) -> None:
        """
        Send MIDI Control Change message.
        
        Args:
            controller: CC number (0-127)
            value: CC value (0-127)
        """
        if not self.enabled or not self.midout:
            return
        
        controller = max(0, min(127, controller))
        value = max(0, min(127, value))
        
        # Status byte: 0xB0 (Control Change) + channel
        status = 0xB0 + self.channel
        
        try:
            self.midout.write_short(status, controller, value)
            logger.debug(f"MIDI CC: {controller} = {value}")
        except Exception as e:
            logger.error(f"MIDI CC failed: {e}")
    
    def all_notes_off(self) -> None:
        """Send All Notes Off message."""
        if not self.enabled or not self.midout:
            return
        
        try:
            # CC 123 = All Notes Off
            self.controller_change(123, 0)
            self.active_notes.clear()
        except Exception as e:
            logger.error(f"All Notes Off failed: {e}")
    
    def close(self) -> None:
        """Close MIDI port."""
        if self.midout:
            self.midout.close()
            logger.info("MIDI output closed")
    
    def frequency_to_midi_note(self, freq: float) -> int:
        """
        Convert frequency to MIDI note number.
        MIDI Note = 69 + 12 * log2(f / 440)
        
        Args:
            freq: Frequency in Hz
        
        Returns:
            MIDI note number (0-127)
        """
        import math
        midi_note = 69 + 12 * math.log2(freq / 440.0)
        return max(0, min(127, int(round(midi_note))))
    
    def midi_note_to_frequency(self, note: int) -> float:
        """
        Convert MIDI note number to frequency.
        f = 440 * 2^((n-69)/12)
        
        Args:
            note: MIDI note number (0-127)
        
        Returns:
            Frequency in Hz
        """
        return 440.0 * (2.0 ** ((note - 69) / 12.0))
