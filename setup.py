# -*- coding: utf-8 -*-
"""
BVBC Payroll System — Windows Setup Wizard v7.0
Fixed: text alignment, Continue button, optimized layout
"""
import os, sys, shutil, ctypes, subprocess, threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ── App constants ─────────────────────────────────────────────────────────────
APP_NAME    = "BVBC Payroll System"
APP_VER     = "7.0"
PUBLISHER   = "Baptist Voice Bible College"
INSTALL_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\BVBCPayroll"
DEFAULT_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "BVBC Payroll System")

MAR  = "#4A0909"
GLD  = "#C9A84C"
WHT  = "#FFFFFF"
BG   = "#F5F0E8"
BG2  = "#EDE8DC"
DARK = "#2A0000"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Helpers ───────────────────────────────────────────────────────────────────
def is_admin():
    try:    return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def request_admin():
    """Request elevation only on Windows. Safe to call on any OS."""
    try:
        if not is_admin():
            # Re-launch elevated
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable,
                f'"{os.path.abspath(__file__)}"', SCRIPT_DIR, 1)
            if ret > 32:   # ShellExecute succeeded — exit this instance
                sys.exit()
            # If elevation failed (ret <= 32), continue without admin
    except Exception:
        pass   # Not on Windows or ctypes unavailable — continue anyway

def _find_python3():
    """Find python.exe — searches PATH, common install locations."""
    # Current interpreter first
    if os.path.exists(sys.executable):
        return sys.executable
    # Common Windows locations
    for candidate in [
        os.path.join(os.path.dirname(sys.executable), "python.exe"),
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",
        r"C:\Python39\python.exe",
        r"C:\Python38\python.exe",
    ]:
        if os.path.exists(candidate):
            return candidate
    # Try PATH
    try:
        r = subprocess.run(["where", "python"], capture_output=True, text=True)
        for line in r.stdout.strip().splitlines():
            line = line.strip()
            if line and os.path.exists(line):
                return line
    except Exception:
        pass
    return "python"


def _find_pythonw():
    """Find pythonw.exe (no console window). Falls back to python.exe."""
    # Same directory as current interpreter
    py_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(py_dir, "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    # Common locations
    for base in [r"C:\Python311", r"C:\Python310", r"C:\Python39",
                 r"C:\Python38", r"C:\Users\Public\Python"]:
        candidate = os.path.join(base, "pythonw.exe")
        if os.path.exists(candidate):
            return candidate
    # AppData local
    local = os.environ.get("LOCALAPPDATA", "")
    for sub in [r"Programs\Python\Python311", r"Programs\Python\Python310",
                r"Programs\Python\Python39", r"Programs\Python\Python38"]:
        candidate = os.path.join(local, sub, "pythonw.exe")
        if os.path.exists(candidate):
            return candidate
    # Try PATH
    try:
        r = subprocess.run(["where", "pythonw"], capture_output=True, text=True)
        for line in r.stdout.strip().splitlines():
            line = line.strip()
            if line and os.path.exists(line):
                return line
    except Exception:
        pass
    # Fall back to python.exe
    return _find_python3()


def create_lnk(lnk_path, target, args="", wdir="", icon="", desc=""):
    """
    Create a .lnk shortcut using PowerShell (always available on Win7+).
    This is the most reliable method — no pywin32 dependency needed.
    """
    # Escape single quotes for PowerShell
    def ps_str(s): return s.replace("'", "''")

    ps_lines = [
        f"$ws = New-Object -ComObject WScript.Shell",
        f"$s  = $ws.CreateShortcut('{ps_str(lnk_path)}')",
        f"$s.TargetPath      = '{ps_str(target)}'",
    ]
    if args:  ps_lines.append(f"$s.Arguments       = '{ps_str(args)}'")
    if wdir:  ps_lines.append(f"$s.WorkingDirectory = '{ps_str(wdir)}'")
    if icon:  ps_lines.append(f"$s.IconLocation    = '{ps_str(icon)}'")
    if desc:  ps_lines.append(f"$s.Description     = '{ps_str(desc)}'")
    ps_lines.append("$s.Save()")

    ps_cmd = "; ".join(ps_lines)
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-Command", ps_cmd],
            capture_output=True, text=True, timeout=20)
        if r.returncode == 0 and os.path.exists(lnk_path):
            return True
    except Exception:
        pass
    return False


