#!/usr/bin/env python3
# src/whisper_hotkey/main.py
"""
Main entry point for the Whisper Hotkey application.
"""
import sys
import traceback
import rumps

from .ui.menu_bar_app import WhisperHotkeyApp
from .constants import APP_NAME

def main():
    """Main entry point for the application."""
    try:
        # Create and run the app
        app = WhisperHotkeyApp()
        app.run()
    except Exception as e:
        # Show an error message
        error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}"
        rumps.alert(
            title=f"{APP_NAME} - Fatal Error",
            message=error_msg
        )
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
