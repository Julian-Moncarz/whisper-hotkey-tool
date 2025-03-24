#!/bin/bash
# build_dmg.sh - Script to build a .dmg file for the Whisper Hotkey Tool

set -e  # Exit on error

# Configuration
APP_NAME="Whisper Hotkey"
VERSION=$(grep "'CFBundleVersion':" setup.py | awk -F'"' '{print $2}')
DMG_NAME="${APP_NAME// /_}-${VERSION}.dmg"
BUILD_DIR="build"
DIST_DIR="dist"
DMG_DIR="${BUILD_DIR}/dmg"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
BACKGROUND_IMG="assets/dmg_background.png"
DS_STORE="assets/DS_Store"
VOL_NAME="${APP_NAME} ${VERSION}"

# Step 1: Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf "${BUILD_DIR}" "${DIST_DIR}" "${DMG_NAME}" 
# Remove egg-info directories if they exist (suppressing errors if they don't)
find . -name "*.egg-info" -type d -exec rm -rf {} +  2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} +  2>/dev/null || true

# Step 2: Build the app using py2app
echo "Building the application using py2app..."
# Try rebuilding the egg-info directory first
python setup.py egg_info
# Then build the app
python setup.py py2app --no-strip

# Make sure the app was built
if [ ! -d "${APP_PATH}" ]; then
    echo "Error: Application build failed."
    exit 1
fi

# Step 3: Create DMG structure
echo "Creating DMG structure..."
mkdir -p "${DMG_DIR}"

# Copy the app to the DMG directory
cp -R "${APP_PATH}" "${DMG_DIR}/"

# Create a link to the Applications folder
ln -s /Applications "${DMG_DIR}/Applications"

# Step 4: Create the DMG
echo "Creating DMG file..."
if [ -f "${BACKGROUND_IMG}" ] && [ -f "${DS_STORE}" ]; then
    # Create DMG with custom background and layout
    echo "Using custom background and layout..."
    mkdir -p "${DMG_DIR}/.background"
    cp "${BACKGROUND_IMG}" "${DMG_DIR}/.background/background.png"
    cp "${DS_STORE}" "${DMG_DIR}/.DS_Store"
    
    hdiutil create -volname "${VOL_NAME}" -srcfolder "${DMG_DIR}" -ov -format UDZO "${DMG_NAME}"
else
    # Create a basic DMG
    echo "Creating basic DMG (no custom background or layout)..."
    hdiutil create -volname "${VOL_NAME}" -srcfolder "${DMG_DIR}" -ov -format UDZO "${DMG_NAME}"
fi

# Step 5: Clean up
echo "Cleaning up build files..."
rm -rf "${DMG_DIR}"

# Step 6: Verify the DMG
echo "Verifying DMG file..."
if [ -f "${DMG_NAME}" ]; then
    echo "DMG file created successfully: ${DMG_NAME}"
    echo "Size: $(du -h "${DMG_NAME}" | cut -f1)"
else
    echo "Error: DMG file creation failed."
    exit 1
fi

echo "Build complete!"
