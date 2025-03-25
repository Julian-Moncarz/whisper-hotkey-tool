# src/whisper_hotkey/utils/text_inserter.py
"""
Handles inserting text at the current cursor position.
"""
import time
import threading
from typing import Callable, Optional

# Create a platform module to isolate platform-specific code
class MacOSPlatform:
    """Handles macOS-specific operations for text insertion."""
    
    def __init__(self):
        try:
            import Cocoa
            import Quartz
            from ApplicationServices import AXIsProcessTrustedWithOptions
            
            self.cocoa = Cocoa
            self.quartz = Quartz
            self.ax_is_process_trusted = AXIsProcessTrustedWithOptions
            self.is_available = True
        except (ImportError, ModuleNotFoundError):
            self.is_available = False
    
    def check_accessibility_permissions(self) -> bool:
        """Check if the app has accessibility permissions."""
        if not self.is_available:
            print("PyObjC not available, cannot check accessibility permissions")
            return False
            
        try:
            try:
                from ApplicationServices import kAXTrustedCheckOptionPrompt
                return self.ax_is_process_trusted({
                    kAXTrustedCheckOptionPrompt: True
                })
            except (ImportError, NameError):
                # Last resort, use the value directly (1 is the known value for this constant)
                return self.ax_is_process_trusted({
                    1: True
                })
        except Exception as e:
            print(f"Error checking accessibility permissions: {e}")
            return False
    
    def set_clipboard_text(self, text: str) -> bool:
        """Set the clipboard text."""
        if not self.is_available:
            return False
            
        try:
            pasteboard = self.cocoa.NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            return pasteboard.setString_forType_(text, self.cocoa.NSPasteboardTypeString)
        except Exception as e:
            print(f"Error setting clipboard text: {e}")
            return False
    
    def get_clipboard_text(self) -> Optional[str]:
        """Get the clipboard text."""
        if not self.is_available:
            return None
            
        try:
            pasteboard = self.cocoa.NSPasteboard.generalPasteboard()
            return pasteboard.stringForType_(self.cocoa.NSPasteboardTypeString)
        except Exception as e:
            print(f"Error getting clipboard text: {e}")
            return None
    
    def send_keyboard_shortcut(self, key_code: int, with_command: bool = False) -> bool:
        """Send a keyboard shortcut."""
        if not self.is_available:
            return False
            
        try:
            # Create an event source
            source = self.quartz.CGEventSourceCreate(self.quartz.kCGEventSourceStateHIDSystemState)
            
            if with_command:
                # Command key down
                cmd_down = self.quartz.CGEventCreateKeyboardEvent(source, 0x37, True)
                self.quartz.CGEventSetFlags(cmd_down, self.quartz.kCGEventFlagMaskCommand)
                self.quartz.CGEventPost(self.quartz.kCGHIDEventTap, cmd_down)
                time.sleep(0.01)
            
            # Key down
            key_down = self.quartz.CGEventCreateKeyboardEvent(source, key_code, True)
            if with_command:
                self.quartz.CGEventSetFlags(key_down, self.quartz.kCGEventFlagMaskCommand)
            self.quartz.CGEventPost(self.quartz.kCGHIDEventTap, key_down)
            time.sleep(0.01)
            
            # Key up
            key_up = self.quartz.CGEventCreateKeyboardEvent(source, key_code, False)
            if with_command:
                self.quartz.CGEventSetFlags(key_up, self.quartz.kCGEventFlagMaskCommand)
            self.quartz.CGEventPost(self.quartz.kCGHIDEventTap, key_up)
            time.sleep(0.01)
            
            if with_command:
                # Command key up
                cmd_up = self.quartz.CGEventCreateKeyboardEvent(source, 0x37, False)
                self.quartz.CGEventPost(self.quartz.kCGHIDEventTap, cmd_up)
                time.sleep(0.01)
            
            return True
        except Exception as e:
            print(f"Error sending keyboard shortcut: {e}")
            return False


class TextInserter:
    """Inserts text at the current cursor position in any application."""
    
    def __init__(self, platform=None):
        self.on_insertion_complete: Optional[Callable] = None
        self.inserting = False
        self.platform = platform or MacOSPlatform()
    
    def insert_text(self, text: str) -> bool:
        """
        Insert text at the current cursor position.
        
        Args:
            text: Text to insert
            
        Returns:
            bool: True if insertion started, False otherwise
        """
        if not text or self.inserting:
            return False
            
        # Start insertion in a background thread
        self.inserting = True
        threading.Thread(
            target=self._insert_text_thread,
            args=(text,),
            daemon=True
        ).start()
        
        return True
    
    def _insert_text_thread(self, text: str) -> None:
        """
        Thread function for inserting text.
        
        Args:
            text: Text to insert
        """
        old_contents = None
        try:
            # Check if platform is available
            if not self.platform.is_available:
                print("Platform not available")
                return  # Return early without calling the callback
                
            # Check if accessibility is enabled
            if not self.platform.check_accessibility_permissions():
                print("Error: Accessibility permissions not granted")
                return  # Return early without calling the callback
            
            # Save the current clipboard content
            old_contents = self.platform.get_clipboard_text()
            
            # Set the clipboard to our text
            self.platform.set_clipboard_text(text)
            
            # Give the system a moment to process the clipboard change
            time.sleep(0.1)
            
            # Send Command+V to paste
            self.platform.send_keyboard_shortcut(0x09, with_command=True)  # 'v' key
            
            # Wait for paste to complete
            time.sleep(0.2)
            
            # Notify listeners
            if self.on_insertion_complete:
                self.on_insertion_complete()
                
        except Exception as e:
            print(f"Error inserting text: {e}")
        finally:
            # Always restore the original clipboard content
            if old_contents:
                self.platform.set_clipboard_text(old_contents)
            self.inserting = False
