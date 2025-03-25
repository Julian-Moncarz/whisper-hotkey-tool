# Whisper Hotkey Tool

A macOS application that converts speech to text using OpenAI's Whisper model. Press a hotkey, speak, and the transcribed text will appear at your cursor position.

## Features

- **Global Hotkeys**: Start and stop recording from anywhere with customizable keyboard shortcuts
- **Local Processing**: Uses OpenAI's Whisper models running locally on your machine for privacy
- **Multiple Models**: Choose between different Whisper models (tiny, base, small, medium, large) based on your accuracy needs and hardware capabilities
- **Clipboard Integration**: Automatically inserts transcribed text at the current cursor position
- **Menu Bar Interface**: Simple, unobtrusive menu bar application
- **Memory-Only Processing**: Audio recordings are kept in memory only and never saved to disk for enhanced privacy

## Installation

### Prerequisites

- Python 3.8 or 3.9
- Homebrew (for installing dependencies)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Julian-Moncarz/whisper-hotkey-tool.git
   cd whisper-hotkey-tool
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application
   ```bash
   python -m src.whisper_hotkey.main
   ```

4. On first run, you'll be prompted to grant necessary permissions:
   - **Accessibility permissions**: Required to insert text at the cursor position
   - **Microphone access**: Required to record audio for transcription

## Usage

1. Place your cursor where you want the transcribed text to appear
2. Press the start recording hotkey (default: `Control-R`)
3. Speak clearly into your microphone
4. Press the stop recording hotkey (default: `Control-S`)
5. The transcribed text will appear at your cursor position

## Configuration

Click on the menu bar icon (🎤) to access the following options:

- **Start/Stop Recording**: Manually control recording
- **Whisper Model**: Select which model to use for transcription
  - **Tiny** (39MB): Fast but less accurate
  - **Base** (142MB): Good balance of speed and accuracy for most uses
  - **Small** (466MB): More accurate than base, but slower
  - **Medium** (1.5GB): Very accurate, but requires more resources
  - **Large** (3GB): Most accurate, but slowest and most resource-intensive
- **Settings**:
  - **Change Hotkeys**: Customize the keyboard shortcuts

## System Requirements

- macOS 10.15 (Catalina) or later
- 4GB RAM minimum (8GB+ recommended for medium/large models)
- 500MB free disk space plus space for the Whisper model

## Testing

Run the test suite:
```bash
python -m pytest tests
```

The test suite includes comprehensive tests for:
- Audio recording and transcription
- Configuration management
- Hotkey handling
- Menu bar interface
- Text insertion

## License

MIT License - See the LICENSE file for details.

## Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) for the speech recognition model
- [rumps](https://github.com/jaredks/rumps) for the menu bar interface
