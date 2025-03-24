#!/usr/bin/env python3
"""
Setup script for building the Whisper Hotkey Tool application using py2app.
"""
from setuptools import setup, find_packages

APP = ['src/whisper_hotkey/main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'assets/app_icon.icns',
    'plist': {
        'CFBundleName': 'Whisper Hotkey',
        'CFBundleDisplayName': 'Whisper Hotkey',
        'CFBundleGetInfoString': "Convert speech to text with hotkeys",
        'CFBundleIdentifier': "com.user.whisperhotkey",
        'CFBundleVersion': "0.1.0",
        'CFBundleShortVersionString': "0.1.0",
        'NSMicrophoneUsageDescription': 'Microphone access is required to record audio for speech-to-text conversion.',
        'NSHumanReadableCopyright': 'Copyright © 2024 Your Name. All rights reserved.',
        'NSHighResolutionCapable': True,
        'LSUIElement': True,  # Make it a background application (menu bar only)
    },
    'packages': [
        'rumps',
        'pyobjc',
        'pyaudio',
        'numpy',
        'torch',
        'whisper',
        'soundfile',
    ],
    'excludes': [
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'scipy',
        'pandas',
        'PIL',
    ]
}

setup(
    name='Whisper Hotkey',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='Convert speech to text with hotkeys using OpenAI Whisper',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'rumps>=0.3.0',
        'PyObjC>=8.5',
        'pyobjc-framework-Cocoa>=8.5',
        'pyobjc-framework-Carbon>=8.5',
        'pyobjc-framework-Quartz>=8.5',
        'pyaudio>=0.2.13',
        'numpy>=1.20.0',
        'soundfile>=0.10.3',
        'torch>=1.10.0,<2.0.0',
        'openai-whisper>=20230314',
    ],
    python_requires='>=3.8,<3.10',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: MacOS X',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Utilities',
    ],
)
