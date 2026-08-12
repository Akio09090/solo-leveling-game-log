#!/usr/bin/env python3
"""
================================================================
   THE SYSTEM — GAME LOG (GUI Edition)
   "Arise, Player. Your Quest Log awaits."
================================================================
A Solo Leveling styled desktop app (Tkinter) for tracking games
you're Playing, have Completed, or plan to Play (Backlog).

Now supports multiple accounts — each user logs in / registers and gets
their own private game log + theme, stored under users_data/<username>/.

Run:  python3 game_log_gui.py
================================================================
"""

import json
import os
import hashlib
import hmac
import secrets
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
USERS_DATA_DIR = os.path.join(BASE_DIR, "users_data")

STATUS_PLAYING = "Playing"
STATUS_COMPLETED = "Completed"
STATUS_BACKLOG = "Backlog"
STATUSES = [STATUS_PLAYING, STATUS_COMPLETED, STATUS_BACKLOG]
RANKS = ["E", "D", "C", "B", "A", "S", "National Level"]

DEFAULT_THEME = {
    "bg": "#0a0e1a",
    "panel_bg": "#0f1526",
    "accent": "#4da6ff",
    "text": "#d6e4ff",
    "subtext": "#7f93b8",
    "border": "#2a3a5c",
    "success": "#33e08a",
    "font_family": "Consolas",
    "font_size": 11,
}

THEME_PRESETS = {
    "Shadow Monarch (Blue)": {"bg": "#0a0e1a", "panel_bg": "#0f1526", "accent": "#4da6ff",
                               "text": "#d6e4ff", "subtext": "#7f93b8", "border": "#2a3a5c", "success": "#33e08a"},
    "Red Gate (Crimson)": {"bg": "#170a0a", "panel_bg": "#1f0f0f", "accent": "#ff4d4d",
                            "text": "#ffdede", "subtext": "#b87f7f", "border": "#5c2a2a", "success": "#ffb84d"},
    "Guild Gold": {"bg": "#141005", "panel_bg": "#1c1608", "accent": "#f2c14e",
                   "text": "#fff3d6", "subtext": "#b8a97f", "border": "#5c4d2a", "success": "#8be07a"},
    "Hunter Green": {"bg": "#08130f", "panel_bg": "#0d1c16", "accent": "#3ee08a",
                     "text": "#d6ffe9", "subtext": "#7fb897", "border": "#2a5c42", "success": "#7ad1ff"},
}


# ---------------------------------------------------------------
#  DATA LAYER
# ---------------------------------------------------------------

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def user_dir(username):
    d = os.path.join(USERS_DATA_DIR, username)
    os.makedirs(d, exist_ok=True)
    return d


def load_data(username):
    path = os.path.join(user_dir(username), "game_data.json")
    return load_json(path, {"games": [], "next_id": 1, "player": {"name": username, "level": 1, "exp": 0}})


def save_data_for(username, data):
    path = os.path.join(user_dir(username), "game_data.json")
    save_json(path, data)


def load_settings(username):
    path = os.path.join(user_dir(username), "settings.json")
    s = load_json(path, {})
    theme = dict(DEFAULT_THEME)
    theme.update(s.get("theme", {}))
    return theme


def save_settings_for(username, theme):
    path = os.path.join(user_dir(username), "settings.json")
    save_json(path, {"theme": theme})


# ---------------------------------------------------------------
#  ACCOUNTS (LOGIN / REGISTER)
# ---------------------------------------------------------------

def load_users():
    return load_json(USERS_FILE, {})


def save_users(users):
    save_json(USERS_FILE, users)


