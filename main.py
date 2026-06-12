"""
Baptist Voice Bible College – Payroll Management System v6.0
Main Application  |  Maroon & Gold UI  |  With Official Logo
No console/CMD window on Windows.
"""
import sys, os, hashlib, tkinter as tk
from tkinter import ttk, messagebox

# ── Hide console window on Windows (works even if launched via python.exe) ──
if sys.platform == "win32":
    try:
        import ctypes
        # SW_HIDE = 0
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

# ── Dependency check ──────────────────────────────────────────────────────
def _dep_check():
    try:
        import openpyxl
    except ImportError:
        root = tk.Tk(); root.withdraw()
        messagebox.showerror(
            "Missing Package — openpyxl",
            "The required package 'openpyxl' is not installed.\n\n"
            "Fix:\n"
            "1. Open Command Prompt (cmd)\n"
            "2. Run:  pip install openpyxl\n"
            "3. Restart this application\n\n"
            "TIP: Use  install_and_run.bat  to auto-install everything.",
            parent=root)
        sys.exit(1)

_dep_check()

from database import initialize_database, get_connection
from ui import C, F, MONTHS, apply_global_styles

# ── Asset paths ───────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
LOGO_LOGIN = os.path.join(BASE_DIR, "assets", "logo_login.png")
LOGO_SIDE  = os.path.join(BASE_DIR, "assets", "logo_sidebar.png")

