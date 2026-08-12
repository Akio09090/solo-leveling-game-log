# THE SYSTEM — Game Log
*"Arise, Player."*

Two versions included:

- **`game_log_gui.py`** — Desktop GUI (Tkinter) with a **login screen, multiple accounts**, separate windows (Status Window, Add Quest, Update, Theme Editor), and full color customization. **Recommended.**
- **`game_log.py`** — Original single-user terminal version, no GUI dependencies.

## How to run the GUI

```bash
python3 game_log_gui.py
```

Tkinter ships with standard Python — no `pip install` needed on most systems (on Linux, if missing: `sudo apt install python3-tk`).

## Accounts (Multi-User)
On launch you'll see a **Log In / Create Account** screen.
- Each person registers their own username + password
- Passwords are never stored in plain text — they're salted and hashed (PBKDF2-HMAC-SHA256, 200,000 iterations)
- Every account gets its own private Quest Log and its own theme, saved under:
  ```
  users_data/<username>/game_data.json
  users_data/<username>/settings.json
  ```
- Switch accounts any time via **Account → Log Out / Switch User** in the menu bar
- Account credentials live in `users.json` (only usernames + salted hashes — never raw passwords)

## GUI Features
- **Separate Windows** — Status Window, Register New Quest, Update Quest, Player Settings, and Theme Editor all open as their own popup windows
- **Tabs** for All / Playing / Completed / Backlog inside the main window
- **Full Customization** via the Theme menu:
  - 4 built-in presets: Shadow Monarch (Blue), Red Gate (Crimson), Guild Gold, Hunter Green
  - Custom Theme Editor — pick your own background, panel, accent, text, and highlight colors with a color picker, plus font size
  - Each user's theme is saved to their own account and reloads on next login
- Add games with **Rank** (E → S → National Level), genre, platform, hours, rating, notes
- Completing a game grants +50 EXP and checks for level-up (with a popup notification)

## EXP System
- Add a game to Backlog: +10 EXP · Playing: +25 EXP
- Mark a game Completed: +50 EXP
- Level up requirement: `level × 50` EXP

## Turning this into a PC Application (.exe / native app)

This uses [PyInstaller](https://pyinstaller.org) to bundle Python + your script into a single standalone app — no Python installation needed for whoever runs it.

**Steps:**
1. Make sure Python 3.9+ is installed on your build machine.
2. Open a terminal in this folder.
3. Run one of the included build scripts:
   - **Any OS** → `python3 build_app.py`
   - **Windows** → double-click `build_windows.bat`
   - **Mac/Linux** → `bash build_mac_linux.sh`

   All three do the same thing: install PyInstaller if needed, then build the app.
4. Your finished app appears in a new `dist` folder:
   - **Windows** → `dist/TheSystem.exe`
   - **Mac/Linux** → `dist/TheSystem`

**Notes:**
- Build **on the same OS** you want to run it on — a Windows `.exe` must be built on Windows, a Mac app on Mac, etc. There's no true cross-compiling.
- The first run may take a few seconds longer to unpack (this is normal for `--onefile` builds).
- `users.json` and the `users_data/` folder are created next to wherever the app runs — keep the app in its own folder so accounts don't scatter.
- To ship it to others: just send them the single `.exe` (or the Mac/Linux binary). They don't need Python installed.
- If you want a custom icon, add `--icon=youricon.ico` (Windows) or `--icon=youricon.icns` (Mac) to the PyInstaller command in `build_app.py`.

## File structure
```
solo_gaming_log/
├── game_log_gui.py     # GUI app (recommended)
├── game_log.py         # terminal version
├── build_app.py        # packages the app into a .exe / native app
├── users.json           # accounts: usernames + salted password hashes (auto-created)
└── users_data/
    └── <username>/
        ├── game_data.json   # that user's Quest Log
        └── settings.json    # that user's theme
```

Everything runs locally — nothing is sent anywhere.

## Turning it into a PC Application (.exe / standalone app)

You can package `game_log_gui.py` into a real desktop app using **PyInstaller** — no Python needed to run it afterward.

### Windows
1. Make sure Python is installed on your PC (python.org).
2. Put `build_windows.bat` in the same folder as `game_log_gui.py`.
3. Double-click `build_windows.bat` (or run it from Command Prompt).
4. Your app appears at `dist\TheSystem.exe` — copy that single file anywhere and double-click to run it.

### macOS / Linux
1. Put `build_mac_linux.sh` in the same folder as `game_log_gui.py`.
2. In Terminal, run:
   ```bash
   chmod +x build_mac_linux.sh
   ./build_mac_linux.sh
   ```
3. Your app appears at `dist/TheSystem` — copy it anywhere and run it directly.

### Notes
- The build must be run on the same OS you want the app for (a Windows `.exe` must be built on Windows, a Mac app on Mac).
- First build can take a minute or two — PyInstaller bundles Python + Tkinter into the file.
- `game_data.json` and `settings.json` will be created next to wherever the built app is run from, so keep the app in its own folder.
- If you want a custom icon, add `--icon=youricon.ico` (Windows) or `.icns` (Mac) to the PyInstaller command in the build script.
- Antivirus/SmartScreen may flag freshly-built PyInstaller `.exe` files as unrecognized (not malicious) — this is common for unsigned apps; you can click "Run anyway."
