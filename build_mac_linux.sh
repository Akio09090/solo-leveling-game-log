#!/bin/bash
# ================================================================
#  THE SYSTEM — Build Script (macOS / Linux)
#  Packages game_log_gui.py into a standalone app
# ================================================================

echo "Installing PyInstaller (if not already installed)..."
pip3 install pyinstaller

echo ""
echo "Building TheSystem ..."
pyinstaller --onefile --windowed --name "TheSystem" game_log_gui.py

echo ""
echo "================================================================"
echo "  DONE! Your app is at: dist/TheSystem"
echo "  You can copy that single file anywhere and run it directly."
echo "================================================================"
