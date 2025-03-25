# src/whisper_hotkey/ui/menu_bar_app.py
"""
Menu bar interface for the Whisper Hotkey Tool.
"""
import os
import sys
import threading
import webbrowser
from typing import Dict, Optional, Tuple

import rumps

from ..app_core import AppCore
from ..constants import APP_NAME, APP_VERSION, DEFAULT_START_RECORDING_HOTKEY, DEFAULT_STOP_RECORDING_HOTKEY

class WhisperHotkeyApp(rumps.App):
    """Menu bar application for Whisper Hotkey Tool."""
    
    def __init__(self):
        # Initialize the menu bar app
        super().__init__(
            name=APP_NAME,
            title="🎤",
            quit_button="Quit"
        )
        
        # Create the app core
        self.app_core = AppCore()
        
        # Set up menu items
        self.status_item = rumps.MenuItem("Status: Initializing...")
        self.recording_item = rumps.MenuItem("Start Recording", callback=self.toggle_recording)
        self.recording_hotkey_item = rumps.MenuItem(f"Start Recording Hotkey: {DEFAULT_START_RECORDING_HOTKEY}")
        self.stop_hotkey_item = rumps.MenuItem(f"Stop Recording Hotkey: {DEFAULT_STOP_RECORDING_HOTKEY}")
        
        # Model selection submenu
        self.model_menu = rumps.MenuItem("Whisper Model")
        self.model_items: Dict[str, rumps.MenuItem] = {}
        
        # Change hotkeys menu item
        self.change_hotkeys_item = rumps.MenuItem("Change Hotkeys...", callback=self.show_hotkey_window)
        
        # About and Permissions items
        self.about_item = rumps.MenuItem("About", callback=self.show_about)
        self.permissions_item = rumps.MenuItem("Accessibility Permissions...", callback=self.open_accessibility)
        
        # Add items to the menu
        self.menu = [
            self.status_item,
            None,  # Separator
            self.recording_item,
            None,  # Separator
            self.recording_hotkey_item,
            self.stop_hotkey_item,
            None,  # Separator
            self.model_menu,
            None,  # Separator
            self.change_hotkeys_item,
            None,  # Separator
            self.about_item,
            self.permissions_item
        ]
        
        # Set up callbacks
        self.app_core.on_recording_started = self._on_recording_started
        self.app_core.on_recording_stopped = self._on_recording_stopped
        self.app_core.on_transcription_started = self._on_transcription_started
        self.app_core.on_transcription_complete = self._on_transcription_complete
        self.app_core.on_error = self._on_error
        
        # Initialize app in background thread
        threading.Thread(target=self._initialize_app, daemon=True).start()
    
    def _initialize_app(self) -> None:
        """Initialize the application in a background thread."""
        try:
            # Initialize the app core
            self.app_core.initialize()
            
            # Update the status
            self.status_item.title = "Status: Ready"
            
            # Create model selection menu items
            available_models = self.app_core.get_available_models()
            current_model = self.app_core.config_manager.get("whisper_model", "base")
            
            for model_name, model_size in available_models.items():
                item = rumps.MenuItem(
                    f"{model_name.capitalize()} ({model_size})",
                    callback=self.select_model
                )
                item.state = model_name == current_model
                self.model_items[model_name] = item
                self.model_menu.add(item)
            
            # Update hotkey display
            config_manager = self.app_core.config_manager
            start_hotkey = config_manager.get("start_recording_hotkey", DEFAULT_START_RECORDING_HOTKEY)
            stop_hotkey = config_manager.get("stop_recording_hotkey", DEFAULT_STOP_RECORDING_HOTKEY)
            
            self.recording_hotkey_item.title = f"Start Recording Hotkey: {start_hotkey}"
            self.stop_hotkey_item.title = f"Stop Recording Hotkey: {stop_hotkey}"
            
            # Check for first run
            if self.app_core.is_first_run:
                self._show_first_run_message()
            
        except Exception as e:
            self.status_item.title = "Status: Initialization Error"
            rumps.notification(
                title=APP_NAME,
                subtitle="Initialization Error",
                message=str(e)
            )
    
    @rumps.clicked("Start Recording")
    def toggle_recording(self, sender) -> None:
        """Toggle recording state."""
        if self.app_core.is_currently_recording():
            self.app_core.stop_recording()
        else:
            self.app_core.start_recording()
    
    @rumps.clicked("Whisper Model")
    def select_model(self, sender) -> None:
        """Select a Whisper model."""
        # Find which model was selected based on the menu item title
        selected_model = None
        for model_name, size in self.app_core.get_available_models().items():
            expected_title = f"{model_name.capitalize()} ({size})"
            if sender.title == expected_title:
                selected_model = model_name
                break
        
        # If we found a matching model, update it
        if selected_model:
            # Update the status to show we're loading
            self.status_item.title = f"Status: Loading {selected_model} model..."
            
            # Change the model
            self.app_core.change_whisper_model(selected_model)
            
            # Update the menu checkmarks - first clear all
            for item in self.model_items.values():
                item.state = False
            
            # Then set the current one
            if selected_model in self.model_items:
                self.model_items[selected_model].state = True
    
    @rumps.clicked("Change Hotkeys...")
    def show_hotkey_window(self, sender) -> None:
        """Show window for changing hotkeys."""
        # Create a window for changing hotkeys
        window = rumps.Window(
            title="Change Hotkeys",
            message="Enter new hotkeys for starting and stopping recording.\n\n"
                    "Format: Command-Shift-R (use Command, Control, Option, Shift as modifiers)",
            dimensions=(400, 100)
        )
        
        # Set default values
        config_manager = self.app_core.config_manager
        start_hotkey = config_manager.get("start_recording_hotkey", DEFAULT_START_RECORDING_HOTKEY)
        stop_hotkey = config_manager.get("stop_recording_hotkey", DEFAULT_STOP_RECORDING_HOTKEY)
        
        window.default_text = f"{start_hotkey},{stop_hotkey}"
        
        # Show the window
        response = window.run()
        
        if response.clicked:
            try:
                # Parse the input
                hotkeys = response.text.split(",")
                if len(hotkeys) != 2:
                    raise ValueError("Please enter two hotkeys separated by a comma.")
                    
                start_hotkey = hotkeys[0].strip()
                stop_hotkey = hotkeys[1].strip()
                
                # Set the new hotkeys
                if self.app_core.set_hotkeys(start_hotkey, stop_hotkey):
                    # Update the menu items
                    self.recording_hotkey_item.title = f"Start Recording Hotkey: {start_hotkey}"
                    self.stop_hotkey_item.title = f"Stop Recording Hotkey: {stop_hotkey}"
                    
                    rumps.notification(
                        title=APP_NAME,
                        subtitle="Hotkeys Changed",
                        message=f"Start: {start_hotkey}, Stop: {stop_hotkey}"
                    )
                else:
                    rumps.notification(
                        title=APP_NAME,
                        subtitle="Error",
                        message="Failed to set hotkeys. Please use the correct format."
                    )
            except Exception as e:
                rumps.notification(
                    title=APP_NAME,
                    subtitle="Error",
                    message=f"Failed to set hotkeys: {e}"
                )
    
    @rumps.clicked("About")
    def show_about(self, sender) -> None:
        """Show about information."""
        rumps.alert(
            title=f"About {APP_NAME}",
            message=f"{APP_NAME} v{APP_VERSION}\n\n"
                    f"A tool to convert speech to text using OpenAI's Whisper model.\n\n"
                    f"© 2024 Your Name"
        )
    
    @rumps.clicked("Accessibility Permissions...")
    def open_accessibility(self, sender) -> None:
        """Open the Accessibility permissions panel in System Preferences."""
        # Open the Security & Privacy panel
        os.system("open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'")
    
    def _on_recording_started(self) -> None:
        """Called when recording starts."""
        # Update UI
        self.title = "🔴"
        self.recording_item.title = "Stop Recording"
        self.status_item.title = "Status: Recording..."
    
    def _on_recording_stopped(self) -> None:
        """Called when recording stops."""
        self.recording_item.title = "Start Recording"
    
    def _on_transcription_started(self) -> None:
        """Called when transcription starts."""
        # Update UI
        self.title = "⏱️"
        self.status_item.title = "Status: Transcribing..."
    
    def _on_transcription_complete(self, text: str) -> None:
        """
        Called when transcription is complete.
        
        Args:
            text: The transcribed text
        """
        # Update UI
        self.title = "🎤"
        self.status_item.title = "Status: Ready"
        
        # Show a notification
        rumps.notification(
            title=APP_NAME,
            subtitle="Transcription Complete",
            message=f"Text inserted at cursor: \"{text[:50]}{'...' if len(text) > 50 else ''}\""
        )
    
    def _on_error(self, message: str) -> None:
        """
        Called when an error occurs.
        
        Args:
            message: The error message
        """
        # Update UI
        self.title = "🎤"
        self.status_item.title = "Status: Error"
        
        # Show a notification
        rumps.notification(
            title=APP_NAME,
            subtitle="Error",
            message=message
        )
    
    def _show_first_run_message(self) -> None:
        """Show first run message and request permissions."""
        rumps.alert(
            title=f"Welcome to {APP_NAME}!",
            message="This tool allows you to convert speech to text using hotkeys.\n\n"
                    "To use this app, you'll need to grant accessibility permissions.\n\n"
                    "Click OK to open the Security & Privacy panel, then add this app to the list of "
                    "apps allowed to control your computer."
        )
        
        # Open the accessibility permissions panel
        self.open_accessibility(None)

def run() -> None:
    """Run the menu bar application."""
    app = WhisperHotkeyApp()
    app.run()

if __name__ == "__main__":
    run()
