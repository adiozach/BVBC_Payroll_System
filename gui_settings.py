"""BVBC Payroll – Settings Page"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, hashlib
from database import get_connection, backup_database, restore_database
from ui import C, F, page_header, section_header, card, button

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")


class SettingsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._build()

    def _build(self):
        page_header(self, "⚙️  Settings", "Password, deduction rates, backup & restore")

        # Scrollable body
        cv  = tk.Canvas(self, bg=C["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); cv.pack(fill="both", expand=True)
        body = tk.Frame(cv, bg=C["bg"], padx=26, pady=18)
        win  = cv.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win, width=e.width))

        # Two-column layout
        left  = tk.Frame(body, bg=C["bg"])
        right = tk.Frame(body, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        right.pack(side="left", fill="both", expand=True)

        # ── Change Password ──────────────────────────────────────────
        section_header(left, "🔒  Change Password", bg=C["bg"]).pack(fill="x")
        pw_o, pw = card(left, padx=22, pady=20)
        pw_o.pack(fill="x", pady=(0, 20))

        def pw_field(parent, label):
            tk.Label(parent, text=label, bg=C["card"],
                     fg=C["t600"], font=F["label"]).pack(anchor="w")
            var = tk.StringVar()
            e = tk.Entry(parent, textvariable=var, show="●",
                         font=F["body"], width=32, bd=0,
                         highlightthickness=1,
                         highlightbackground=C["border"],
                         highlightcolor=C["g500"], bg=C["g100"])
            e.pack(fill="x", pady=(4, 14), ipady=6)
            return var

        self._cur  = pw_field(pw, "Current Password")
        self._new  = pw_field(pw, "New Password")
        self._conf = pw_field(pw, "Confirm New Password")
        button(pw, "Update Password", "primary",
               self._change_pw, icon="🔑", px=16, py=8).pack(anchor="w")

        # ── Deduction Rates ──────────────────────────────────────────
        section_header(left, "📋  Deduction Rates (Reference)", bg=C["bg"]).pack(fill="x")
        dr_o, dr = card(left, padx=22, pady=20)
        dr_o.pack(fill="x", pady=(0, 20))

        conn  = get_connection()
        rates = conn.execute("SELECT * FROM deduction_rates").fetchall()
        conn.close()

        self._rate_vars = {}
        for i, r in enumerate(rates):
            rf = tk.Frame(dr, bg=C["card"])
            rf.pack(fill="x", pady=5)
            # Color tag
            tag_bg = C["m600"] if i == 0 else (C["g600"] if i == 1 else C["inf"])
            tk.Frame(rf, bg=tag_bg, width=4).pack(side="left", fill="y", padx=(0, 10))
            tk.Label(rf, text=r["name"], bg=C["card"],
                     fg=C["t600"], font=F["label"], width=26,
                     anchor="w").pack(side="left")
            var = tk.StringVar(value=str(r["rate"]))
            e = tk.Entry(rf, textvariable=var, width=10, font=F["body"],
                         bd=0, highlightthickness=1,
                         highlightbackground=C["border"],
                         highlightcolor=C["g500"], bg=C["g100"])
            e.pack(side="left", padx=8, ipady=4)
            pct = " %" if r["is_percent"] else " ₱"
            tk.Label(rf, text=pct, bg=C["card"],
                     fg=C["t400"], font=F["body"]).pack(side="left")
            self._rate_vars[r["id"]] = var

        button(dr, "Save Rates", "gold", self._save_rates,
               icon="💾", px=16, py=8).pack(anchor="w", pady=(10, 0))

        # ── Backup & Restore ─────────────────────────────────────────
        section_header(right, "💾  Database Backup & Restore", bg=C["bg"]).pack(fill="x")
        bk_o, bk = card(right, padx=22, pady=22)
        bk_o.pack(fill="x", pady=(0, 20))

        tk.Label(bk, text="Always backup before making bulk changes.",
                 bg=C["card"], fg=C["t400"], font=F["small"]).pack(anchor="w", pady=(0, 14))

        button(bk, "Create Backup Now", "success",
               self._backup, icon="📦", px=16, py=10).pack(fill="x", pady=4)
        button(bk, "Restore from Backup", "danger",
               self._restore, icon="🔁", px=16, py=10).pack(fill="x", pady=4)

        self._bk_status = tk.Label(bk, text="", bg=C["card"],
                                    fg=C["ok"], font=F["small"])
        self._bk_status.pack(anchor="w", pady=(8, 0))

        # ── About ────────────────────────────────────────────────────
        section_header(right, "ℹ️  About This System", bg=C["bg"]).pack(fill="x", pady=(8, 0))
        ab_o, ab = card(right, padx=22, pady=22)
        ab_o.pack(fill="x")

        about_info = [
            ("System",      "BVBC Payroll Management System v2.0"),
            ("Institution", "Baptist Voice Bible College"),
            ("Region",      "Philippines"),
            ("Deductions",  "SSS · PhilHealth · Pag-IBIG (2023 schedule)"),
            ("Database",    "SQLite (offline, no internet required)"),
            ("Language",    "Python 3 + Tkinter"),
            ("Reports",     "Excel export via openpyxl"),
        ]
        for lbl_text, val_text in about_info:
            row = tk.Frame(ab, bg=C["card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{lbl_text}:", bg=C["card"],
                     fg=C["t600"], font=F["label"], width=14,
                     anchor="w").pack(side="left")
            tk.Label(row, text=val_text, bg=C["card"],
                     fg=C["t900"], font=F["body"],
                     anchor="w").pack(side="left")

        # Gold footer bar
        tk.Frame(ab, bg=C["g500"], height=3).pack(fill="x", pady=(16, 0))
        tk.Label(ab, text="© 2025 Baptist Voice Bible College  ·  All Rights Reserved",
                 bg=C["card"], fg=C["t400"], font=F["tiny"]).pack(pady=(4, 0))

    def _change_pw(self):
        cur  = self._cur.get()
        new  = self._new.get()
        conf = self._conf.get()
        if not cur or not new:
            messagebox.showerror("Required", "All fields are required.", parent=self); return
        if new != conf:
            messagebox.showerror("Mismatch", "New passwords do not match.", parent=self); return
        if len(new) < 6:
            messagebox.showerror("Too Short",
                "Password must be at least 6 characters.", parent=self); return
        cur_hash = hashlib.sha256(cur.encode()).hexdigest()
        conn = get_connection()
        user = conn.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (self.app.current_user["username"], cur_hash)).fetchone()
        if not user:
            conn.close()
            messagebox.showerror("Wrong Password",
                "Current password is incorrect.", parent=self); return
        new_hash = hashlib.sha256(new.encode()).hexdigest()
        conn.execute("UPDATE users SET password=? WHERE username=?",
                     (new_hash, self.app.current_user["username"]))
        conn.commit(); conn.close()
        self._cur.set(""); self._new.set(""); self._conf.set("")
        messagebox.showinfo("✅  Updated",
            "Password changed successfully.", parent=self)

    def _save_rates(self):
        conn = get_connection()
        for rid, var in self._rate_vars.items():
            try:
                conn.execute("UPDATE deduction_rates SET rate=? WHERE id=?",
                             (float(var.get()), rid))
            except ValueError: pass
        conn.commit(); conn.close()
        messagebox.showinfo("✅  Saved",
            "Deduction rates updated.", parent=self)

    def _backup(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        path = backup_database(BACKUP_DIR)
        fname = os.path.basename(path)
        self._bk_status.config(
            text=f"✅  Backup created: {fname}")
        messagebox.showinfo("✅  Backup Complete",
            f"Database backup saved:\n{path}", parent=self)

    def _restore(self):
        path = filedialog.askopenfilename(
            parent=self, title="Select Backup File",
            initialdir=BACKUP_DIR if os.path.exists(BACKUP_DIR) else ".",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")])
        if not path: return
        if messagebox.askyesno("⚠️  Confirm Restore",
                "This will REPLACE the current database with the backup.\n\n"
                "All current data will be overwritten.\n\nContinue?",
                parent=self):
            restore_database(path)
            messagebox.showinfo("✅  Restored",
                "Database restored.\n\nPlease restart the application.",
                parent=self)
