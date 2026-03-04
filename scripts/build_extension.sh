#!/bin/bash
# Build VeriSight Extension for Chrome Web Store
# Creates a production-ready zip file

set -e

echo "Building VeriSight Extension..."

# Set variables
EXTENSION_DIR="frontend"
BUILD_DIR="build"
ZIP_NAME="verisight-extension-v$(cat frontend/manifest.json | grep -o '"version": "[^"]*"' | cut -d'"' -f4).zip"

# Clean build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy extension files
echo "Copying extension files..."
cp -r "$EXTENSION_DIR"/* "$BUILD_DIR/"

# Remove development files
echo "Cleaning development files..."
rm -f "$BUILD_DIR"/*.md
rm -f "$BUILD_DIR"/.gitignore

# Create zip file
echo "Creating zip file..."
cd "$BUILD_DIR"
zip -r "../$ZIP_NAME" . -x "*.DS_Store" -x "*__MACOSX*"
cd ..

echo "Extension built successfully: $ZIP_NAME"
echo "Ready for Chrome Web Store upload!"