# ── Main installer class ───────────────────────────────────────────────────────
class Installer(tk.Tk):
    PAGES = ["Welcome","Info","Directory","Confirm","Install","Done"]

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Setup")
        self.resizable(False, False)
        self.configure(bg=BG)

        W, H = 600, 560
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        # Make sure it fits on screen
        H = min(H, sh - 80)
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        # Window icon
        ico = os.path.join(SCRIPT_DIR, "assets", "bvbc.ico")
        if os.path.exists(ico):
            try: self.iconbitmap(ico)
            except: pass

        self.install_dir    = tk.StringVar(value=DEFAULT_DIR)
        self.want_desktop   = tk.BooleanVar(value=True)
        self.want_startmenu = tk.BooleanVar(value=True)
        self.launch_now     = tk.BooleanVar(value=True)
        self.page_idx       = 0

        self.grid_rowconfigure(2, weight=1)   # body row expands
        self.grid_columnconfigure(0, weight=1)
        self._make_header()
        self._make_step_bar()
        self._make_body()
        self._make_buttons()
        self.show_page(0)

    # ── Header ────────────────────────────────────────────────────────────────
    def _make_header(self):
        hdr = tk.Frame(self, bg=MAR, height=78)
        hdr.grid(row=0, column=0, sticky="ew"); hdr.grid_propagate(False)

        try:
            from PIL import Image, ImageTk
            # Try PNG first (more reliable), fall back to ICO
            logo_p = os.path.join(SCRIPT_DIR, "assets", "logo.png")
            ico_p  = os.path.join(SCRIPT_DIR, "assets", "bvbc.ico")
            src = logo_p if os.path.exists(logo_p) else ico_p
            if os.path.exists(src):
                img = Image.open(src).convert("RGBA").resize((54, 54), Image.LANCZOS)
                self._logo = ImageTk.PhotoImage(img)
                tk.Label(hdr, image=self._logo, bg=MAR).place(x=16, rely=0.5, anchor="w")
        except Exception:
            pass

        tk.Label(hdr, text=APP_NAME,
                 bg=MAR, fg=GLD,
                 font=("Segoe UI", 16, "bold")).place(x=82, rely=0.36, anchor="w")
        tk.Label(hdr, text=f"Version {APP_VER}  ·  {PUBLISHER}",
                 bg=MAR, fg="#D4B483",
                 font=("Segoe UI", 9)).place(x=82, rely=0.70, anchor="w")

        tk.Frame(self, bg=GLD, height=3).grid(row=1, column=0, sticky="ew")

    # ── Step indicator bar ────────────────────────────────────────────────────
    def _make_step_bar(self):
        bar = tk.Frame(self, bg=BG2, height=30)
        bar.grid(row=2, column=0, sticky="ew"); bar.grid_propagate(False)
        self._step_labels = []
        steps = ["Welcome", "Info", "Location", "Confirm", "Install", "Done"]
        for i, s in enumerate(steps):
            lbl = tk.Label(bar, text=f"{i+1}. {s}",
                           bg=BG2, fg="#999",
                           font=("Segoe UI", 8))
            lbl.pack(side="left", padx=(14 if i == 0 else 8, 0))
            if i < len(steps) - 1:
                tk.Label(bar, text="›", bg=BG2, fg="#BBB",
                         font=("Segoe UI", 9)).pack(side="left", padx=(4, 0))
            self._step_labels.append(lbl)
        tk.Frame(self, bg="#D0C8B8", height=1).grid(row=3, column=0, sticky="ew")

    def _update_steps(self):
        for i, lbl in enumerate(self._step_labels):
            if i == self.page_idx:
                lbl.config(fg=MAR, font=("Segoe UI", 8, "bold"))
            elif i < self.page_idx:
                lbl.config(fg="#2D7A2D", font=("Segoe UI", 8))
            else:
                lbl.config(fg="#999", font=("Segoe UI", 8))

    # ── Body canvas ───────────────────────────────────────────────────────────
    def _make_body(self):
        self.body = tk.Frame(self, bg=BG)
        self.body.grid(row=4, column=0, sticky="nsew")
        self.grid_rowconfigure(4, weight=1)

    def _clear(self):
        for w in self.body.winfo_children():
            w.destroy()

    # ── Button bar ────────────────────────────────────────────────────────────
    def _make_buttons(self):
        tk.Frame(self, bg="#C0B8A8", height=1).grid(row=5, column=0, sticky="ew")
        bar = tk.Frame(self, bg="#EAE4D8", pady=10)
        bar.grid(row=6, column=0, sticky="ew")

        self.btn_cancel = tk.Button(
            bar, text="Cancel", width=10,
            font=("Segoe UI", 10), relief="flat",
            bg="#C8C0B0", fg="#333",
            activebackground="#B8B0A0",
            cursor="hand2", command=self._on_cancel)
        self.btn_cancel.pack(side="right", padx=(0, 16))

        self.btn_next = tk.Button(
            bar, text="Next  ›", width=14,
            font=("Segoe UI", 10, "bold"), relief="flat",
            bg=MAR, fg=WHT,
            activebackground="#700E0E",
            cursor="hand2", command=self._on_next)
        self.btn_next.pack(side="right", padx=(0, 6))

        self.btn_back = tk.Button(
            bar, text="‹  Back", width=10,
            font=("Segoe UI", 10), relief="flat",
            bg="#C8C0B0", fg="#333",
            activebackground="#B8B0A0",
            cursor="hand2", command=self._on_back, state="disabled")
        self.btn_back.pack(side="right", padx=(0, 4))

    # ── Page header helper ────────────────────────────────────────────────────
    def _pg_hdr(self, title, subtitle=""):
        tk.Label(self.body, text=title,
                 bg=BG, fg=MAR,
                 font=("Segoe UI", 13, "bold"),
                 anchor="w").pack(fill="x", padx=28, pady=(12, 2))
        if subtitle:
            tk.Label(self.body, text=subtitle,
                     bg=BG, fg="#666",
                     font=("Segoe UI", 9),
                     anchor="w").pack(fill="x", padx=28, pady=(0, 8))
        tk.Frame(self.body, bg=GLD, height=2).pack(fill="x", padx=28, pady=(0, 12))

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 0 — WELCOME
    # ═════════════════════════════════════════════════════════════════════════
    def _page_welcome(self):
        self._pg_hdr("Welcome to Setup",
                     f"This wizard will guide you through the installation of {APP_NAME}.")

        card = tk.Frame(self.body, bg=WHT,
                        highlightbackground="#C8C0B0", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 4))

        # Logo area
        logo_row = tk.Frame(card, bg=MAR, height=52)
        logo_row.pack(fill="x"); logo_row.pack_propagate(False)
        # Load logo image for banner
        _xoff = 18
        try:
            from PIL import Image, ImageTk
            _lp = os.path.join(SCRIPT_DIR, "assets", "logo.png")
            if os.path.exists(_lp):
                _im = Image.open(_lp).convert("RGBA").resize((44,44), Image.LANCZOS)
                self._card_logo = ImageTk.PhotoImage(_im)
                tk.Label(logo_row, image=self._card_logo, bg=MAR).place(x=12, rely=0.5, anchor="w")
                _xoff = 66
        except Exception:
            pass
        tk.Label(logo_row, text=APP_NAME,
                 bg=MAR, fg=GLD,
                 font=("Segoe UI", 15, "bold")).place(x=_xoff, rely=0.35, anchor="w")
        tk.Label(logo_row, text=PUBLISHER,
                 bg=MAR, fg="#D4B483",
                 font=("Segoe UI", 9)).place(x=_xoff, rely=0.70, anchor="w")

        tk.Frame(card, bg=GLD, height=2).pack(fill="x")

        body_txt = tk.Frame(card, bg=WHT); body_txt.pack(fill="both", expand=True, padx=20, pady=8)

        lines = [
            ("Setup will install the following:", MAR, "bold"),
            ("", "#333", "normal"),
            ("   >>  Employee Management & Profiles", "#333", "normal"),
            ("   >>  Weekly / Semi-Monthly / Monthly Payroll", "#333", "normal"),
            ("   >>  Complete Deductions & Savings Tracking", "#333", "normal"),
            ("   >>  Professional Excel Payslip Export", "#333", "normal"),
            ("   >>  Reports and Analytics Dashboard", "#333", "normal"),
            ("", "#333", "normal"),
            ("Click  Next  to continue, or  Cancel  to exit.", "#555", "italic"),
        ]
        for text, color, style in lines:
            tk.Label(body_txt, text=text,
                     bg=WHT, fg=color,
                     font=("Segoe UI", 10, style),
                     anchor="w").pack(fill="x", pady=1)

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 1 — SYSTEM INFORMATION  (fixed alignment)
    # ═════════════════════════════════════════════════════════════════════════
    def _page_info(self):
        self._pg_hdr("System Information",
                     "Review system details before continuing.")

        # Use a Frame+Canvas with NO word-wrap — fixed-width monospace text
        outer = tk.Frame(self.body, bg=WHT,
                         highlightbackground="#C8C0B0", highlightthickness=1)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 8))

        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side="right", fill="y")
        cv = tk.Canvas(outer, bg=WHT, highlightthickness=0,
                       yscrollcommand=vsb.set)
        cv.pack(side="left", fill="both", expand=True)
        vsb.config(command=cv.yview)

        inner = tk.Frame(cv, bg=WHT, padx=14, pady=10)
        win = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",
                lambda e: cv.itemconfig(win, width=e.width))
        cv.bind("<MouseWheel>",
                lambda e: cv.yview_scroll(int(-1*(e.delta/120)), "units"))

        def section(title):
            tk.Label(inner, text=title,
                     bg=WHT, fg=MAR,
                     font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(fill="x", pady=(10, 2))
            tk.Frame(inner, bg=GLD, height=2).pack(fill="x", pady=(0, 6))

        def item(text, fg="#333"):
            tk.Label(inner, text=text,
                     bg=WHT, fg=fg,
                     font=("Segoe UI", 9),
                     anchor="w", justify="left").pack(fill="x", pady=1, padx=8)

        def formula_row(label, eq):
            """Fixed two-column formula row — no misalignment."""
            row = tk.Frame(inner, bg=WHT)
            row.pack(fill="x", padx=8, pady=1)
            tk.Label(row, text=label, bg=WHT, fg="#555",
                     font=("Courier New", 9),
                     width=20, anchor="w").pack(side="left")
            tk.Label(row, text=eq, bg=WHT, fg=MAR,
                     font=("Courier New", 9),
                     anchor="w").pack(side="left")

        # Header
        tk.Label(inner,
                 text=f"{PUBLISHER.upper()}",
                 bg=WHT, fg=MAR,
                 font=("Segoe UI", 11, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 2))
        tk.Label(inner,
                 text=f"Payroll Management System  v{APP_VER}",
                 bg=WHT, fg="#888",
                 font=("Segoe UI", 9),
                 anchor="w").pack(fill="x")
        tk.Frame(inner, bg="#E0D8CC", height=1).pack(fill="x", pady=(8, 0))

        section("📋  System Features")
        for feat in [
            "Employee Management with complete profile",
            "Payroll: Weekly, Semi-Monthly, Monthly cutoffs",
            "Accurate computation using BVBC formula",
            "Deductions: SSS, WISP, Loans, PhilHealth, Pag-IBIG,",
            "            HDMF, Alumni Fee, COOP Loan, Uniform, Canteen",
            "Savings:    COOP Savings, Insurance, Travel Fund, Sacrificial",
            "Professional Excel Payslip Export",
            "Reports and Analytics Dashboard",
        ]:
            item(f"  •  {feat}")

        section("🧮  Payroll Formula")
        formula_row("Gross Salary    =", "Monthly Salary  −  Rent")
        formula_row("Daily Rate      =", "Gross Salary  ×  12  ÷  260")
        formula_row("Honorarium      =", "Daily Rate  ×  Days Worked")
        formula_row("Total Deductions=", "SSS + WISP + Loans + PhilHealth")
        formula_row("                 ", "+ Pag-IBIG + HDMF + Alumni + COOP")
        formula_row("                 ", "+ Uniform + Canteen + Others")
        formula_row("NET PAY         =", "Honorarium  −  Total Deductions")

        section("💻  Requirements")
        item("  •  Windows 7 / 8 / 10 / 11  (64-bit recommended)")
        item("  •  Python 3.8 or newer  (auto-installed if missing)")
        item("  •  50 MB free disk space")
        item("  •  Internet connection  (first install only)")

        section("🔑  Default Login")
        row = tk.Frame(inner, bg="#FFF8EE",
                       highlightbackground=GLD, highlightthickness=1)
        row.pack(fill="x", padx=8, pady=4)
        tk.Label(row, text="  Username : admin        Password : admin123",
                 bg="#FFF8EE", fg=MAR,
                 font=("Courier New", 10, "bold")).pack(pady=8)
        item("  Change password in Settings after first login.", fg="#888")

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 2 — CHOOSE DIRECTORY
    # ═════════════════════════════════════════════════════════════════════════
    def _page_directory(self):
        self._pg_hdr("Choose Install Location",
                     "Where should the system be installed?")

        # Directory row
        lf = tk.Frame(self.body, bg=BG)
        lf.pack(fill="x", padx=28, pady=(0, 6))
        tk.Label(lf, text="Install to:",
                 bg=BG, fg="#444",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        er = tk.Frame(lf, bg=BG); er.pack(fill="x")
        ent = tk.Entry(er, textvariable=self.install_dir,
                       font=("Segoe UI", 10), width=44,
                       bd=0, highlightthickness=1,
                       highlightbackground="#C8C0B0",
                       highlightcolor=GLD, bg=WHT)
        ent.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 6))
        def _browse():
            d = filedialog.askdirectory(title="Choose install folder")
            if d:
                self.install_dir.set(os.path.normpath(d))
        tk.Button(er, text=" Browse... ",
                  font=("Segoe UI", 10), relief="flat",
                  bg="#C8C0B0", fg="#333",
                  activebackground="#B8B0A0",
                  cursor="hand2",
                  command=_browse).pack(side="left")

        # Divider
        tk.Frame(self.body, bg="#D0C8B8", height=1).pack(fill="x", padx=28, pady=12)

        # Options
        tk.Label(self.body, text="Additional options:",
                 bg=BG, fg="#444",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=28, pady=(0, 8))

        for text, var in [
            ("Create a Desktop shortcut  (recommended)",  self.want_desktop),
            ("Create a Start Menu entry  (recommended)",  self.want_startmenu),
        ]:
            f = tk.Frame(self.body, bg=BG); f.pack(anchor="w", padx=38, pady=3)
            tk.Checkbutton(f, text=text, variable=var,
                           font=("Segoe UI", 10),
                           bg=BG, fg="#333",
                           activebackground=BG,
                           selectcolor=WHT,
                           cursor="hand2").pack(side="left")

        # Space info
        tk.Frame(self.body, bg="#D0C8B8", height=1).pack(fill="x", padx=28, pady=(12, 6))
        tk.Label(self.body, text="  Space required: approximately 10 MB",
                 bg=BG, fg="#888",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=28)

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 3 — CONFIRM
    # ═════════════════════════════════════════════════════════════════════════
    def _page_confirm(self):
        self._pg_hdr("Ready to Install",
                     "Review your choices, then click Install to begin.")

        card = tk.Frame(self.body, bg=WHT,
                        highlightbackground="#C8C0B0", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 8))

        items = [
            ("Application",     APP_NAME),
            ("Version",         APP_VER),
            ("Publisher",       PUBLISHER),
            ("Install location",self.install_dir.get()),
            ("Desktop shortcut","Yes ✔" if self.want_desktop.get()   else "No"),
            ("Start Menu entry","Yes ✔" if self.want_startmenu.get() else "No"),
        ]
        for i, (lbl, val) in enumerate(items):
            bg = "#F5F0E8" if i % 2 == 0 else WHT
            row = tk.Frame(card, bg=bg); row.pack(fill="x")
            tk.Label(row, text=f"  {lbl}",
                     bg=bg, fg="#666",
                     font=("Segoe UI", 9, "bold"),
                     width=20, anchor="w").pack(side="left", pady=9, padx=(8, 0))
            tk.Label(row, text=val,
                     bg=bg, fg=MAR,
                     font=("Segoe UI", 9),
                     anchor="w").pack(side="left", padx=6)

        tk.Frame(card, bg=GLD, height=2).pack(fill="x", pady=(8, 0))
        tk.Label(card,
                 text="  Click Install to proceed. This may take a minute.",
                 bg=WHT, fg="#555",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=8, padx=8)

        # Change Next button to Install
        self.btn_next.config(text="  Install  ", bg="#1A5C1A",
                              activebackground="#0A3C0A")

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 4 — INSTALLING
    # ═════════════════════════════════════════════════════════════════════════
    def _page_installing(self):
        self.btn_back.config(state="disabled")
        self.btn_next.config(state="disabled", text="Installing…")
        self.btn_cancel.config(state="disabled")

        self._pg_hdr("Installing…", "Please wait while the system is installed.")

        self.status_var = tk.StringVar(value="Preparing…")
        tk.Label(self.body, textvariable=self.status_var,
                 bg=BG, fg=MAR,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", padx=28, pady=(0, 6))

        self.prog = ttk.Progressbar(self.body, mode="determinate",
                                     maximum=100, length=520)
        self.prog.pack(padx=28, pady=(0, 8))

        self.detail_var = tk.StringVar(value="")
        tk.Label(self.body, textvariable=self.detail_var,
                 bg=BG, fg="#666",
                 font=("Segoe UI", 8),
                 anchor="w").pack(fill="x", padx=28)

        # Log
        log_f = tk.Frame(self.body, bg="#111",
                         highlightbackground="#555", highlightthickness=1)
        log_f.pack(fill="both", expand=True, padx=28, pady=(10, 6))
        self.log_txt = tk.Text(log_f,
                               font=("Consolas", 8),
                               bg="#111", fg="#00DD44",
                               relief="flat", bd=0,
                               state="normal",
                               padx=10, pady=8)
        log_vsb = ttk.Scrollbar(log_f, orient="vertical",
                                 command=self.log_txt.yview)
        self.log_txt.configure(yscrollcommand=log_vsb.set)
        log_vsb.pack(side="right", fill="y")
        self.log_txt.pack(fill="both", expand=True)

        threading.Thread(target=self._run_install, daemon=True).start()

    def _log(self, msg):
        """Thread-safe log update via after()."""
        def _do():
            try:
                self.log_txt.insert("end", f"  {msg}\n")
                self.log_txt.see("end")
            except Exception:
                pass
        self.after(0, _do)

    def _status(self, msg, pct=None):
        """Thread-safe status/progress update via after()."""
        def _do():
            try:
                self.status_var.set(msg)
                if pct is not None:
                    self.prog["value"] = pct
            except Exception:
                pass
        self.after(0, _do)

    def _run_install(self):
        dest = self.install_dir.get()
        try:
            # 1. Directories
            self._status("Creating directories…", 5)
            for d in [dest,
                      os.path.join(dest, "assets"),
                      os.path.join(dest, "reports")]:
                os.makedirs(d, exist_ok=True)
            self._log(f"Created: {dest}")

            # 2. Install Python packages
            self._status("Installing packages (openpyxl, pillow)…", 12)
            self._log("Installing required Python packages…")
            for pkg in ["openpyxl", "pillow"]:
                pkg_name = pkg
                self.after(0, lambda p=pkg_name: self.detail_var.set(f"pip install {p}..."))
                r = subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg,
                     "--quiet", "--no-warn-script-location"],
                    capture_output=True, text=True)
                status = "OK" if r.returncode == 0 else "WARNING (not critical)"
                self._log(f"  {pkg}: {status}")

            # 3. Copy Python files
            self._status("Copying system files…", 28)
            py_files = [
                "main.py","run.pyw","BVBC_Payroll.vbs",
                "database.py","computation.py","reports_export.py","ui.py",
                "gui_dashboard.py","gui_employees.py","gui_payroll.py",
                "gui_payslip.py","gui_reports.py","gui_settings.py",
            ]
            total = len(py_files)
            for i, fname in enumerate(py_files):
                src = os.path.join(SCRIPT_DIR, fname)
                if os.path.exists(src):
                    shutil.copy2(src, dest)
                pct = 28 + int(i / total * 32)
                fname_cap = fname
                def _upd(f=fname_cap, p=pct):
                    try:
                        self.detail_var.set(f"Copying {f}...")
                        self.prog["value"] = p
                    except Exception:
                        pass
                self.after(0, _upd)
                self._log(f"  Copied: {fname}")

            # 4. Copy assets
            self._status("Copying assets…", 62)
            adir = os.path.join(SCRIPT_DIR, "assets")
            if os.path.exists(adir):
                for fname in os.listdir(adir):
                    shutil.copy2(os.path.join(adir, fname),
                                 os.path.join(dest, "assets", fname))
                    self._log(f"  Copied: assets/{fname}")

            # 5. Find Python executable
            self._status("Locating Python...", 68)
            pythonw = _find_pythonw()
            python3 = _find_python3()
            self._log(f"  Python  : {python3}")
            self._log(f"  Pythonw : {pythonw}")

            # 6. Write launchers
            self._status("Creating launchers...", 72)
            ico = os.path.join(dest, "assets", "bvbc.ico")

            # 6. Write launchers
            #    Strategy: try multiple Python commands so it works
            #    regardless of how Python was installed on this PC.
            bat = os.path.join(dest, "BVBC_Payroll_Launch.bat")
            run_pyw = os.path.join(dest, "run.pyw")

            # Build the bat content:
            # - cd /d first (critical — sets working dir for imports)
            # - try: hardcoded pythonw path found during install
            # - fallback 1: "py" launcher (Windows Python Launcher)
            # - fallback 2: "python" from PATH
            bat_lines = [
                "@echo off",
                f'cd /d "{dest}"',
                "",
                ":: Try pythonw.exe with full path (no console window)",
                f'"{pythonw}" "{run_pyw}"',
                "if %errorlevel% equ 0 goto :done",
                "",
                ":: Try Windows py launcher",
                f'py "{run_pyw}"',
                "if %errorlevel% equ 0 goto :done",
                "",
                ":: Try python from PATH",
                f'python "{run_pyw}"',
                "if %errorlevel% equ 0 goto :done",
                "",
                ":: All failed — show error",
                "echo.",
                "echo ERROR: Python not found.",
                "echo Please install Python from https://www.python.org/",
                "echo Then run this file again.",
                "echo.",
                "pause",
                ":done",
            ]
            with open(bat, "w", encoding="utf-8") as bf:
                bf.write("\r\n".join(bat_lines) + "\r\n")
            self._log(f"  Launcher bat: {bat}")

            # VBS launcher — calls pythonw directly, window=0 = fully hidden
            # pythonw.exe itself has no console; this VBS also hides any flash
            vbs = os.path.join(dest, "BVBC_Payroll.vbs")
            with open(vbs, "w", encoding="utf-8") as vf:
                vf.write('On Error Resume Next\r\n')
                vf.write('Dim sh\r\n')
                vf.write('Set sh = CreateObject("WScript.Shell")\r\n')
                # First try pythonw (no console) — window style 0 = hidden
                vf.write(f'sh.Run Chr(34) & "{pythonw}" & Chr(34) & " " & Chr(34) & "{run_pyw}" & Chr(34), 0, False\r\n')
                vf.write('If Err.Number <> 0 Then\r\n')
                vf.write('  Err.Clear\r\n')
                # Fallback: py launcher
                vf.write(f'  sh.Run "py " & Chr(34) & "{run_pyw}" & Chr(34), 0, False\r\n')
                vf.write('End If\r\n')
                vf.write('Set sh = Nothing\r\n')
            self._log(f"  VBS launcher: {vbs}")

            # 7. Desktop shortcut → points to .bat file directly
            if self.want_desktop.get():
                self._status("Creating Desktop shortcut...", 80)
                desktop = os.path.join(
                    os.environ.get("USERPROFILE", os.path.expanduser("~")),
                    "Desktop")
                lnk = os.path.join(desktop, "BVBC Payroll.lnk")

                # Use PowerShell to create shortcut — bat target, ico icon
                ps = (
                    f'$ws=New-Object -ComObject WScript.Shell;' +
                    f'$s=$ws.CreateShortcut(\'{lnk}\');' +
                    f'$s.TargetPath=\'{vbs}\';' +
                    f'$s.WorkingDirectory=\'{dest}\';' +
                    (f'$s.IconLocation=\'{ico}\';'
                     if os.path.exists(ico) else '') +
                    f'$s.Description=\'BVBC Payroll Management System\';' +
                    f'$s.Save()'
                )
                r = subprocess.run(
                    ["powershell","-NoProfile",
                     "-ExecutionPolicy","Bypass",
                     "-Command", ps],
                    capture_output=True, text=True, timeout=20)

                # Verify the .lnk was actually created
                if os.path.exists(lnk):
                    self._log("  Desktop shortcut: OK")
                else:
                    # Hard fallback: write VBScript and run via wscript
                    self._log("  PowerShell shortcut failed, trying VBScript...")
                    sc_vbs = os.path.join(
                        os.environ.get("TEMP", dest), "_make_sc.vbs")
                    with open(sc_vbs, "w") as sv:
                        sv.write(f'Set ws=CreateObject("WScript.Shell")\r\n')
                        sv.write(f'Set s=ws.CreateShortcut("{lnk}")\r\n')
                        sv.write(f's.TargetPath="{vbs}"\r\n')
                        sv.write(f's.WorkingDirectory="{dest}"\r\n')
                        if os.path.exists(ico):
                            sv.write(f's.IconLocation="{ico}"\r\n')
                        sv.write(f's.Description="BVBC Payroll"\r\n')
                        sv.write('s.Save\r\n')
                    subprocess.run(
                        ["wscript", "//nologo", sc_vbs],
                        capture_output=True, timeout=15)
                    try: os.remove(sc_vbs)
                    except: pass
                    if os.path.exists(lnk):
                        self._log("  Desktop shortcut: OK (VBScript)")
                    else:
                        self._log("  Desktop shortcut: FAILED (check Admin rights)")

            # 8. Start Menu shortcut
            if self.want_startmenu.get():
                self._status("Creating Start Menu entry...", 87)
                sm = os.path.join(
                    os.environ.get("APPDATA", ""),
                    r"Microsoft\Windows\Start Menu\Programs\BVBC Payroll")
                os.makedirs(sm, exist_ok=True)
                sm_lnk = os.path.join(sm, "BVBC Payroll.lnk")
                ps2 = (
                    f'$ws=New-Object -ComObject WScript.Shell;' +
                    f'$s=$ws.CreateShortcut(\'{sm_lnk}\');' +
                    f'$s.TargetPath=\'{vbs}\';' +
                    f'$s.WorkingDirectory=\'{dest}\';' +
                    (f'$s.IconLocation=\'{ico}\';'
                     if os.path.exists(ico) else '') +
                    f'$s.Description=\'BVBC Payroll Management System\';' +
                    f'$s.Save()'
                )
                subprocess.run(
                    ["powershell","-NoProfile",
                     "-ExecutionPolicy","Bypass",
                     "-Command", ps2],
                    capture_output=True, timeout=20)
                self._log(f"  Start Menu: {'OK' if os.path.exists(sm_lnk) else 'FAILED'}")

            # 8. Registry
            self._status("Registering application…", 90)
            try:
                import winreg
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, INSTALL_KEY)
                for name, val in [
                    ("DisplayName",     APP_NAME),
                    ("DisplayVersion",  APP_VER),
                    ("Publisher",       PUBLISHER),
                    ("InstallLocation", dest),
                    ("DisplayIcon",     ico),
                    ("UninstallString", os.path.join(dest, "Uninstall.bat")),
                ]:
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, val)
                winreg.CloseKey(key)
                self._log("  Registered in Add/Remove Programs OK")
            except Exception as ex:
                self._log(f"  Registry skipped: {ex}")

            # 9. Uninstaller
            self._status("Writing uninstaller…", 95)
            desktop_lnk = os.path.join(
                os.environ.get("USERPROFILE", ""), "Desktop", "BVBC Payroll.lnk")
            sm_dir = os.path.join(
                os.environ.get("APPDATA", ""),
                r"Microsoft\Windows\Start Menu\Programs\BVBC Payroll")
            uninst = os.path.join(dest, "Uninstall.bat")
            with open(uninst, "w") as f:
                f.write("@echo off\n")
                f.write(f'title Uninstall {APP_NAME}\n')
                f.write(f'set /p SURE=Uninstall {APP_NAME}? (Y/N): \n')
                f.write('if /i not "%SURE%"=="Y" exit /b\n')
                f.write(f'rmdir /S /Q "{dest}"\n')
                f.write(f'del /F /Q "{desktop_lnk}" >nul 2>&1\n')
                f.write(f'rmdir /S /Q "{sm_dir}" >nul 2>&1\n')
                f.write(f'reg delete "HKCU\\{INSTALL_KEY}" /f >nul 2>&1\n')
                f.write('echo Done. echo.\npause\n')
            self._log("  Uninstaller created OK")

            # Done
            self._status("Installation complete!", 100)
            self.after(0, lambda: self.detail_var.set(""))
            self._log("")
            self._log("━" * 44)
            self._log(f"  {APP_NAME} v{APP_VER}")
            self._log("  Installation successful!")
            self._log(f"  Location: {dest}")
            self._log("━" * 44)

            self.after(900, self._show_done)

        except Exception as ex:
            self._log(f"\n[ERROR] {ex}")
            self._status(f"Error: {ex}")
            def _show_err(e=ex):
                messagebox.showerror(
                    "Installation Failed",
                    f"Error:\n{e}\n\nTry running Setup.vbs as Administrator.",
                    parent=self)
                self.btn_cancel.config(state="normal")
            self.after(0, _show_err)

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 5 — DONE
    # ═════════════════════════════════════════════════════════════════════════
    def _show_done(self):
        self.page_idx = 5
        self._clear()
        self._update_steps()
        self.btn_back.config(state="disabled")
        self.btn_next.config(text="  Finish  ", state="normal",
                              bg=MAR, activebackground="#700E0E")
        self.btn_cancel.config(state="disabled")

        # Success banner
        banner = tk.Frame(self.body, bg="#1A5C1A", height=52)
        banner.pack(fill="x"); banner.pack_propagate(False)
        tk.Label(banner,
                 text="  [OK]   Installation Complete!",
                 bg="#1A5C1A", fg=WHT,
                 font=("Segoe UI", 13, "bold")).place(x=14, rely=0.5, anchor="w")
        tk.Frame(self.body, bg=GLD, height=2).pack(fill="x")

        card = tk.Frame(self.body, bg=WHT,
                        highlightbackground="#C8C0B0", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(12, 8))

        tk.Label(card,
                 text=f"  {APP_NAME}  v{APP_VER}  has been installed successfully.",
                 bg=WHT, fg=MAR,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", padx=12, pady=(16, 4))

        tk.Label(card,
                 text=f"  Installed to:  {self.install_dir.get()}",
                 bg=WHT, fg="#555",
                 font=("Segoe UI", 9),
                 anchor="w").pack(fill="x", padx=12)

        tk.Frame(card, bg="#E0D8CC", height=1).pack(fill="x", padx=12, pady=10)

        info = (
            "  You can now launch the system:\n\n"
            "    •  Double-click  \"BVBC Payroll\"  on your Desktop\n"
            "    •  Start Menu → BVBC Payroll\n\n"
            "  Default login:   admin  /  admin123\n"
            "  (Change your password in Settings after first login)"
        )
        tk.Label(card, text=info,
                 bg=WHT, fg="#333",
                 font=("Segoe UI", 9),
                 justify="left", anchor="w").pack(fill="x", padx=12)

        tk.Frame(card, bg="#E0D8CC", height=1).pack(fill="x", padx=12, pady=10)

        tk.Checkbutton(card,
                       text="  Launch BVBC Payroll System now",
                       variable=self.launch_now,
                       font=("Segoe UI", 10, "bold"),
                       bg=WHT, fg=MAR,
                       activebackground=WHT,
                       selectcolor=WHT,
                       cursor="hand2").pack(anchor="w", padx=12, pady=(0, 16))

    # ═════════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═════════════════════════════════════════════════════════════════════════
    def show_page(self, idx):
        self.page_idx = idx
        self._clear()
        self._update_steps()

        # Reset button states
        self.btn_back.config(state="disabled" if idx == 0 else "normal")
        self.btn_next.config(state="normal", bg=MAR,
                              activebackground="#700E0E")
        self.btn_cancel.config(state="normal")

        pages = {
            0: (self._page_welcome,   "Next  ›"),
            1: (self._page_info,      "Continue  ›"),
            2: (self._page_directory, "Next  ›"),
            3: (self._page_confirm,   "  Install  "),
        }
        if idx in pages:
            fn, btn_txt = pages[idx]
            fn()
            self.btn_next.config(text=btn_txt)
            if idx == 3:
                self.btn_next.config(bg="#1A5C1A", activebackground="#0A3C0A")

    def _on_next(self):
        if   self.page_idx < 3: self.show_page(self.page_idx + 1)
        elif self.page_idx == 3:
            self.page_idx = 4
            self._clear()
            self._update_steps()
            self._page_installing()
        elif self.page_idx == 5:
            if self.launch_now.get():
                vbs = os.path.join(self.install_dir.get(), "BVBC_Payroll.vbs")
                if os.path.exists(vbs):
                    subprocess.Popen(["wscript", vbs])
            self.destroy()

    def _on_back(self):
        if 1 <= self.page_idx <= 3:
            self.show_page(self.page_idx - 1)

    def _on_cancel(self):
        if self.page_idx == 4:
            return  # Can't cancel during install
        if messagebox.askyesno("Cancel Setup",
                "Cancel the installation?", parent=self):
            self.destroy()


if __name__ == "__main__":
    request_admin()
    app = Installer()
    app.mainloop()
