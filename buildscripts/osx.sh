#!/bin/bash
set -e

if [[ -z "$1" ]]; then
  echo "Please supply a version number for this release as the first argument."
  exit 1
fi

echo "Creating OS X packages for Bitmessage v$1"

export PYBITMESSAGEVERSION=$1

echo "Installing dependencies..."
uv pip install py2app

echo "Building C extension..."
uv run python setup.py build_ext --inplace

echo "Building .app bundle..."
cd src
uv run python build_osx.py py2app

if [[ $? = "0" ]]; then
  echo "Creating DMG..."
  rm -f dist/bitmessage-v$1.dmg
  
  hdiutil create -fs HFS+ -volname "Bitmessage" -srcfolder dist/Bitmessage.app dist/bitmessage-v$1.dmg
  
  echo "-------------------------------------------------------"
  echo "Success! DMG created at: src/dist/bitmessage-v$1.dmg"
  echo "-------------------------------------------------------"
else
  echo "Problem creating Bitmessage.app, stopping."
  exit 1
fi
