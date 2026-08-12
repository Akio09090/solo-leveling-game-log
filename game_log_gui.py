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
    "bg": "#05070d",
    "panel_bg": "#0b0f1a",
    "panel_bg_alt": "#0f1424",
    "accent": "#00e5ff",
    "accent2": "#ff2fd0",
    "text": "#e4f4ff",
    "subtext": "#5c7ba0",
    "border": "#16243d",
    "success": "#39ff9e",
    "danger": "#ff3860",
    "font_family": "Consolas",
    "font_size": 11,
}

THEME_PRESETS = {
    "Neon Cyan": {"bg": "#05070d", "panel_bg": "#0b0f1a", "panel_bg_alt": "#0f1424",
                  "accent": "#00e5ff", "accent2": "#ff2fd0", "text": "#e4f4ff",
                  "subtext": "#5c7ba0", "border": "#16243d", "success": "#39ff9e", "danger": "#ff3860"},
    "Red Gate (Crimson)": {"bg": "#0d0507", "panel_bg": "#1a0b0f", "panel_bg_alt": "#1f0f14",
                            "accent": "#ff2f5e", "accent2": "#ff8a00", "text": "#ffe4ec",
                            "subtext": "#a05c72", "border": "#3d1624", "success": "#ffb84d", "danger": "#ff3860"},
    "Guild Gold": {"bg": "#0d0a03", "panel_bg": "#1a1408", "panel_bg_alt": "#1f180a",
                   "accent": "#ffcc33", "accent2": "#ff8a00", "text": "#fff3d6",
                   "subtext": "#a08f5c", "border": "#3d3216", "success": "#8be07a", "danger": "#ff3860"},
    "Matrix Green": {"bg": "#040d08", "panel_bg": "#081a0f", "panel_bg_alt": "#0a1f13",
                      "accent": "#39ff9e", "accent2": "#00e5ff", "text": "#d6ffe9",
                      "subtext": "#5ca078", "border": "#163d26", "success": "#39ff9e", "danger": "#ff3860"},
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
    for k, v in DEFAULT_THEME.items():
        theme.setdefault(k, v)
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
        self.root.geometry("1040x660")
        self.root.minsize(800, 520)

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

        base = t["font_family"]
        size = t["font_size"]
        font_main = (base, size)
        font_bold = (base, size, "bold")
        font_mono_small = (base, size - 2)
        font_label = (base, size - 1, "bold")

        # --- base surfaces ---
        self.style.configure("TFrame", background=t["panel_bg"])
        self.style.configure("Root.TFrame", background=t["bg"])
        self.style.configure("Card.TFrame", background=t["panel_bg_alt"])
        self.style.configure("TLabel", background=t["panel_bg"], foreground=t["text"], font=font_main)

        # --- headers / branding ---
        self.style.configure("Header.TLabel", background=t["bg"], foreground=t["accent"],
                              font=(base, size + 8, "bold"))
        self.style.configure("SectionTitle.TLabel", background=t["panel_bg"], foreground=t["accent"],
                              font=(base, size + 1, "bold"))
        self.style.configure("Tag.TLabel", background=t["bg"], foreground=t["accent2"],
                              font=(base, size - 3, "bold"))
        self.style.configure("Sub.TLabel", background=t["panel_bg"], foreground=t["subtext"], font=font_mono_small)
        self.style.configure("SubRoot.TLabel", background=t["bg"], foreground=t["subtext"], font=font_mono_small)
        self.style.configure("Stat.TLabel", background=t["panel_bg"], foreground=t["success"], font=font_bold)
        self.style.configure("FieldLabel.TLabel", background=t["panel_bg"], foreground=t["subtext"],
                              font=(base, size - 2, "bold"))

        # --- buttons: flat neon-outline look, brighter on hover ---
        self.style.configure("TButton", background=t["accent"], foreground=t["bg"],
                              font=font_bold, borderwidth=0, focuscolor="", padding=(14, 9))
        self.style.map("TButton",
                        background=[("active", t["text"]), ("pressed", t["accent2"])],
                        foreground=[("active", t["bg"]), ("pressed", t["bg"])])

        self.style.configure("Ghost.TButton", background=t["panel_bg_alt"], foreground=t["accent"],
                              font=font_bold, borderwidth=1, focuscolor="", padding=(12, 8))
        self.style.map("Ghost.TButton",
                        background=[("active", t["border"])],
                        foreground=[("active", t["text"])])

        self.style.configure("Danger.TButton", background=t["panel_bg_alt"], foreground=t["danger"],
                              font=font_bold, borderwidth=1, focuscolor="", padding=(12, 8))
        self.style.map("Danger.TButton",
                        background=[("active", t["danger"])],
                        foreground=[("active", t["bg"])])

        # --- table ---
        self.style.configure("Treeview", background=t["panel_bg_alt"], fieldbackground=t["panel_bg_alt"],
                              foreground=t["text"], font=font_main, rowheight=30, borderwidth=0)
        self.style.configure("Treeview.Heading", background=t["border"], foreground=t["accent"],
                              font=(base, size - 1, "bold"), relief="flat", padding=(8, 8))
        self.style.map("Treeview.Heading", background=[("active", t["border"])])
        self.style.map("Treeview", background=[("selected", t["accent"])],
                        foreground=[("selected", t["bg"])])
        self.style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        # --- tabs: underline style instead of boxy ---
        self.style.configure("TNotebook", background=t["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=t["bg"], foreground=t["subtext"],
                              font=(base, size, "bold"), padding=(18, 10), borderwidth=0)
        self.style.map("TNotebook.Tab",
                        background=[("selected", t["bg"])],
                        foreground=[("selected", t["accent"])])
        self.style.layout("TNotebook.Tab", [
            ("Notebook.tab", {"sticky": "nswe", "children": [
                ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
                    ("Notebook.label", {"side": "top", "sticky": ""})
                ]})
            ]})
        ])

        # --- inputs ---
        self.style.configure("TEntry", fieldbackground=t["panel_bg_alt"], foreground=t["text"],
                              insertcolor=t["accent"], borderwidth=1, padding=8,
                              bordercolor=t["border"], lightcolor=t["border"], darkcolor=t["border"])
        self.style.map("TEntry",
                        bordercolor=[("focus", t["accent"])],
                        lightcolor=[("focus", t["accent"])])
        self.style.configure("TCombobox", fieldbackground=t["panel_bg_alt"], background=t["panel_bg_alt"],
                              foreground=t["text"], arrowcolor=t["accent"], borderwidth=1, padding=8,
                              bordercolor=t["border"])
        self.style.map("TCombobox", fieldbackground=[("readonly", t["panel_bg_alt"])],
                        foreground=[("readonly", t["text"])])
        self.style.configure("TSpinbox", fieldbackground=t["panel_bg_alt"], foreground=t["text"],
                              arrowcolor=t["accent"], borderwidth=1, padding=6, bordercolor=t["border"])
        self.style.configure("TScrollbar", background=t["panel_bg_alt"], troughcolor=t["bg"],
                              bordercolor=t["bg"], arrowcolor=t["accent"])
        self.style.configure("Vertical.TScrollbar", background=t["border"], troughcolor=t["bg"])
        self.root.option_add("*TCombobox*Listbox.background", t["panel_bg_alt"])
        self.root.option_add("*TCombobox*Listbox.foreground", t["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", t["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", t["bg"])

    # ---------- toplevel window styling helper ----------
    def style_toplevel(self, win, w, h, title):
        """Give a Toplevel a consistent dark cyber-styled frame + header bar."""
        t = self.theme
        win.configure(bg=t["bg"])
        win.geometry(f"{w}x{h}")
        win.title(title)

        top_bar = tk.Frame(win, bg=t["bg"], height=4)
        top_bar.pack(fill="x", side="top")
        accent_line = tk.Frame(win, bg=t["accent"], height=2)
        accent_line.pack(fill="x", side="top")

        header = tk.Frame(win, bg=t["bg"])
        header.pack(fill="x", padx=18, pady=(14, 4))
        tk.Label(header, text=title.upper(), bg=t["bg"], fg=t["accent"],
                  font=(t["font_family"], t["font_size"] + 2, "bold")).pack(side="left")

        body = tk.Frame(win, bg=t["panel_bg"], highlightbackground=t["border"],
                          highlightthickness=1)
        body.pack(fill="both", expand=True, padx=18, pady=(4, 18))
        return body

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
        t = self.theme
        menubar = tk.Menu(self.root, bg=t["panel_bg"], fg=t["text"], activebackground=t["accent"],
                           activeforeground=t["bg"], borderwidth=0, tearoff=0)
        menu_kwargs = dict(bg=t["panel_bg"], fg=t["text"], activebackground=t["accent"],
                            activeforeground=t["bg"], borderwidth=0, tearoff=0)

        theme_menu = tk.Menu(menubar, **menu_kwargs)
        for name in THEME_PRESETS:
            theme_menu.add_command(label=name, command=lambda n=name: self.apply_preset(n))
        theme_menu.add_separator()
        theme_menu.add_command(label="Custom Theme Editor...", command=self.open_theme_editor)
        menubar.add_cascade(label="Theme", menu=theme_menu)

        window_menu = tk.Menu(menubar, **menu_kwargs)
        window_menu.add_command(label="Status Window", command=self.open_status_window)
        window_menu.add_command(label="Add Game Window", command=self.open_add_window)
        window_menu.add_command(label="Player Settings Window", command=self.open_player_window)
        menubar.add_cascade(label="Windows", menu=window_menu)

        account_menu = tk.Menu(menubar, **menu_kwargs)
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

        # top accent line — thin neon strip across the very top of the window
        tk.Frame(self.root, bg=t["accent"], height=2).pack(fill="x", side="top")

        header = ttk.Frame(self.root, style="Root.TFrame")
        header.pack(fill="x", padx=22, pady=(16, 2))
        title_box = ttk.Frame(header, style="Root.TFrame")
        title_box.pack(side="left")
        ttk.Label(title_box, text="THE SYSTEM", style="Header.TLabel").pack(anchor="w")
        ttk.Label(title_box, text="GAME LOG // QUEST TRACKER", style="SubRoot.TLabel").pack(anchor="w")

        player_box = ttk.Frame(header, style="Root.TFrame")
        player_box.pack(side="right")
        self.player_name_label = ttk.Label(player_box, text="", style="Header.TLabel")
        self.player_name_label.configure(font=(t["font_family"], t["font_size"] + 2, "bold"))
        self.player_name_label.pack(anchor="e")
        self.player_exp_label = ttk.Label(player_box, text="", style="SubRoot.TLabel")
        self.player_exp_label.pack(anchor="e")

        # divider
        tk.Frame(self.root, bg=t["border"], height=1).pack(fill="x", padx=22, pady=(12, 12))

        btn_bar = ttk.Frame(self.root, style="Root.TFrame")
        btn_bar.pack(fill="x", padx=22, pady=(0, 14))
        ttk.Button(btn_bar, text="+  Register New Quest", command=self.open_add_window).pack(side="left")
        ttk.Button(btn_bar, text="Update Selected", style="Ghost.TButton",
                   command=self.open_update_window).pack(side="left", padx=(10, 0))
        ttk.Button(btn_bar, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_selected).pack(side="left", padx=(10, 0))
        ttk.Button(btn_bar, text="Status Window", style="Ghost.TButton",
                   command=self.open_status_window).pack(side="right", padx=(10, 0))
        ttk.Button(btn_bar, text="Customize Theme", style="Ghost.TButton",
                   command=self.open_theme_editor).pack(side="right")

        # Tabs = separate filtered windows within main frame
        notebook_wrap = ttk.Frame(self.root, style="Root.TFrame")
        notebook_wrap.pack(fill="both", expand=True, padx=22, pady=(0, 20))
        self.notebook = ttk.Notebook(notebook_wrap)
        self.notebook.pack(fill="both", expand=True)

        self.trees = {}
        for status in ["All"] + STATUSES:
            frame = ttk.Frame(self.notebook, style="Card.TFrame")
            self.notebook.add(frame, text=f"  {status}  ")
            tree = self.build_tree(frame)
            self.trees[status] = tree

    def build_tree(self, parent):
        t = self.theme
        wrap = tk.Frame(parent, bg=t["panel_bg_alt"], highlightbackground=t["border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=6, pady=6)

        cols = ("id", "title", "rank", "genre", "platform", "hours", "rating", "added")
        tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        headings = {"id": "ID", "title": "TITLE", "rank": "RANK", "genre": "GENRE",
                    "platform": "PLATFORM", "hours": "HRS", "rating": "RTG", "added": "ADDED"}
        widths = {"id": 44, "title": 260, "rank": 64, "genre": 130,
                  "platform": 110, "hours": 60, "rating": 56, "added": 96}
        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="w")

        vsb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=(2, 0), pady=2)

        tree.tag_configure("odd", background=t["panel_bg_alt"])
        tree.tag_configure("even", background=t["panel_bg"])
        tree.tag_configure("playing", foreground=t["accent"])
        tree.tag_configure("completed", foreground=t["success"])
        tree.tag_configure("backlog", foreground=t["subtext"])
        return tree

    def player_summary_text(self):
        p = self.data["player"]
        needed = p["level"] * 50
        return p["name"], f"LV.{p['level']}   EXP {p['exp']}/{needed}"

    # ---------- TABLE REFRESH ----------
    def refresh_table(self):
        status_tag = {STATUS_PLAYING: "playing", STATUS_COMPLETED: "completed", STATUS_BACKLOG: "backlog"}
        for status, tree in self.trees.items():
            for row in tree.get_children():
                tree.delete(row)
            games = self.data["games"] if status == "All" else [g for g in self.data["games"] if g["status"] == status]
            for i, g in enumerate(games):
                stripe = "even" if i % 2 == 0 else "odd"
                tags = (stripe, status_tag.get(g["status"], ""))
                tree.insert("", "end", iid=str(g["id"]), tags=tags, values=(
                    g["id"], g["title"], g["rank"], g.get("genre", ""), g.get("platform", ""),
                    g.get("hours", 0), g.get("rating", "") or "-", g.get("date_added", "")
                ))
        name, exp_text = self.player_summary_text()
        self.player_name_label.configure(text=name)
        self.player_exp_label.configure(text=exp_text)

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
        win = tk.Toplevel(self.root)
        body = self.style_toplevel(win, 440, 600, "Register New Quest")

        def row(parent, label_text, widget_factory):
            ttk.Label(parent, text=label_text.upper(), style="FieldLabel.TLabel").pack(anchor="w", padx=18, pady=(12, 3))
            widget = widget_factory()
            widget.pack(fill="x", padx=18)
            return widget

        title_entry = row(body, "Game Title", lambda: ttk.Entry(body))

        status_var = tk.StringVar(value=STATUS_PLAYING)
        row(body, "Status", lambda: ttk.Combobox(body, textvariable=status_var, values=STATUSES, state="readonly"))

        rank_var = tk.StringVar(value="E")
        row(body, "Rank", lambda: ttk.Combobox(body, textvariable=rank_var, values=RANKS, state="readonly"))

        genre_entry = row(body, "Genre", lambda: ttk.Entry(body))
        platform_entry = row(body, "Platform", lambda: ttk.Entry(body))
        hours_entry = row(body, "Hours Played", lambda: ttk.Entry(body))
        rating_entry = row(body, "Rating (1-10)", lambda: ttk.Entry(body))
        notes_entry = row(body, "Notes", lambda: ttk.Entry(body))

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

        ttk.Button(body, text="Register Quest", command=submit).pack(pady=22)

    def open_update_window(self):
        gid = self.current_selected_id()
        if gid is None:
            messagebox.showwarning("No selection", "Select a game first.")
            return
        game = next((g for g in self.data["games"] if g["id"] == gid), None)
        if not game:
            return

        win = tk.Toplevel(self.root)
        body = self.style_toplevel(win, 400, 360, f"Update — {game['title']}")

        ttk.Label(body, text="STATUS", style="FieldLabel.TLabel").pack(anchor="w", padx=18, pady=(14, 3))
        status_var = tk.StringVar(value=game["status"])
        ttk.Combobox(body, textvariable=status_var, values=STATUSES, state="readonly").pack(fill="x", padx=18)

        ttk.Label(body, text="HOURS PLAYED", style="FieldLabel.TLabel").pack(anchor="w", padx=18, pady=(12, 3))
        hours_entry = ttk.Entry(body)
        hours_entry.insert(0, str(game.get("hours", 0)))
        hours_entry.pack(fill="x", padx=18)

        ttk.Label(body, text="RATING (1-10)", style="FieldLabel.TLabel").pack(anchor="w", padx=18, pady=(12, 3))
        rating_entry = ttk.Entry(body)
        rating_entry.insert(0, str(game.get("rating", "") or ""))
        rating_entry.pack(fill="x", padx=18)

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

        ttk.Button(body, text="Save Update", command=submit).pack(pady=20)

    def open_status_window(self):
        win = tk.Toplevel(self.root)
        win.resizable(False, False)
        body = self.style_toplevel(win, 360, 420, "Status Window")

        p = self.data["player"]
        needed = p["level"] * 50
        games = self.data["games"]
        playing = len([g for g in games if g["status"] == STATUS_PLAYING])
        completed = len([g for g in games if g["status"] == STATUS_COMPLETED])
        backlog = len([g for g in games if g["status"] == STATUS_BACKLOG])
        total_hours = sum(g.get("hours", 0) for g in games)

        t = self.theme

        def stat_row(parent, label, value, value_style="Stat.TLabel"):
            r = tk.Frame(parent, bg=t["panel_bg"])
            r.pack(fill="x", padx=6, pady=3)
            ttk.Label(r, text=label.upper(), style="FieldLabel.TLabel").pack(side="left")
            ttk.Label(r, text=str(value), style=value_style).pack(side="right")

        stat_row(body, "Player", p["name"])
        stat_row(body, "Level", p["level"])
        stat_row(body, "EXP", f"{p['exp']} / {needed}")
        tk.Frame(body, bg=t["border"], height=1).pack(fill="x", padx=6, pady=10)
        stat_row(body, "Playing", playing)
        stat_row(body, "Completed", completed)
        stat_row(body, "Backlog", backlog)
        stat_row(body, "Total Hours", total_hours)

    def open_player_window(self):
        win = tk.Toplevel(self.root)
        body = self.style_toplevel(win, 340, 200, "Player Settings")

        ttk.Label(body, text="PLAYER NAME", style="FieldLabel.TLabel").pack(anchor="w", padx=18, pady=(18, 3))
        name_entry = ttk.Entry(body)
        name_entry.insert(0, self.data["player"]["name"])
        name_entry.pack(fill="x", padx=18)

        def submit():
            name = name_entry.get().strip()
            if name:
                self.data["player"]["name"] = name
                save_data_for(self.username, self.data)
                self.refresh_table()
            win.destroy()

        ttk.Button(body, text="Save", command=submit).pack(pady=22)

    # ---------- THEME EDITOR WINDOW ----------
    def open_theme_editor(self):
        win = tk.Toplevel(self.root)
        t = self.theme
        body = self.style_toplevel(win, 400, 560, "Customize Theme")

        color_fields = [
            ("bg", "Window Background"),
            ("panel_bg", "Panel Background"),
            ("panel_bg_alt", "Panel Background (Alt)"),
            ("accent", "Accent Color"),
            ("accent2", "Accent Color 2"),
            ("text", "Text Color"),
            ("subtext", "Subtext Color"),
            ("border", "Border Color"),
            ("success", "Success Color"),
            ("danger", "Danger Color"),
        ]

        swatches = {}

        def pick_color(key):
            initial = self.theme.get(key, "#ffffff")
            color = colorchooser.askcolor(color=initial, title=f"Choose {key}")
            if color and color[1]:
                self.theme[key] = color[1]
                swatches[key].configure(bg=color[1])

        canvas_wrap = tk.Frame(body, bg=t["panel_bg"])
        canvas_wrap.pack(fill="both", expand=True, padx=4, pady=4)

        for key, label in color_fields:
            row_frame = tk.Frame(canvas_wrap, bg=t["panel_bg"])
            row_frame.pack(fill="x", padx=14, pady=5)
            tk.Label(row_frame, text=label.upper(), bg=t["panel_bg"], fg=t["subtext"],
                      font=(t["font_family"], t["font_size"] - 2, "bold")).pack(side="left")
            ttk.Button(row_frame, text="Pick", style="Ghost.TButton",
                       command=lambda k=key: pick_color(k)).pack(side="right", padx=(8, 0))
            sw = tk.Label(row_frame, text="      ", bg=self.theme.get(key, "#ffffff"),
                          relief="flat", highlightbackground=t["border"], highlightthickness=1)
            sw.pack(side="right")
            swatches[key] = sw

        tk.Frame(body, bg=t["border"], height=1).pack(fill="x", padx=14, pady=10)

        ttk.Label(body, text="FONT SIZE", style="FieldLabel.TLabel").pack(anchor="w", padx=14, pady=(0, 3))
        size_var = tk.IntVar(value=self.theme.get("font_size", 11))
        size_spin = ttk.Spinbox(body, from_=8, to=20, textvariable=size_var)
        size_spin.pack(fill="x", padx=14)

        def apply_and_save():
            self.theme["font_size"] = size_var.get()
            save_settings_for(self.username, self.theme)
            win.destroy()
            self.refresh_theme_everywhere()

        ttk.Button(body, text="Apply Theme", command=apply_and_save).pack(pady=20)


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
        self.root.geometry("440x480")
        self.root.minsize(400, 460)
        t = LOGIN_THEME
        self.root.configure(bg=t["bg"])

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=t["bg"])
        style.configure("Card.TFrame", background=t["panel_bg"])
        style.configure("TLabel", background=t["bg"], foreground=t["text"], font=(t["font_family"], 11))
        style.configure("CardLabel.TLabel", background=t["panel_bg"], foreground=t["text"],
                         font=(t["font_family"], 11))
        style.configure("FieldLabel.TLabel", background=t["panel_bg"], foreground=t["subtext"],
                         font=(t["font_family"], t["font_size"] - 2, "bold"))
        style.configure("Header.TLabel", background=t["bg"], foreground=t["accent"],
                         font=(t["font_family"], 26, "bold"))
        style.configure("SubRoot.TLabel", background=t["bg"], foreground=t["subtext"],
                         font=(t["font_family"], 10))
        style.configure("TButton", background=t["accent"], foreground=t["bg"],
                         font=(t["font_family"], 11, "bold"), borderwidth=0, focuscolor="", padding=(14, 10))
        style.map("TButton", background=[("active", t["text"]), ("pressed", t["accent2"])])
        style.configure("TEntry", fieldbackground=t["panel_bg_alt"], foreground=t["text"],
                         insertcolor=t["accent"], borderwidth=1, padding=8,
                         bordercolor=t["border"], lightcolor=t["border"], darkcolor=t["border"])
        style.map("TEntry", bordercolor=[("focus", t["accent"])])
        style.configure("TNotebook", background=t["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=t["bg"], foreground=t["subtext"],
                         font=(t["font_family"], 10, "bold"), padding=(18, 10), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", t["bg"])],
                   foreground=[("selected", t["accent"])])
        style.layout("TNotebook.Tab", [
            ("Notebook.tab", {"sticky": "nswe", "children": [
                ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
                    ("Notebook.label", {"side": "top", "sticky": ""})
                ]})
            ]})
        ])

        tk.Frame(root, bg=t["accent"], height=2).pack(fill="x", side="top")

        ttk.Label(root, text="THE SYSTEM", style="Header.TLabel").pack(pady=(34, 0))
        ttk.Label(root, text='"ARISE, PLAYER."', style="SubRoot.TLabel").pack(pady=(2, 24))

        card = tk.Frame(root, bg=t["panel_bg"], highlightbackground=t["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 28))

        notebook = ttk.Notebook(card)
        notebook.pack(fill="both", expand=True, padx=4, pady=4)

        login_tab = ttk.Frame(notebook, style="Card.TFrame")
        register_tab = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(login_tab, text="  LOG IN  ")
        notebook.add(register_tab, text="  CREATE ACCOUNT  ")

        self.build_login_tab(login_tab)
        self.build_register_tab(register_tab)

    def build_login_tab(self, parent):
        ttk.Label(parent, text="USERNAME", style="FieldLabel.TLabel").pack(anchor="w", padx=22, pady=(26, 3))
        user_entry = ttk.Entry(parent)
        user_entry.pack(fill="x", padx=22)

        ttk.Label(parent, text="PASSWORD", style="FieldLabel.TLabel").pack(anchor="w", padx=22, pady=(16, 3))
        pass_entry = ttk.Entry(parent, show="*")
        pass_entry.pack(fill="x", padx=22)

        def submit(event=None):
            username = user_entry.get().strip()
            password = pass_entry.get()
            ok, msg = authenticate_user(username, password)
            if ok:
                self.launch_app(username)
            else:
                messagebox.showerror("Login Failed", msg)

        pass_entry.bind("<Return>", submit)
        ttk.Button(parent, text="ENTER THE SYSTEM", command=submit).pack(pady=28, padx=22, fill="x")

    def build_register_tab(self, parent):
        ttk.Label(parent, text="CHOOSE A USERNAME", style="FieldLabel.TLabel").pack(anchor="w", padx=22, pady=(26, 3))
        user_entry = ttk.Entry(parent)
        user_entry.pack(fill="x", padx=22)

        ttk.Label(parent, text="CHOOSE A PASSWORD (MIN 4 CHARS)", style="FieldLabel.TLabel").pack(anchor="w", padx=22, pady=(16, 3))
        pass_entry = ttk.Entry(parent, show="*")
        pass_entry.pack(fill="x", padx=22)

        ttk.Label(parent, text="CONFIRM PASSWORD", style="FieldLabel.TLabel").pack(anchor="w", padx=22, pady=(16, 3))
        confirm_entry = ttk.Entry(parent, show="*")
        confirm_entry.pack(fill="x", padx=22)

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
        ttk.Button(parent, text="REGISTER", command=submit).pack(pady=24, padx=22, fill="x")

    def launch_app(self, username):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("1040x660")
        self.root.minsize(800, 520)
        SystemApp(self.root, username)


# ---------------------------------------------------------------
def main():
    os.makedirs(USERS_DATA_DIR, exist_ok=True)
    root = tk.Tk()
    LoginScreen(root)
    root.mainloop()


if __name__ == "__main__":
    main()
