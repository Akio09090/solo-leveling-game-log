@echo off
REM ================================================================
REM  THE SYSTEM — Build Script (Windows)
REM  Packages game_log_gui.py into a standalone .exe
REM ================================================================

echo Installing PyInstaller (if not already installed)...
pip install pyinstaller

echo.
echo Building THE SYSTEM.exe ...
pyinstaller --onefile --windowed --name "TheSystem" game_log_gui.py

echo.
echo ================================================================
echo   DONE! Your app is at:  dist\TheSystem.exe
echo   You can copy that single .exe anywhere and run it directly.
echo ================================================================
pause
