# src/whisper_hotkey/utils/hotkey_manager.py
"""
Manages system-wide hotkeys for the application.
"""
import threading
from typing import Callable, Dict, Optional, Tuple

import objc
from Foundation import NSObject
import AppKit
from AppKit import NSEvent, NSKeyDownMask, NSSystemDefined, NSApplicationDefined, NSApplication

class HotkeyManager:
    """Manages global hotkeys for the application."""
    
    # Key code mappings
    KEY_CODES = {
        'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4, 'i': 34,
        'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31, 'p': 35, 'q': 12,
        'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9, 'w': 13, 'x': 7, 'y': 16, 'z': 6,
        '0': 29, '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22, '7': 26,
        '8': 28, '9': 25, '-': 27, '=': 24, '[': 33, ']': 30, ';': 41, "'": 39,
        ',': 43, '.': 47, '/': 44, '\\': 42, '`': 50
    }
    
    # Modifier key mappings (as used by NSEvent)
    MODIFIERS = {
        'Command': 1 << 20,    # NSEventModifierFlagCommand
        'Shift': 1 << 17,      # NSEventModifierFlagShift
        'Option': 1 << 19,     # NSEventModifierFlagOption
        'Control': 1 << 18     # NSEventModifierFlagControl
    }
    
    def __init__(self):
        self.hotkeys: Dict[str, Tuple[Tuple[int, int], Callable]] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.monitor = None
    
    def register_hotkey(self, hotkey_str: str, callback: Callable) -> bool:
        """
        Register a global hotkey.
        
        Args:
            hotkey_str: String representation of the hotkey (e.g., "Command-Shift-R")
            callback: Function to call when the hotkey is pressed
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        try:
            key_code, modifiers = self._parse_hotkey_string(hotkey_str)
            
            # Store the hotkey information for later use
            self.hotkeys[hotkey_str] = ((key_code, modifiers), callback)
            
            return True
            
        except Exception as e:
            print(f"Failed to register hotkey '{hotkey_str}': {e}")
            return False
    
    def unregister_hotkey(self, hotkey_str: str) -> bool:
        """
        Unregister a previously registered hotkey.
        
        Args:
            hotkey_str: String representation of the hotkey
            
        Returns:
            bool: True if unregistration was successful, False otherwise
        """
        try:
            if hotkey_str in self.hotkeys:
                del self.hotkeys[hotkey_str]
                return True
            return False
        except Exception as e:
            print(f"Failed to unregister hotkey '{hotkey_str}': {e}")
            return False
    
    def start(self) -> None:
        """Start the hotkey monitoring thread."""
        if self.running:
            return
            
        self.running = True
        
        # Start the event handling thread
        self.thread = threading.Thread(target=self._event_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the hotkey monitoring thread."""
        if not self.running:
            return
            
        self.running = False
        
        # Stop monitoring if active
        if self.monitor:
            NSEvent.removeMonitor_(self.monitor)
            self.monitor = None
        
        # Signal the event loop to stop
        if self.thread:
            # Post an application-defined event to wake up the run loop
            app = NSApplication.sharedApplication()
            if app:
                event = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                    NSApplicationDefined,
                    (0, 0),
                    0,
                    0,
                    0,
                    None,
                    0,
                    0,
                    0
                )
                app.postEvent_atStart_(event, True)
            
            # Wait for the thread to terminate
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _parse_hotkey_string(self, hotkey_str: str) -> Tuple[int, int]:
        """
        Parse a hotkey string into key code and modifiers.
        
        Args:
            hotkey_str: String representation of the hotkey (e.g., "Command-Shift-R")
            
        Returns:
            Tuple[int, int]: Key code and modifiers
        """
        parts = hotkey_str.split('-')
        if len(parts) < 2:
            raise ValueError(f"Invalid hotkey format: {hotkey_str}")
            
        # The last part is the key
        key = parts[-1].lower()
        if len(key) != 1 or key not in self.KEY_CODES:
            raise ValueError(f"Unsupported key: {key}")
            
        key_code = self.KEY_CODES[key]
        
        # Parse modifiers
        modifiers = 0
        for modifier in parts[:-1]:
            if modifier not in self.MODIFIERS:
                raise ValueError(f"Unknown modifier: {modifier}")
            modifiers |= self.MODIFIERS[modifier]
            
        return key_code, modifiers
    
    def _event_loop(self) -> None:
        """Event loop for handling hotkey events."""
        try:
            # Set up event monitoring for key down events
            self.monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                NSKeyDownMask,
                self._handle_event
            )
            
            # Keep the thread alive until stop() is called
            while self.running:
                # Process events using the main run loop
                NSApp = NSApplication.sharedApplication()
                NSApp.run()
                
        except Exception as e:
            print(f"Error in event loop: {e}")
        finally:
            # Clean up the monitor if it exists
            if self.monitor and self.running:
                NSEvent.removeMonitor_(self.monitor)
                self.monitor = None
    
    def _handle_event(self, event) -> None:
        """
        Handle key events and trigger callbacks if they match registered hotkeys.
        
        Args:
            event: The NSEvent to process
        """
        try:
            # Get key code and modifiers from the event
            key_code = event.keyCode()
            modifiers = event.modifierFlags() & 0xFFFF0000  # Mask to get just the modifier flags
            
            # Check if this matches any registered hotkeys
            for hotkey_str, ((registered_key_code, registered_modifiers), callback) in self.hotkeys.items():
                if key_code == registered_key_code and modifiers == registered_modifiers:
                    # Run the callback in a separate thread to avoid blocking
                    threading.Thread(target=callback, daemon=True).start()
                    break
        except Exception as e:
            print(f"Error handling event: {e}")
