"""BVBC Payroll – Dashboard Page"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from database import get_all_employees, get_payroll_records
from ui import C, F, MONTHS, page_header, section_header, card, button, treeview, stat_card


class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self._build()

    def _build(self):
        now   = datetime.now()
        uname = (self.app.current_user.get("full_name") or
                 self.app.current_user["username"])
        page_header(self, "🏠  Dashboard", f"Welcome, {uname}")

        scroll_canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0)
        scroll_canvas.pack(fill="both", expand=True)
        body = tk.Frame(scroll_canvas, bg=C["bg"])
        scroll_canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox("all")))

        pad = tk.Frame(body, bg=C["bg"])
        pad.pack(fill="both", expand=True, padx=24, pady=18)

        # ── Data ──────────────────────────────────────────────────────
        emps     = get_all_employees()
        inactive = get_all_employees(status_filter="Inactive")
        payroll  = get_payroll_records(month=now.month, year=now.year)
        net_tot  = sum(r["net_pay"] for r in payroll)
        gross_tot= sum(r["gross_pay"] for r in payroll)

        # ── Stat cards ────────────────────────────────────────────────
        sr = tk.Frame(pad, bg=C["bg"])
        sr.pack(fill="x", pady=(0, 20))
        stats = [
            ("👥", "Active Employees",    len(emps),              C["m600"]),
            ("💰", f"Total Net Pay",      f"₱{net_tot:,.2f}",     C["g600"]),
            ("📋", f"Records – {MONTHS[now.month]}", len(payroll), C["inf"]),
            ("❌", "Inactive Staff",      len(inactive),          C["m500"]),
        ]
        for icon, lbl, val, color in stats:
            sc = stat_card(sr, icon, lbl, val, color)
            sc.pack(side="left", fill="both", expand=True, padx=(0, 14))

        # ── Middle row ────────────────────────────────────────────────
        mid = tk.Frame(pad, bg=C["bg"])
        mid.pack(fill="both", expand=True)

        # Quick actions
        qa_o, qa = card(mid, padx=22, pady=20)
        qa_o.pack(side="left", fill="y", padx=(0, 16))
        section_header(qa, "⚡  Quick Actions", bg=C["card"]).pack(fill="x")

        def quick_btn(text, icon, style, cmd):
            b = button(qa, text, style=style, command=cmd,
                       icon=icon, px=16, py=11, font_key="btn", anchor="w")
            b.pack(fill="x", pady=4)

        quick_btn("Add Employee",      "➕", "primary", lambda: self.app.goto("employees"))
        quick_btn("Process Payroll",   "💰", "gold",    lambda: self.app.goto("payroll"))
        quick_btn("Generate Payslip",  "📄", "info",    lambda: self.app.goto("payslip"))
        quick_btn("View Reports",      "📊", "success", lambda: self.app.goto("reports"))
        quick_btn("Settings & Backup", "⚙️",  "dark",   lambda: self.app.goto("settings"))

        # Payroll summary card
        rp_o, rp = card(mid, padx=22, pady=20)
        rp_o.pack(side="left", fill="both", expand=True)
        section_header(rp,
            f"📋  Payroll Summary – {MONTHS[now.month]} {now.year}",
            bg=C["card"]).pack(fill="x")

        cols   = ("id", "name", "dept", "gross", "ded", "net")
        hdrs   = ["Emp ID","Name","Department","Gross Pay","Deductions","Net Pay"]
        widths = [85, 165, 120, 105, 105, 105]
        anchors= {"id":"center","name":"w","dept":"w",
                  "gross":"right","ded":"right","net":"right"}
        tf, tv = treeview(rp, cols, hdrs, widths, height=9,
                           anchors=anchors, stretch_col="name")
        tf.pack(fill="both", expand=True)
        for i, rec in enumerate(payroll):
            tag = "even" if i % 2 == 0 else "odd"
            tv.insert("", "end", tag=tag, values=(
                rec["employee_id"],
                f"{rec['last_name']}, {rec['first_name']}",
                rec["department"] or "",
                f"₱{rec['gross_pay']:,.2f}",
                f"₱{rec['total_deductions']:,.2f}",
                f"₱{rec['net_pay']:,.2f}"))

        # Totals footer
        if payroll:
            tot_f = tk.Frame(rp, bg=C["g100"],
                             highlightbackground=C["border"], highlightthickness=1)
            tot_f.pack(fill="x", pady=(8, 0))
            items = [
                ("Total Gross:", f"₱{gross_tot:,.2f}"),
                ("Total Net Pay:", f"₱{net_tot:,.2f}"),
                ("Employees:", str(len(payroll))),
            ]
            for lbl, val in items:
                col_f = tk.Frame(tot_f, bg=C["g100"])
                col_f.pack(side="left", expand=True, fill="x", padx=10, pady=6)
                tk.Label(col_f, text=lbl, bg=C["g100"],
                         fg=C["t600"], font=F["small"]).pack(anchor="w")
                tk.Label(col_f, text=val, bg=C["g100"],
                         fg=C["m700"], font=F["h3"]).pack(anchor="w")

        # Timestamp footer
        tk.Label(pad, text=f"  📅  {now.strftime('%A, %B %d, %Y  ·  %I:%M %p')}",
                 bg=C["bg"], fg=C["t400"],
                 font=F["small"]).pack(anchor="e", pady=(16, 0))
