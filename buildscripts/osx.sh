#!/bin/bash
set -e

if [[ -z "$1" ]]; then
    # Auto-detect version from src/version.py
    VERSION=$(grep "softwareVersion =" src/version.py | cut -d "'" -f 2)
    if [[ -z "$VERSION" ]]; then
        echo "Could not detect version from src/version.py and no argument provided."
        exit 1
    fi
    echo "No version argument provided. Using detected version: $VERSION"
else
    VERSION=$1
fi

echo "Creating MacOS packages for Bitmessage v$VERSION"

export PYBITMESSAGEVERSION=$VERSION

echo "Installing dependencies..."
uv pip install py2app

echo "Building C extension..."
uv run python setup.py build_ext --inplace

echo "Building .app bundle..."
cd src
uv run python build_osx.py py2app

if [[ $? = "0" ]]; then
  echo "Creating DMG..."
  rm -f dist/bitmessage-v$VERSION.dmg
  
  hdiutil create -fs HFS+ -volname "Bitmessage" -srcfolder dist/Bitmessage.app dist/bitmessage-v$VERSION.dmg
  
  echo "-------------------------------------------------------"
  echo "Success! DMG created at: src/dist/bitmessage-v$VERSION.dmg"
  echo "-------------------------------------------------------"
else
  echo "Problem creating Bitmessage.app, stopping."
  exit 1
fi