def hash_password(password, salt=None):
    """PBKDF2-HMAC-SHA256 password hashing with a random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000)
    return salt, digest.hex()


def verify_password(password, salt, expected_hash):
    _, computed = hash_password(password, salt)
    return hmac.compare_digest(computed, expected_hash)


def register_user(username, password):
    users = load_users()
    username = username.strip()
    if not username:
        return False, "Enter a username."
    if username in users:
        return False, "That username is already taken."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    salt, pw_hash = hash_password(password)
    users[username] = {"salt": salt, "hash": pw_hash, "created": datetime.now().strftime("%Y-%m-%d")}
    save_users(users)
    user_dir(username)  # create their data folder
    return True, "Account created."


def authenticate_user(username, password):
    users = load_users()
    entry = users.get(username.strip())
    if not entry:
        return False, "No account with that username."
    if not verify_password(password, entry["salt"], entry["hash"]):
        return False, "Incorrect password."
    return True, "OK"


# ---------------------------------------------------------------
#  APP
# ---------------------------------------------------------------

class SystemApp:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.data = load_data(username)
        self.theme = load_settings(username)

        self.root.title(f"THE SYSTEM — Game Log  [{username}]")
        self.root.geometry("980x620")
        self.root.minsize(760, 480)

        self.apply_root_theme()
        self.build_menu_bar()
        self.build_main_window()
        self.refresh_table()

    # ---------- THEME ----------
    def apply_root_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg"])
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        font_main = (t["font_family"], t["font_size"])
        font_bold = (t["font_family"], t["font_size"], "bold")

        self.style.configure("TFrame", background=t["panel_bg"])
        self.style.configure("Root.TFrame", background=t["bg"])
        self.style.configure("TLabel", background=t["panel_bg"], foreground=t["text"], font=font_main)
        self.style.configure("Header.TLabel", background=t["bg"], foreground=t["accent"],
                              font=(t["font_family"], t["font_size"] + 6, "bold"))
        self.style.configure("Sub.TLabel", background=t["panel_bg"], foreground=t["subtext"], font=font_main)
        self.style.configure("Stat.TLabel", background=t["panel_bg"], foreground=t["success"], font=font_bold)

        self.style.configure("TButton", background=t["accent"], foreground=t["bg"],
                              font=font_bold, borderwidth=0, focuscolor=t["accent"], padding=6)
        self.style.map("TButton", background=[("active", t["text"])])

        self.style.configure("Treeview", background=t["panel_bg"], fieldbackground=t["panel_bg"],
                              foreground=t["text"], font=font_main, rowheight=26, borderwidth=0)
        self.style.configure("Treeview.Heading", background=t["border"], foreground=t["accent"],
                              font=font_bold, relief="flat")
        self.style.map("Treeview", background=[("selected", t["accent"])],
                        foreground=[("selected", t["bg"])])

        self.style.configure("TNotebook", background=t["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=t["panel_bg"], foreground=t["subtext"],
                              font=font_bold, padding=(14, 8))
        self.style.map("TNotebook.Tab",
                        background=[("selected", t["accent"])],
                        foreground=[("selected", t["bg"])])

        self.style.configure("TEntry", fieldbackground=t["panel_bg"], foreground=t["text"],
                              insertcolor=t["text"])
        self.style.configure("TCombobox", fieldbackground=t["panel_bg"], foreground=t["text"])

    def refresh_theme_everywhere(self):
        self.apply_root_theme()
        self.root.destroy_children = None
        for widget in self.root.winfo_children():
            widget.destroy()
        self.build_menu_bar()
        self.build_main_window()
        self.refresh_table()

    # ---------- MENU BAR ----------
    def build_menu_bar(self):
        menubar = tk.Menu(self.root)
        theme_menu = tk.Menu(menubar, tearoff=0)
        for name in THEME_PRESETS:
            theme_menu.add_command(label=name, command=lambda n=name: self.apply_preset(n))
        theme_menu.add_separator()
        theme_menu.add_command(label="Custom Theme Editor...", command=self.open_theme_editor)
        menubar.add_cascade(label="Theme", menu=theme_menu)

        window_menu = tk.Menu(menubar, tearoff=0)
        window_menu.add_command(label="Status Window", command=self.open_status_window)
        window_menu.add_command(label="Add Game Window", command=self.open_add_window)
        window_menu.add_command(label="Player Settings Window", command=self.open_player_window)
        menubar.add_cascade(label="Windows", menu=window_menu)

        account_menu = tk.Menu(menubar, tearoff=0)
        account_menu.add_command(label=f"Logged in as: {self.username}", state="disabled")
        account_menu.add_separator()
        account_menu.add_command(label="Log Out / Switch User", command=self.log_out)
        menubar.add_cascade(label="Account", menu=account_menu)

        self.root.config(menu=menubar)

    def log_out(self):
        if messagebox.askyesno("Log Out", "Log out and return to the login screen?"):
            for widget in self.root.winfo_children():
                widget.destroy()
            self.root.config(menu=tk.Menu(self.root))
            LoginScreen(self.root)

    def apply_preset(self, name):
        preset = THEME_PRESETS[name]
        self.theme.update(preset)
        save_settings_for(self.username, self.theme)
        self.refresh_theme_everywhere()

    # ---------- MAIN WINDOW LAYOUT ----------
    def build_main_window(self):
        t = self.theme
        header = ttk.Frame(self.root, style="Root.TFrame")
        header.pack(fill="x", padx=16, pady=(14, 6))
        ttk.Label(header, text="THE SYSTEM — GAME LOG", style="Header.TLabel").pack(side="left")

        self.player_label = ttk.Label(header, text=self.player_summary_text(),
                                       style="Header.TLabel")
        self.player_label.configure(font=(t["font_family"], t["font_size"] + 1, "bold"))
        self.player_label.pack(side="right")

        btn_bar = ttk.Frame(self.root, style="Root.TFrame")
        btn_bar.pack(fill="x", padx=16, pady=(0, 8))
        ttk.Button(btn_bar, text="+ Register New Quest", command=self.open_add_window).pack(side="left", padx=(0, 6))
        ttk.Button(btn_bar, text="Status Window", command=self.open_status_window).pack(side="left", padx=6)
        ttk.Button(btn_bar, text="Update Selected", command=self.open_update_window).pack(side="left", padx=6)
        ttk.Button(btn_bar, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=6)
        ttk.Button(btn_bar, text="Customize Theme", command=self.open_theme_editor).pack(side="right")

        # Tabs = separate filtered windows within main frame
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.trees = {}
        for status in ["All"] + STATUSES:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=status)
            tree = self.build_tree(frame)
            self.trees[status] = tree

    def build_tree(self, parent):
        cols = ("id", "title", "rank", "genre", "platform", "hours", "rating", "added")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        headings = {"id": "ID", "title": "Title", "rank": "Rank", "genre": "Genre",
                    "platform": "Platform", "hours": "Hours", "rating": "Rating", "added": "Added"}
        widths = {"id": 40, "title": 240, "rank": 60, "genre": 120,
                  "platform": 100, "hours": 60, "rating": 60, "added": 90}
        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="w")
        tree.pack(fill="both", expand=True, padx=4, pady=4)
        return tree

    def player_summary_text(self):
        p = self.data["player"]
        needed = p["level"] * 50
        return f"{p['name']}   Lv.{p['level']}   EXP {p['exp']}/{needed}"

    # ---------- TABLE REFRESH ----------
    def refresh_table(self):
        for status, tree in self.trees.items():
            for row in tree.get_children():
                tree.delete(row)
            games = self.data["games"] if status == "All" else [g for g in self.data["games"] if g["status"] == status]
            for g in games:
                tree.insert("", "end", iid=str(g["id"]), values=(
                    g["id"], g["title"], g["rank"], g.get("genre", ""), g.get("platform", ""),
                    g.get("hours", 0), g.get("rating", "") or "-", g.get("date_added", "")
                ))
        self.player_label.configure(text=self.player_summary_text())

    def current_selected_id(self):
        tab = self.notebook.tab(self.notebook.select(), "text")
        tree = self.trees[tab]
        sel = tree.selection()
        if not sel:
            return None
        return int(sel[0])

    # ---------- CRUD ----------
    def check_level_up(self):
        p = self.data["player"]
        needed = p["level"] * 50
        leveled = False
        while p["exp"] >= needed:
            p["exp"] -= needed
            p["level"] += 1
            leveled = True
            needed = p["level"] * 50
        if leveled:
            messagebox.showinfo("LEVEL UP!", f"*** You are now Level {p['level']}! ***")

    def add_game(self, values):
        game = {
            "id": self.data["next_id"],
            "title": values["title"],
            "status": values["status"],
            "rank": values["rank"],
            "genre": values["genre"],
            "platform": values["platform"],
            "rating": values["rating"],
            "notes": values["notes"],
            "hours": values["hours"],
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "date_completed": datetime.now().strftime("%Y-%m-%d") if values["status"] == STATUS_COMPLETED else None,
        }
        self.data["games"].append(game)
        self.data["next_id"] += 1
        exp_gain = 50 if values["status"] == STATUS_COMPLETED else (25 if values["status"] == STATUS_PLAYING else 10)
        self.data["player"]["exp"] += exp_gain
        self.check_level_up()
        save_data_for(self.username, self.data)
        self.refresh_table()

    def delete_selected(self):
        gid = self.current_selected_id()
        if gid is None:
            messagebox.showwarning("No selection", "Select a game first.")
            return
        game = next((g for g in self.data["games"] if g["id"] == gid), None)
        if not game:
            return
        if messagebox.askyesno("Confirm", f'Remove "{game["title"]}" from the Quest Log?'):
            self.data["games"] = [g for g in self.data["games"] if g["id"] != gid]
            save_data_for(self.username, self.data)
            self.refresh_table()

    # ---------- SEPARATE WINDOWS ----------
    def open_add_window(self):
        t = self.theme
        win = tk.Toplevel(self.root)
        win.title("Register New Quest")
        win.configure(bg=t["panel_bg"])
        win.geometry("420x520")

        fields = {}

        def row(label_text, widget_factory, default=""):
            ttk.Label(win, text=label_text).pack(anchor="w", padx=16, pady=(10, 2))
            widget = widget_factory()
            widget.pack(fill="x", padx=16)
            fields[label_text] = widget
            return widget

        title_entry = row("Game Title", lambda: ttk.Entry(win))

        ttk.Label(win, text="Status").pack(anchor="w", padx=16, pady=(10, 2))
        status_var = tk.StringVar(value=STATUS_PLAYING)
        status_box = ttk.Combobox(win, textvariable=status_var, values=STATUSES, state="readonly")
        status_box.pack(fill="x", padx=16)

        ttk.Label(win, text="Rank").pack(anchor="w", padx=16, pady=(10, 2))
        rank_var = tk.StringVar(value="E")
        rank_box = ttk.Combobox(win, textvariable=rank_var, values=RANKS, state="readonly")
        rank_box.pack(fill="x", padx=16)

        genre_entry = row("Genre", lambda: ttk.Entry(win))
        platform_entry = row("Platform", lambda: ttk.Entry(win))
        hours_entry = row("Hours Played", lambda: ttk.Entry(win))
        rating_entry = row("Rating (1-10)", lambda: ttk.Entry(win))
        notes_entry = row("Notes", lambda: ttk.Entry(win))

        def submit():
            title = title_entry.get().strip()
            if not title:
                messagebox.showerror("Missing Title", "Enter a game title.")
                return
            try:
                hours = float(hours_entry.get().strip()) if hours_entry.get().strip() else 0
            except ValueError:
                hours = 0
            values = {
                "title": title,
                "status": status_var.get(),
                "rank": rank_var.get(),
                "genre": genre_entry.get().strip(),
                "platform": platform_entry.get().strip(),
                "hours": hours,
                "rating": rating_entry.get().strip(),
                "notes": notes_entry.get().strip(),
            }
            self.add_game(values)
            win.destroy()

        ttk.Button(win, text="Register Quest", command=submit).pack(pady=18)

    def open_update_window(self):
        gid = self.current_selected_id()
        if gid is None:
            messagebox.showwarning("No selection", "Select a game first.")
            return
        game = next((g for g in self.data["games"] if g["id"] == gid), None)
        if not game:
            return

        t = self.theme
        win = tk.Toplevel(self.root)
        win.title(f"Update — {game['title']}")
        win.configure(bg=t["panel_bg"])
        win.geometry("380x300")

        ttk.Label(win, text=game["title"], style="Stat.TLabel").pack(pady=(16, 6))

        ttk.Label(win, text="Status").pack(anchor="w", padx=16, pady=(10, 2))
        status_var = tk.StringVar(value=game["status"])
        ttk.Combobox(win, textvariable=status_var, values=STATUSES, state="readonly").pack(fill="x", padx=16)

        ttk.Label(win, text="Hours Played").pack(anchor="w", padx=16, pady=(10, 2))
        hours_entry = ttk.Entry(win)
        hours_entry.insert(0, str(game.get("hours", 0)))
        hours_entry.pack(fill="x", padx=16)

        ttk.Label(win, text="Rating (1-10)").pack(anchor="w", padx=16, pady=(10, 2))
        rating_entry = ttk.Entry(win)
        rating_entry.insert(0, str(game.get("rating", "") or ""))
        rating_entry.pack(fill="x", padx=16)

        def submit():
            old_status = game["status"]
            new_status = status_var.get()
            game["status"] = new_status
            try:
                game["hours"] = float(hours_entry.get().strip()) if hours_entry.get().strip() else game.get("hours", 0)
            except ValueError:
                pass
            game["rating"] = rating_entry.get().strip()

            if new_status == STATUS_COMPLETED and old_status != STATUS_COMPLETED:
                game["date_completed"] = datetime.now().strftime("%Y-%m-%d")
                self.data["player"]["exp"] += 50
                self.check_level_up()

            save_data_for(self.username, self.data)
            self.refresh_table()
            win.destroy()

        ttk.Button(win, text="Save Update", command=submit).pack(pady=18)

    def open_status_window(self):
        t = self.theme
        win = tk.Toplevel(self.root)
        win.title("Status Window")
        win.configure(bg=t["panel_bg"])
        win.geometry("340x360")
        win.resizable(False, False)

        p = self.data["player"]
        needed = p["level"] * 50
        games = self.data["games"]
        playing = len([g for g in games if g["status"] == STATUS_PLAYING])
        completed = len([g for g in games if g["status"] == STATUS_COMPLETED])
        backlog = len([g for g in games if g["status"] == STATUS_BACKLOG])
        total_hours = sum(g.get("hours", 0) for g in games)

        ttk.Label(win, text="STATUS WINDOW", style="Header.TLabel").pack(pady=(20, 10))
        info = [
            f"Name  : {p['name']}",
            f"Level : {p['level']}",
            f"EXP   : {p['exp']} / {needed}",
            "",
            f"Playing   : {playing}",
            f"Completed : {completed}",
            f"Backlog   : {backlog}",
            f"Total Hours : {total_hours}",
        ]
        for line in info:
            ttk.Label(win, text=line, style="Stat.TLabel" if ":" in line else "TLabel").pack(anchor="w", padx=30, pady=2)

    def open_player_window(self):
        t = self.theme
        win = tk.Toplevel(self.root)
        win.title("Player Settings")
        win.configure(bg=t["panel_bg"])
        win.geometry("320x160")

        ttk.Label(win, text="Player Name").pack(anchor="w", padx=16, pady=(16, 2))
        name_entry = ttk.Entry(win)
        name_entry.insert(0, self.data["player"]["name"])
        name_entry.pack(fill="x", padx=16)

        def submit():
            name = name_entry.get().strip()
            if name:
                self.data["player"]["name"] = name
                save_data_for(self.username, self.data)
                self.refresh_table()
            win.destroy()

        ttk.Button(win, text="Save", command=submit).pack(pady=20)

    # ---------- THEME EDITOR WINDOW ----------
    def open_theme_editor(self):
        t = self.theme
        win = tk.Toplevel(self.root)
        win.title("Customize Theme")
        win.configure(bg=t["panel_bg"])
        win.geometry("360x460")

        color_fields = [
            ("bg", "Window Background"),
            ("panel_bg", "Panel Background"),
            ("accent", "Accent Color"),
            ("text", "Text Color"),
            ("subtext", "Subtext Color"),
            ("border", "Border Color"),
            ("success", "Success/Highlight Color"),
        ]

        swatches = {}

        def pick_color(key):
            initial = self.theme.get(key, "#ffffff")
            color = colorchooser.askcolor(color=initial, title=f"Choose {key}")
            if color and color[1]:
                self.theme[key] = color[1]
                swatches[key].configure(bg=color[1])

        for key, label in color_fields:
            row_frame = tk.Frame(win, bg=t["panel_bg"])
            row_frame.pack(fill="x", padx=16, pady=6)
            tk.Label(row_frame, text=label, bg=t["panel_bg"], fg=t["text"]).pack(side="left")
            sw = tk.Label(row_frame, text="   ", bg=self.theme.get(key, "#ffffff"), relief="solid", bd=1)
            sw.pack(side="right")
            swatches[key] = sw
            ttk.Button(row_frame, text="Pick", command=lambda k=key: pick_color(k)).pack(side="right", padx=8)

        ttk.Label(win, text="Font Size").pack(anchor="w", padx=16, pady=(16, 2))
        size_var = tk.IntVar(value=self.theme.get("font_size", 11))
        size_spin = ttk.Spinbox(win, from_=8, to=20, textvariable=size_var)
        size_spin.pack(fill="x", padx=16)

        def apply_and_save():
            self.theme["font_size"] = size_var.get()
            save_settings_for(self.username, self.theme)
            win.destroy()
            self.refresh_theme_everywhere()

        ttk.Button(win, text="Apply Theme", command=apply_and_save).pack(pady=20)


# ---------------------------------------------------------------
#  LOGIN / REGISTER SCREEN
# ---------------------------------------------------------------

LOGIN_THEME = DEFAULT_THEME  # neutral theme for the login gate itself


class LoginScreen:
    """Shown on launch (and after logout). Lets a user log in or
    register a brand-new account. Each account has its own private
    game log + theme under users_data/<username>/."""

    def __init__(self, root):
        self.root = root
        self.root.title("THE SYSTEM — Sign In")
        self.root.geometry("420x420")
        self.root.minsize(380, 400)
        t = LOGIN_THEME
        self.root.configure(bg=t["bg"])

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=t["bg"])
        style.configure("TLabel", background=t["bg"], foreground=t["text"], font=(t["font_family"], 11))
        style.configure("Header.TLabel", background=t["bg"], foreground=t["accent"],
                         font=(t["font_family"], 20, "bold"))
        style.configure("TButton", background=t["accent"], foreground=t["bg"],
                         font=(t["font_family"], 11, "bold"), padding=8)
        style.map("TButton", background=[("active", t["text"])])
        style.configure("TEntry", fieldbackground=t["panel_bg"], foreground=t["text"])
        style.configure("TNotebook", background=t["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=t["panel_bg"], foreground=t["subtext"],
                         font=(t["font_family"], 10, "bold"), padding=(16, 8))
        style.map("TNotebook.Tab", background=[("selected", t["accent"])], foreground=[("selected", t["bg"])])

        ttk.Label(root, text="THE SYSTEM", style="Header.TLabel").pack(pady=(30, 0))
        ttk.Label(root, text='"Arise, Player."').pack(pady=(0, 20))

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=24, pady=10)

        login_tab = ttk.Frame(notebook)
        register_tab = ttk.Frame(notebook)
        notebook.add(login_tab, text="Log In")
        notebook.add(register_tab, text="Create Account")

        self.build_login_tab(login_tab)
        self.build_register_tab(register_tab)

    def build_login_tab(self, parent):
        ttk.Label(parent, text="Username").pack(anchor="w", padx=20, pady=(24, 2))
        user_entry = ttk.Entry(parent)
        user_entry.pack(fill="x", padx=20)

        ttk.Label(parent, text="Password").pack(anchor="w", padx=20, pady=(14, 2))
        pass_entry = ttk.Entry(parent, show="*")
        pass_entry.pack(fill="x", padx=20)

        def submit(event=None):
            username = user_entry.get().strip()
            password = pass_entry.get()
            ok, msg = authenticate_user(username, password)
            if ok:
                self.launch_app(username)
            else:
                messagebox.showerror("Login Failed", msg)

        pass_entry.bind("<Return>", submit)
        ttk.Button(parent, text="Enter the System", command=submit).pack(pady=24)

    def build_register_tab(self, parent):
        ttk.Label(parent, text="Choose a Username").pack(anchor="w", padx=20, pady=(24, 2))
        user_entry = ttk.Entry(parent)
        user_entry.pack(fill="x", padx=20)

        ttk.Label(parent, text="Choose a Password (min 4 chars)").pack(anchor="w", padx=20, pady=(14, 2))
        pass_entry = ttk.Entry(parent, show="*")
        pass_entry.pack(fill="x", padx=20)

        ttk.Label(parent, text="Confirm Password").pack(anchor="w", padx=20, pady=(14, 2))
        confirm_entry = ttk.Entry(parent, show="*")
        confirm_entry.pack(fill="x", padx=20)

        def submit(event=None):
            username = user_entry.get().strip()
            password = pass_entry.get()
            confirm = confirm_entry.get()
            if password != confirm:
                messagebox.showerror("Mismatch", "Passwords do not match.")
                return
            ok, msg = register_user(username, password)
            if ok:
                messagebox.showinfo("Account Created", f'Welcome, {username}. Your Quest Log has been created.')
                self.launch_app(username)
            else:
                messagebox.showerror("Registration Failed", msg)

        confirm_entry.bind("<Return>", submit)
        ttk.Button(parent, text="Register", command=submit).pack(pady=24)

    def launch_app(self, username):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("980x620")
        self.root.minsize(760, 480)
        SystemApp(self.root, username)


# ---------------------------------------------------------------
def main():
    os.makedirs(USERS_DATA_DIR, exist_ok=True)
    root = tk.Tk()
    LoginScreen(root)
    root.mainloop()


if __name__ == "__main__":
    main()