def _load_photo(path, size=None):
    """Load a PNG as PhotoImage, return None if file missing or PIL absent."""
    try:
        from PIL import Image, ImageTk
        img = Image.open(path).convert("RGBA")
        if size:
            img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        try:
            return tk.PhotoImage(file=path)
        except Exception:
            return None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Baptist Voice Bible College – Payroll Management System")
        self.geometry("1340x820")
        self.minsize(1100, 680)
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.current_user = None
        self._nav_refs    = {}
        self._active_key  = None
        self._logo_login  = None   # keep reference
        self._logo_side   = None
        self._center()
        apply_global_styles(self)
        self._show_login()

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w  = min(1340, sw); h = min(820, sh)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ══════════════════════════════════════════════════════════════════
    # LOGIN
    # ══════════════════════════════════════════════════════════════════
    def _show_login(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=C["m800"])

        # Left branding panel
        left = tk.Frame(self, bg=C["m800"], width=500)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        right = tk.Frame(self, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        # ── Brand panel ──────────────────────────────────────────────
        brand = tk.Frame(left, bg=C["m800"])
        brand.place(relx=0.5, rely=0.44, anchor="center")

        # Official logo (large, transparent bg)
        self._logo_login = _load_photo(LOGO_LOGIN, size=(200, 200))
        if self._logo_login:
            logo_lbl = tk.Label(brand, image=self._logo_login,
                                bg=C["m800"], bd=0)
            logo_lbl.pack(pady=(0, 22))
        else:
            # Fallback badge
            med = tk.Frame(brand, bg=C["g500"], width=110, height=110)
            med.pack(pady=(0, 22)); med.pack_propagate(False)
            tk.Label(med, text="✝", bg=C["g500"], fg=C["m800"],
                     font=("Segoe UI", 52, "bold")).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(brand, text="BAPTIST VOICE",
                 bg=C["m800"], fg=C["g500"],
                 font=("Segoe UI", 26, "bold")).pack()
        tk.Label(brand, text="BIBLE COLLEGE",
                 bg=C["m800"], fg=C["g400"],
                 font=("Segoe UI", 15)).pack()

        tk.Frame(brand, bg=C["g500"], height=2, width=340).pack(pady=20)

        tk.Label(brand, text="PAYROLL MANAGEMENT SYSTEM",
                 bg=C["m800"], fg=C["white"],
                 font=("Segoe UI", 12, "bold")).pack()
        tk.Label(brand, text='"Better To Burn Than Bow"',
                 bg=C["m800"], fg=C["g400"],
                 font=("Segoe UI", 10, "italic")).pack(pady=(6, 0))
        tk.Label(brand, text="Est. 2000  ·  Philippines",
                 bg=C["m800"], fg=C["t400"],
                 font=("Segoe UI", 9)).pack(pady=(4, 0))

        # Footer
        vf = tk.Frame(left, bg=C["m900"])
        vf.pack(side="bottom", fill="x")
        tk.Label(vf, text="v2.0  ·  Philippine Payroll  ·  SSS · PhilHealth · Pag-IBIG",
                 bg=C["m900"], fg=C["t400"],
                 font=("Segoe UI", 8)).pack(pady=8)

        # ── Login card ───────────────────────────────────────────────
        card_wrap = tk.Frame(right, bg=C["bg"])
        card_wrap.place(relx=0.5, rely=0.5, anchor="center")

        border_f = tk.Frame(card_wrap, bg=C["g500"], padx=1, pady=1)
        border_f.pack()
        card = tk.Frame(border_f, bg=C["white"], padx=52, pady=46)
        card.pack()

        tk.Frame(card, bg=C["m600"], height=6).pack(fill="x", pady=(0, 28))

        tk.Label(card, text="Administrator Login",
                 bg=C["white"], fg=C["m700"],
                 font=("Segoe UI", 17, "bold")).pack()
        tk.Label(card, text="Sign in with your credentials to continue",
                 bg=C["white"], fg=C["t400"],
                 font=("Segoe UI", 9)).pack(pady=(3, 28))

        def _efield(label, var, show=None):
            tk.Label(card, text=label, bg=C["white"],
                     fg=C["t600"], font=F["label"], anchor="w").pack(fill="x")
            kw = {"show": show} if show else {}
            e = tk.Entry(card, textvariable=var, font=("Segoe UI", 11),
                         width=30, bd=0, highlightthickness=1,
                         highlightbackground=C["border"],
                         highlightcolor=C["g500"],
                         bg=C["g100"], **kw)
            e.pack(pady=(4, 18), ipady=9, fill="x")
            return e

        self._lu = tk.StringVar(value="admin")
        self._lp = tk.StringVar()
        _efield("Username", self._lu)
        pw_e = _efield("Password", self._lp, show="●")
        pw_e.bind("<Return>", lambda e: self._do_login())

        lb = tk.Button(card, text="   LOGIN  →",
                       bg=C["m600"], fg=C["white"],
                       font=("Segoe UI", 12, "bold"),
                       relief="flat", cursor="hand2",
                       pady=13, command=self._do_login)
        lb.pack(fill="x")
        lb.bind("<Enter>", lambda e: lb.config(bg=C["m500"]))
        lb.bind("<Leave>", lambda e: lb.config(bg=C["m600"]))

        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", pady=18)
        tk.Label(card, text="Default credentials:  admin  /  admin123",
                 bg=C["white"], fg=C["t400"],
                 font=("Segoe UI", 9)).pack()
        pw_e.focus_set()

    def _do_login(self):
        u  = self._lu.get().strip()
        ph = hashlib.sha256(self._lp.get().encode()).hexdigest()
        conn = get_connection()
        row  = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (u, ph)).fetchone()
        conn.close()
        if row:
            self.current_user = dict(row)
            self.configure(bg=C["bg"])
            self._show_main()
        else:
            messagebox.showerror("Login Failed",
                "Incorrect username or password.", parent=self)

    # ══════════════════════════════════════════════════════════════════
    # MAIN SHELL
    # ══════════════════════════════════════════════════════════════════
    def _show_main(self):
        for w in self.winfo_children(): w.destroy()
        self._sb   = tk.Frame(self, bg=C["m800"], width=248)
        self._sb.pack(side="left", fill="y"); self._sb.pack_propagate(False)
        self._main = tk.Frame(self, bg=C["bg"])
        self._main.pack(side="left", fill="both", expand=True)
        self._build_sidebar()
        self.goto("dashboard")

    def _build_sidebar(self):
        sb = self._sb

        # ── Top logo block ────────────────────────────────────────────
        top = tk.Frame(sb, bg=C["m900"])
        top.pack(fill="x")

        # Logo image
        self._logo_side = _load_photo(LOGO_SIDE, size=(72, 72))
        if self._logo_side:
            logo_row = tk.Frame(top, bg=C["m900"], pady=12)
            logo_row.pack(fill="x")
            tk.Label(logo_row, image=self._logo_side,
                     bg=C["m900"], bd=0).pack(side="left", padx=(14, 10))
            txt_f = tk.Frame(logo_row, bg=C["m900"])
            txt_f.pack(side="left")
            tk.Label(txt_f, text="BVBC", bg=C["m900"],
                     fg=C["g500"], font=("Segoe UI", 14, "bold")).pack(anchor="w")
            tk.Label(txt_f, text="Payroll System", bg=C["m900"],
                     fg=C["t400"], font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(txt_f, text="Est. 2000", bg=C["m900"],
                     fg=C["t400"], font=("Segoe UI", 8)).pack(anchor="w")
        else:
            # Fallback text header
            hdr_row = tk.Frame(top, bg=C["m900"], pady=14)
            hdr_row.pack(fill="x", padx=14)
            med = tk.Frame(hdr_row, bg=C["g500"], width=42, height=42)
            med.pack(side="left", padx=(0,10)); med.pack_propagate(False)
            tk.Label(med, text="✝", bg=C["g500"], fg=C["m800"],
                     font=("Segoe UI", 20,"bold")).place(relx=0.5,rely=0.5,anchor="center")
            tk.Label(hdr_row, text="BVBC", bg=C["m900"],
                     fg=C["g500"], font=("Segoe UI",14,"bold")).pack(side="left")

        tk.Frame(sb, bg=C["g500"], height=3).pack(fill="x")

        # User pill
        uf = tk.Frame(sb, bg=C["m800"], pady=10, padx=14)
        uf.pack(fill="x")
        uname = (self.current_user.get("full_name") or
                 self.current_user["username"])[:26]
        tk.Label(uf, text="👤", bg=C["m800"],
                 fg=C["g500"], font=("Segoe UI",12)).pack(side="left", padx=(0,8))
        tk.Label(uf, text=uname, bg=C["m800"],
                 fg=C["white"], font=F["small"]).pack(side="left")

        tk.Frame(sb, bg=C["m600"], height=1).pack(fill="x", padx=14)

        # Nav items
        nav = [
            ("dashboard", "🏠", "Dashboard"),
            ("employees", "👥", "Employees"),
            ("payroll",   "💰", "Payroll Processing"),
            ("payslip",   "📄", "Payslip Generator"),
            ("reports",   "📊", "Reports"),
            ("settings",  "⚙️",  "Settings"),
        ]
        self._nav_refs = {}
        for key, icon, label in nav:
            self._make_nav_btn(sb, key, icon, label)

        # Spacer + logout
        tk.Frame(sb, bg=C["m800"]).pack(expand=True, fill="y")
        tk.Frame(sb, bg=C["m600"], height=1).pack(fill="x", padx=14, pady=4)
        lo = tk.Frame(sb, bg=C["m800"], cursor="hand2", pady=11)
        lo.pack(fill="x", padx=14, pady=(0, 10))
        tk.Label(lo, text="🚪", bg=C["m800"],
                 fg="#EF9A9A", font=("Segoe UI",13)).pack(side="left", padx=(0,10))
        tk.Label(lo, text="Logout", bg=C["m800"],
                 fg="#EF9A9A", font=F["nav"]).pack(side="left")
        for w in (lo, *lo.winfo_children()):
            try: w.bind("<Button-1>", lambda e: self._logout())
            except Exception: pass

    def _make_nav_btn(self, parent, key, icon, label):
        row   = tk.Frame(parent, bg=C["m800"], cursor="hand2")
        row.pack(fill="x")
        ind   = tk.Frame(row, bg=C["m800"], width=5)
        ind.pack(side="left", fill="y")
        inner = tk.Frame(row, bg=C["m800"], pady=12, padx=14)
        inner.pack(side="left", fill="both", expand=True)
        il = tk.Label(inner, text=icon, bg=C["m800"],
                      fg=C["g400"], font=("Segoe UI",14))
        il.pack(side="left", padx=(0,12))
        tl = tk.Label(inner, text=label, bg=C["m800"],
                      fg=C["white"], font=F["nav"])
        tl.pack(side="left")
        self._nav_refs[key] = (row, ind, inner, il, tl)

        def click(e=None, k=key):   self.goto(k)
        def enter(e=None, k=key):
            if k != self._active_key:
                for w in (row, inner, il, tl): w.config(bg=C["m500"])
                ind.config(bg=C["g400"])
        def leave(e=None, k=key):
            if k != self._active_key:
                for w in (row, inner, il, tl): w.config(bg=C["m800"])
                ind.config(bg=C["m800"])

        for w in (row, inner, il, tl):
            w.bind("<Button-1>", click)
            w.bind("<Enter>",    enter)
            w.bind("<Leave>",    leave)

    def _set_active_nav(self, key):
        if self._active_key and self._active_key in self._nav_refs:
            row, ind, inner, il, tl = self._nav_refs[self._active_key]
            for w in (row, inner, il, tl): w.config(bg=C["m800"])
            tl.config(fg=C["white"], font=F["nav"])
            ind.config(bg=C["m800"])
        self._active_key = key
        if key in self._nav_refs:
            row, ind, inner, il, tl = self._nav_refs[key]
            for w in (row, inner, il, tl): w.config(bg=C["m500"])
            tl.config(fg=C["g400"], font=F["nav_a"])
            ind.config(bg=C["g500"])

    def goto(self, page):
        self._set_active_nav(page)
        for w in self._main.winfo_children(): w.destroy()
        pages = {
            "dashboard": ("gui_dashboard",  "DashboardPage"),
            "employees": ("gui_employees",  "EmployeesPage"),
            "payroll":   ("gui_payroll",    "PayrollPage"),
            "payslip":   ("gui_payslip",    "PayslipPage"),
            "reports":   ("gui_reports",    "ReportsPage"),
            "settings":  ("gui_settings",   "SettingsPage"),
        }
        mod_name, cls_name = pages[page]
        import importlib
        mod = importlib.import_module(mod_name)
        getattr(mod, cls_name)(self._main, self)

    def _logout(self):
        self.current_user = None
        self._nav_refs    = {}
        self._active_key  = None
        self._logo_side   = None
        self._show_login()


def main():
    initialize_database()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
