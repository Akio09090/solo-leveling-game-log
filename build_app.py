"""
Build helper — turns game_log_gui.py into a standalone .exe (Windows)
or a native app (Mac/Linux) using PyInstaller.

USAGE:
    1) pip install pyinstaller
    2) python3 build_app.py

The finished app will appear in a new "dist" folder.
"""

import subprocess
import sys

def main():
    try:
        import PyInstaller  # noqa
    except ImportError:
        print("PyInstaller not found. Installing it now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",              # no console window pops up
        "--name", "TheSystem",
        "game_log_gui.py",
    ]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
    print("\nDone! Find your app inside the 'dist' folder.")
    print("On Windows: dist/TheSystem.exe")
    print("On Mac/Linux: dist/TheSystem")

if __name__ == "__main__":
    main()
