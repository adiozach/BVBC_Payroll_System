"""
BVBC Payroll – Payroll Processing Page
Weekly cutoff support: 1-7 · 8-14 · 15-22 · 23-30
Plus semi-monthly (1-15, 16-31) and monthly (1-31) cutoffs.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database import (get_all_employees, get_payroll_records,
                      save_payroll, get_employee_by_id, get_connection)
from computation import (
    compute_payroll, compute_sss, compute_philhealth, compute_pagibig,
    ALL_CUTOFFS, WEEKLY_CUTOFFS, SEMIMONTHLY_CUTOFFS, MONTHLY_CUTOFFS,
    get_cutoff_days, get_cutoff_divisor, get_cutoff_meta,
)
from ui import C, F, MONTHS, page_header, button

# ── Cutoff display mapping ────────────────────────────────────────────────────
CUTOFF_DISPLAY_MAP = {
    "1-7":   "Week 1:  1 – 7",
    "8-14":  "Week 2:  8 – 14",
    "15-22": "Week 3:  15 – 22",
    "23-30": "Week 4:  23 – 30",
    "1-15":  "1st Half:  1 – 15",
    "16-31": "2nd Half:  16 – 31",
    "1-31":  "Full Month:  1 – 31",
}
DISPLAY_TO_KEY = {v: k for k, v in CUTOFF_DISPLAY_MAP.items()}
CUTOFF_DISPLAY_LIST = [
    "Week 1:  1 – 7",
    "Week 2:  8 – 14",
    "Week 3:  15 – 22",
    "Week 4:  23 – 30",
    "1st Half:  1 – 15",
    "2nd Half:  16 – 31",
    "Full Month:  1 – 31",
]


# ══════════════════════════════════════════════════════════════════════════════
class PayrollPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.pack(fill="both", expand=True)
        self.app       = app
        now            = datetime.now()
        self._month    = tk.IntVar(value=now.month)
        self._year     = tk.StringVar(value=str(now.year))
        self._cut_disp = tk.StringVar(value="Full Month:  1 – 31")
        self._tv       = None
        self._build()

    @property
    def _cut(self):
        return DISPLAY_TO_KEY.get(self._cut_disp.get(), "1-31")

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        page_header(self, "💰  Payroll Processing",
                    "Weekly · Semi-Monthly · Monthly Cutoffs")

        # ── Control bar ───────────────────────────────────────────────
        ctrl = tk.Frame(self, bg=C["white"], padx=14, pady=10,
                        highlightbackground=C["border"], highlightthickness=1)
        ctrl.pack(fill="x")

        def lbl(t):
            tk.Label(ctrl, text=t, bg=C["white"],
                     fg=C["t600"], font=F["label"]).pack(side="left")
        def vsep():
            tk.Frame(ctrl, bg=C["border"], width=1
                     ).pack(side="left", fill="y", padx=10)

        lbl("Month:")
        ttk.Combobox(ctrl, textvariable=self._month,
                     values=list(range(1, 13)), width=5,
                     state="readonly", font=F["body"]
                     ).pack(side="left", padx=(4, 0), ipady=4)
        vsep()
        lbl("Year:")
        ttk.Combobox(ctrl, textvariable=self._year,
                     values=[str(y) for y in range(2020, 2031)],
                     width=7, state="readonly", font=F["body"]
                     ).pack(side="left", padx=(4, 0), ipady=4)
        vsep()
        lbl("Cutoff:")
        self._cut_cb = ttk.Combobox(
            ctrl, textvariable=self._cut_disp,
            values=CUTOFF_DISPLAY_LIST, width=22,
            state="readonly", font=("Segoe UI", 10, "bold"))
        self._cut_cb.pack(side="left", padx=(4, 4), ipady=4)
        self._cut_cb.bind("<<ComboboxSelected>>", lambda e: self._update_badge())

        # Badge showing cutoff type info
        self._badge = tk.Label(ctrl, text="", bg=C["ok"], fg=C["white"],
                                font=("Segoe UI", 8, "bold"), padx=8, pady=2)
        self._badge.pack(side="left", padx=4)
        self._update_badge()
        vsep()

        button(ctrl, "Load",             "ghost",   self._load,        icon="🔄", py=6).pack(side="left", padx=2)
        button(ctrl, "Process All",      "success", self._process_all, icon="⚡", py=6).pack(side="left", padx=2)
        button(ctrl, "Edit Deductions",  "primary", self._quick_edit,  icon="✏️", py=6).pack(side="left", padx=2)
        button(ctrl, "Full Edit / Add",  "gold",    self._edit,        icon="📋", py=6).pack(side="left", padx=2)
        button(ctrl, "Delete",           "danger",  self._delete,      icon="🗑️", py=6).pack(side="left", padx=2)

        # ── Info legend ───────────────────────────────────────────────
        leg = tk.Frame(self, bg=C["m900"], padx=14, pady=5)
        leg.pack(fill="x")
        tk.Label(leg, text="Cutoff Colour Guide:", bg=C["m900"],
                 fg=C["g400"], font=("Segoe UI", 8, "bold")).pack(side="left")
        for txt, bg, fg in [
            ("  Weekly (÷4)  ",       "#C9A84C", "#4A0909"),
            ("  Semi-Monthly (÷2)  ", "#1A4A7A", "#FFFFFF"),
            ("  Monthly (full)  ",    "#2D6A2D", "#FFFFFF"),
        ]:
            tk.Label(leg, text=txt, bg=bg, fg=fg,
                     font=("Segoe UI", 8), padx=4, pady=2
                     ).pack(side="left", padx=5)
        tk.Label(leg,
                 text="💡 Weekly/Semi-monthly deductions = monthly SSS/PhilHealth/Pag-IBIG divided proportionally",
                 bg=C["m900"], fg=C["t400"],
                 font=("Segoe UI", 8)).pack(side="right")

        # ── Filter tabs ───────────────────────────────────────────────
        ftab = tk.Frame(self, bg=C["bg2"], padx=14, pady=5)
        ftab.pack(fill="x")
        tk.Label(ftab, text="View:", bg=C["bg2"],
                 fg=C["t600"], font=F["label"]).pack(side="left")
        for fval, flbl, fbg in [
            ("all",    "All Records",   C["m600"]),
            ("weekly", "Weekly Only",   C["g600"]),
            ("semi",   "Semi-Monthly",  C["inf"]),
            ("monthly","Monthly",       C["ok"]),
        ]:
            b = tk.Button(ftab, text=flbl, bg=fbg, fg=C["white"],
                          font=("Segoe UI", 9, "bold"), relief="flat",
                          cursor="hand2", padx=10, pady=4,
                          command=lambda v=fval: self._load(filter_type=v))
            b.pack(side="left", padx=4)

        # ── Paned window ──────────────────────────────────────────────
        pane = tk.PanedWindow(self, orient="horizontal",
                              bg=C["border"], sashwidth=5)
        pane.pack(fill="both", expand=True, padx=14, pady=8)

        left  = tk.Frame(pane, bg=C["bg"])
        pane.add(left, minsize=520)
        self._build_table(left)

        right = tk.Frame(pane, bg=C["white"])
        pane.add(right, minsize=280)
        self._build_detail(right)

        self._load()

    def _build_table(self, parent):
        # Safe anchor map
        _amap = {"left":"w","right":"e","center":"center",
                 "w":"w","e":"e"}

        style = ttk.Style()
        style.configure("BV.Treeview", font=F["body"], rowheight=27,
                        background=C["white"], fieldbackground=C["white"],
                        foreground=C["t900"], borderwidth=0)
        style.configure("BV.Treeview.Heading", font=F["label"],
                        background=C["m600"], foreground=C["white"],
                        relief="flat", padding=7)
        style.map("BV.Treeview",
                  background=[("selected", C["g300"])],
                  foreground=[("selected", C["m700"])])

        cols   = ("id","cutoff","name","dept","days","gross","ded","net")
        hdrs   = ["Emp ID","Cutoff","Name","Dept","Days",
                  "Gross Pay","Deductions","Net Pay"]
        widths = [82, 112, 155, 96, 46, 100, 100, 100]
        anc    = {"id":"center","cutoff":"center","name":"w","dept":"w",
                  "days":"center","gross":"e","ded":"e","net":"e"}

        tv_frame = tk.Frame(parent, bg=C["bg"])
        tv_frame.pack(fill="both", expand=True)

        self._tv = ttk.Treeview(tv_frame, columns=cols, show="headings",
                                 height=16, style="BV.Treeview")
        for col, h, w in zip(cols, hdrs, widths):
            self._tv.heading(col, text=h)
            self._tv.column(col, width=w,
                            anchor=_amap.get(anc.get(col, "center"), "center"),
                            stretch=(col == "name"))

        # Row colour tags by cutoff type
        self._tv.tag_configure("wk1",  background="#FFF8E7")
        self._tv.tag_configure("wk2",  background="#FFF3D0")
        self._tv.tag_configure("wk3",  background="#FFE9AA")
        self._tv.tag_configure("wk4",  background="#FFE099")
        self._tv.tag_configure("sm1",  background="#E3EEF8")
        self._tv.tag_configure("sm2",  background="#C8DFF2")
        self._tv.tag_configure("mon",  background="#E8F5E8")
        self._tv.tag_configure("mona", background="#D0EDD0")

        vsb = ttk.Scrollbar(tv_frame, orient="vertical",   command=self._tv.yview)
        hsb = ttk.Scrollbar(tv_frame, orient="horizontal",  command=self._tv.xview)
        self._tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tv_frame.grid_rowconfigure(0, weight=1)
        tv_frame.grid_columnconfigure(0, weight=1)

        self._tv.bind("<<TreeviewSelect>>", self._on_sel)
        self._tv.bind("<Double-1>", lambda e: self._quick_edit())

        self._sum_lbl = tk.Label(parent, text="", bg=C["g100"],
                                  fg=C["m700"], font=F["label"],
                                  anchor="w", padx=14, pady=6,
                                  highlightbackground=C["border"],
                                  highlightthickness=1)
        self._sum_lbl.pack(fill="x")

    def _build_detail(self, parent):
        tk.Frame(parent, bg=C["m700"], height=5).pack(fill="x")
        tk.Label(parent, text="📋  Payroll Detail",
                 bg=C["white"], fg=C["m700"],
                 font=F["h2"], padx=16, pady=10).pack(anchor="w")
        tk.Frame(parent, bg=C["g500"], height=2).pack(fill="x", padx=14)
        self._detail = tk.Text(parent, font=("Consolas", 9),
                               bg=C["g100"], fg=C["t900"],
                               relief="flat", state="disabled",
                               wrap="none", padx=14, pady=12)
        vsb = ttk.Scrollbar(parent, orient="vertical",
                            command=self._detail.yview)
        self._detail.configure(yscrollcommand=vsb.set)
        self._detail.pack(side="left", fill="both", expand=True,
                          padx=(14, 0), pady=8)
        vsb.pack(side="right", fill="y", pady=8, padx=(0, 6))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _update_badge(self):
        cut  = self._cut
        meta = get_cutoff_meta(cut)
        ct   = meta["type"]
        info = {
            "weekly":       (f"Weekly · {meta['days']} days · ÷4 deductions",
                             C["g500"], C["m800"]),
            "semi-monthly": (f"Semi-Monthly · {meta['days']} days · ÷2 deductions",
                             C["inf"],  C["white"]),
            "monthly":      (f"Monthly · {meta['days']} days · Full deductions",
                             C["ok"],   C["white"]),
        }
        txt, bg, fg = info.get(ct, (cut, C["m600"], C["white"]))
        self._badge.config(text=txt, bg=bg, fg=fg)

    # ── Data ────────────────────────────────────────────────────────────────
    def _load(self, filter_type=None):
        if self._tv is None:
            return
        for r in self._tv.get_children():
            self._tv.delete(r)

        m  = self._month.get()
        y  = int(self._year.get())
        rs = get_payroll_records(month=m, year=y)

        if filter_type == "weekly":
            rs = [r for r in rs if r["cutoff"] in WEEKLY_CUTOFFS]
        elif filter_type == "semi":
            rs = [r for r in rs if r["cutoff"] in SEMIMONTHLY_CUTOFFS]
        elif filter_type == "monthly":
            rs = [r for r in rs if r["cutoff"] in MONTHLY_CUTOFFS]

        order = {"1-7":0,"8-14":1,"15-22":2,"23-30":3,
                 "1-15":4,"16-31":5,"1-31":6}
        rs = sorted(rs, key=lambda r: (
            order.get(r["cutoff"], 9), r["last_name"], r["first_name"]))

        # Tag map per cutoff
        tag_map = {
            "1-7":"wk1","8-14":"wk2","15-22":"wk3","23-30":"wk4",
            "1-15":"sm1","16-31":"sm2","1-31":"mon",
        }
        counts = {}
        tg = td = tn = 0
        for rec in rs:
            cut   = rec["cutoff"]
            counts[cut] = counts.get(cut, 0) + 1
            tag = tag_map.get(cut, "mon")
            if counts[cut] % 2 == 0 and cut == "1-31":
                tag = "mona"

            # Short cutoff label for table
            short = {
                "1-7":"Wk1 (1-7)","8-14":"Wk2 (8-14)",
                "15-22":"Wk3 (15-22)","23-30":"Wk4 (23-30)",
                "1-15":"1st Half","16-31":"2nd Half","1-31":"Monthly",
            }.get(cut, cut)

            self._tv.insert("", "end", iid=str(rec["id"]), tag=tag, values=(
                rec["employee_id"],
                short,
                f"{rec['last_name']}, {rec['first_name']}",
                rec["department"] or "",
                rec["days_worked"],
                f"₱{rec['gross_pay']:,.2f}",
                f"₱{rec['total_deductions']:,.2f}",
                f"₱{rec['net_pay']:,.2f}"))
            tg += rec["gross_pay"]
            td += rec["total_deductions"]
            tn += rec["net_pay"]

        cnt = len(rs)
        self._sum_lbl.config(
            text=f"  {cnt} record(s)  ·  "
                 f"Total Gross: ₱{tg:,.2f}  ·  "
                 f"Total Deductions: ₱{td:,.2f}  ·  "
                 f"Total Net Pay: ₱{tn:,.2f}")

    def _on_sel(self, _=None):
        sel = self._tv.selection()
        if not sel:
            return
        m  = self._month.get()
        y  = int(self._year.get())
        rs = get_payroll_records(month=m, year=y)
        r  = next((x for x in rs if str(x["id"]) == sel[0]), None)
        if not r:
            return
        cut   = r["cutoff"]
        meta  = get_cutoff_meta(cut)
        ctype = meta["type"].title()
        div   = meta["divisor"]
        disp  = CUTOFF_DISPLAY_MAP.get(cut, cut)

        lines = [
            f" ┌{'─'*38}┐",
            f" │  {MONTHS[m]} {y}                          │",
            f" │  Cutoff : {disp:<26}│",
            f" │  Type   : {ctype:<10}  Div: ÷{div}          │",
            f" ├{'─'*38}┤",
            f" │  Rent     : ₱{r.get('rent',0):>16,.2f}  │",
            f" │  Gross Sal: ₱{float(r.get('basic_pay',0)/max(float(r['days_worked']),1)*22):>16,.2f}  │",
            f" │  Emp ID   : {r['employee_id']:<25}│",
            f" │  Name     : {(r['last_name'] + ', ' + r['first_name']):<25}│",
            f" │  Dept     : {(r['department'] or ''):<25}│",
            f" ├{'─'*38}┤",
            f" │  EARNINGS                             │",
            f" │  Days Worked    : {str(r['days_worked']):<21}│",
            f" │  Basic Pay      : ₱{r['basic_pay']:>16,.2f}  │",
            f" │  Overtime Pay   : ₱{r['overtime_pay']:>16,.2f}  │",
            f" │  GROSS PAY      : ₱{r['gross_pay']:>16,.2f}  │",
            f" ├{'─'*38}┤",
            f" │  DEDUCTIONS  (monthly ÷ {div})           │",
            f" │  SSS            : ₱{r['sss']:>16,.2f}  │",
            f" │  PhilHealth     : ₱{r['philhealth']:>16,.2f}  │",
            f" │  Pag-IBIG       : ₱{r['pagibig']:>16,.2f}  │",
            f" │  Late Ded.      : ₱{r['late_deduction']:>16,.2f}  │",
            f" │  Absent Ded.    : ₱{r['absent_deduction']:>16,.2f}  │",
            f" │  Cash Advance   : ₱{r['cash_advance']:>16,.2f}  │",
            f" │  HDMF Loan      : ₱{r['hdmf_loan']:>16,.2f}  │",
            f" │  SSS Loan       : ₱{r.get('sss_loan',0):>16,.2f}  │",
            f" │  HDMF Con.      : ₱{r['pagibig']:>16,.2f}  │",
            f" │  HDMF Loan      : ₱{r['hdmf_loan']:>16,.2f}  │",
            f" │  PhilHealth     : ₱{r['philhealth']:>16,.2f}  │",
            f" │  COOP Loan      : ₱{r.get('coop_loan',0):>16,.2f}  │",
            f" │  Alumni Fee     : ₱{r.get('alumni_fee',0):>16,.2f}  │",
            f" │  Cash Advance   : ₱{r['cash_advance']:>16,.2f}  │",
            f" │  Uniform        : ₱{r.get('uniform',0):>16,.2f}  │",
            f" │  Canteen        : ₱{r.get('canteen',0):>16,.2f}  │",
            f" │  Others         : ₱{r['other_deductions']:>16,.2f}  │",
            f" │  TOTAL DED.     : ₱{r['total_deductions']:>16,.2f}  │",
            f" ├{'─'*38}┤",
            f" │  SAVINGS                              │",
            f" │  COOP Savings   : ₱{r.get('coop_savings',0):>16,.2f}  │",
            f" │  Insurance      : ₱{r.get('insurance',0):>16,.2f}  │",
            f" │  Travel Fund    : ₱{r.get('travel_fund',0):>16,.2f}  │",
            f" │  Sacrificial    : ₱{r.get('sacrificial',0):>16,.2f}  │",
            f" │  TOTAL SAVINGS  : ₱{r.get('total_savings',0):>16,.2f}  │",
            f" ├{'═'*38}┤",
            f" │  NET PAY        : ₱{r['net_pay']:>16,.2f}  │",
            f" └{'═'*38}┘",
        ]
        if r.get("notes"):
            lines += ["", f" 📝 {r['notes']}"]

        self._detail.config(state="normal")
        self._detail.delete("1.0", "end")
        self._detail.insert("end", "\n".join(lines))
        self._detail.config(state="disabled")

    # ── Actions ──────────────────────────────────────────────────────────────
    def _process_all(self):
        m    = self._month.get()
        y    = int(self._year.get())
        cut  = self._cut
        emps = get_all_employees()
        if not emps:
            messagebox.showinfo("No Employees",
                "No active employees found.", parent=self); return

        meta  = get_cutoff_meta(cut)
        disp  = CUTOFF_DISPLAY_MAP.get(cut, cut)
        days  = meta["days"]
        div   = meta["divisor"]
        ctype = meta["type"].title()

        msg = (
            f"Process payroll for ALL {len(emps)} active employees?\n\n"
            f"  Month  :  {MONTHS[m]} {y}\n"
            f"  Period :  {disp}\n"
            f"  Type   :  {ctype}\n"
            f"  Default Days  :  {days}\n"
            f"  Deductions    :  Monthly ÷ {div} per cutoff\n\n"
            "Existing records for this cutoff will be updated."
        )
        if not messagebox.askyesno("⚡  Confirm Process All", msg, parent=self):
            return

        count = 0
        for emp in emps:
            p = {
                "period_month": m, "period_year": y, "cutoff": cut,
                "days_worked": days, "overtime_hours": 0,
                "late_minutes": 0, "absent_days": 0,
                "cash_advance": 0, "hdmf_loan": 0,
                "sss_loan": 0, "alumni_fee": 0, "coop_loan": 0,
                "uniform": 0, "canteen": 0,
                "other_deductions": 0,
                "coop_savings": 0, "insurance": 0,
                "travel_fund": 0, "sacrificial": 0,
                "rent": float(emp.get("rent") or 0),
                "notes": "",
            }
            save_payroll(compute_payroll(emp, p))
            count += 1

        self._load()
        messagebox.showinfo("✅  Payroll Processed",
            f"{count} employee(s) processed.\n\n"
            f"Period: {disp}  [{ctype}]\n"
            f"Default: {days} days  ·  Deductions ÷{div}\n\n"
            "Edit individual records to adjust\n"
            "overtime, late, absences, loans, etc.",
            parent=self)

    def _quick_edit(self):
        """Open the quick deduction editor for the selected payroll record."""
        sel = self._tv.selection()
        if not sel:
            messagebox.showinfo("No Selection",
                "Click a payroll record row first.", parent=self)
            return
        m  = self._month.get()
        y  = int(self._year.get())
        rs = get_payroll_records(month=m, year=y)
        rec = next((r for r in rs if str(r["id"]) == sel[0]), None)
        if not rec:
            messagebox.showinfo("Not Found",
                "Record not found. Click Load first.", parent=self)
            return
        QuickDeductionEditor(self, rec, self._load)

    def _edit(self):
        sel  = self._tv.selection()
        m    = self._month.get()
        y    = int(self._year.get())
        rec  = None
        if sel:
            rs  = get_payroll_records(month=m, year=y)
            rec = next((r for r in rs if str(r["id"]) == sel[0]), None)
        PayrollForm(self, rec, m, y, self._cut, self._load)

    def _delete(self):
        sel = self._tv.selection()
        if not sel:
            messagebox.showinfo("No Selection",
                "Select a payroll record to delete.", parent=self); return
        if messagebox.askyesno("Confirm Delete",
                "Delete this payroll record?\nThis cannot be undone.",
                parent=self):
            conn = get_connection()
            conn.execute("DELETE FROM payroll WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close()
            self._load()


# ══════════════════════════════════════════════════════════════════════════════
class PayrollForm(tk.Toplevel):
    """
    Payroll entry / edit form with full cutoff selector.
    Auto-fills correct days and proportional deductions per cutoff type.
    """
    def __init__(self, parent, rec, month, year, cutoff, on_save):
        super().__init__(parent)
        self._rec     = rec
        self._month   = month
        self._year    = year
        self._cutoff  = str(cutoff).strip()
        self._on_save = on_save
        self._vars    = {}
        self.title("Edit Payroll" if rec else "New Payroll Entry")
        self.geometry("610x820")
        self.resizable(True, True)
        self.configure(bg=C["white"])
        self._center()
        self._build()
        if rec:
            self._load_rec(rec)
        else:
            self._apply_cutoff_defaults()
        self.grab_set()
        self.focus_set()

    def _center(self):
        x = (self.winfo_screenwidth()  - 610) // 2
        y = (self.winfo_screenheight() - 820) // 2
        self.geometry(f"610x820+{x}+{y}")

    def _sec(self, parent, text, top=14):
        f = tk.Frame(parent, bg=C["white"]); f.pack(fill="x", pady=(top, 0))
        tk.Label(f, text=text, bg=C["white"],
                 fg=C["m700"], font=F["h3"]).pack(anchor="w")
        tk.Frame(f, bg=C["g500"], height=2).pack(fill="x", pady=(2, 6))

    def _num_field(self, grid, grow, gcol, label, key, default="0"):
        r, c = grow * 2, gcol * 2
        tk.Label(grid, text=label, bg=C["white"],
                 fg=C["t600"], font=F["label"]
                 ).grid(row=r, column=c, sticky="w", pady=(10, 0), padx=(0, 12))
        var = tk.StringVar(value=default)
        e = tk.Entry(grid, textvariable=var, font=F["body"], width=18,
                     bd=0, highlightthickness=1,
                     highlightbackground=C["border"],
                     highlightcolor=C["g500"], bg=C["g100"])
        e.grid(row=r+1, column=c, sticky="ew", pady=(2, 0), padx=(0, 12), ipady=6)
        self._vars[key] = var
        return var

    def _build(self):
        meta  = get_cutoff_meta(self._cutoff)
        ctype = meta["type"].title()
        div   = meta["divisor"]

        # Header
        hdr = tk.Frame(self, bg=C["m700"], height=58)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        period = f"{MONTHS[self._month]} {self._year}"
        tk.Label(hdr, text=f"  💰  Payroll Entry — {period}",
                 bg=C["m700"], fg=C["white"],
                 font=F["h2"]).place(x=14, rely=0.5, anchor="w")
        tk.Frame(self, bg=C["g500"], height=3).pack(fill="x")

        # Cutoff type colour banner
        bcolors = {
            "weekly":       (C["g500"],  C["m800"]),
            "semi-monthly": (C["inf"],   C["white"]),
            "monthly":      (C["ok"],    C["white"]),
        }
        bbg, bfg = bcolors.get(meta["type"], (C["m600"], C["white"]))
        banner = tk.Frame(self, bg=bbg, padx=14, pady=7)
        banner.pack(fill="x")
        self._banner_lbl = tk.Label(banner, text="", bg=bbg, fg=bfg,
                                     font=("Segoe UI", 10, "bold"))
        self._banner_lbl.pack(side="left")
        self._update_banner()

        # Scrollable body
        cv  = tk.Canvas(self, bg=C["white"], highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); cv.pack(fill="both", expand=True)
        body = tk.Frame(cv, bg=C["white"], padx=24, pady=10)
        win  = cv.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win, width=e.width))

        # ── Employee ──────────────────────────────────────────────────
        tk.Label(body, text="Select Employee *", bg=C["white"],
                 fg=C["t600"], font=F["label"]).pack(anchor="w", pady=(8, 0))
        emps = get_all_employees()
        emp_opts = [f"{e['employee_id']} – {e['first_name']} {e['last_name']}"
                    for e in emps]
        self._emp_var = tk.StringVar()
        cb = ttk.Combobox(body, textvariable=self._emp_var,
                          values=emp_opts, width=46,
                          state="readonly", font=F["body"])
        cb.pack(fill="x", pady=(4, 0), ipady=5)
        cb.bind("<<ComboboxSelected>>", self._on_emp_select)

        # ── Cutoff selector ───────────────────────────────────────────
        self._sec(body, "📅  Cutoff Period", top=12)
        cut_row = tk.Frame(body, bg=C["white"])
        cut_row.pack(fill="x", pady=(0, 4))

        tk.Label(cut_row, text="Select Cutoff:", bg=C["white"],
                 fg=C["t600"], font=F["label"]).pack(side="left")
        self._cut_var = tk.StringVar(
            value=CUTOFF_DISPLAY_MAP.get(self._cutoff, self._cutoff))
        cut_cb = ttk.Combobox(cut_row, textvariable=self._cut_var,
                               values=CUTOFF_DISPLAY_LIST, width=26,
                               state="readonly",
                               font=("Segoe UI", 10, "bold"))
        cut_cb.pack(side="left", padx=8, ipady=4)
        cut_cb.bind("<<ComboboxSelected>>", self._on_cutoff_change)

        self._cut_info_lbl = tk.Label(cut_row, text="", bg=C["g100"],
                                       fg=C["m700"], font=("Segoe UI", 9),
                                       padx=8, pady=4)
        self._cut_info_lbl.pack(side="left", padx=6)
        self._refresh_cut_info()

        # ── Earnings ──────────────────────────────────────────────────
        self._sec(body, "💵  Earnings")
        g1 = tk.Frame(body, bg=C["white"]); g1.pack(fill="x")
        days_def = str(get_cutoff_days(self._cutoff))
        self._num_field(g1, 0, 0, "Days Worked",   "days_worked",    default=days_def)
        self._num_field(g1, 0, 1, "Overtime Hours","overtime_hours", default="0")
        g1.grid_columnconfigure(0, weight=1); g1.grid_columnconfigure(2, weight=1)

        # Live earnings preview
        self._earn_lbl = tk.Label(body, text="", bg=C["m900"],
                                   fg=C["g400"], font=("Segoe UI", 9),
                                   anchor="w", padx=10, pady=5)
        self._earn_lbl.pack(fill="x", pady=(3, 0))
        self._vars["days_worked"].trace("w",    self._update_earn_preview)
        self._vars["overtime_hours"].trace("w", self._update_earn_preview)

        # ── Attendance deductions ────────────────────────────────────
        self._sec(body, "🕐  Attendance Deductions")
        g2 = tk.Frame(body, bg=C["white"]); g2.pack(fill="x")
        self._num_field(g2, 0, 0, "Late Minutes", "late_minutes", default="0")
        self._num_field(g2, 0, 1, "Absent Days",  "absent_days",  default="0")
        g2.grid_columnconfigure(0, weight=1); g2.grid_columnconfigure(2, weight=1)

        # ── Deductions — exact order as in BVBC payslip ─────────────
        self._sec(body, f"💸  Deductions  (monthly ÷ {div})")
        gd = tk.Frame(body, bg=C["white"]); gd.pack(fill="x")
        self._num_field(gd, 0, 0, "SSS Contribution (₱)", "sss",             default="0")
        self._num_field(gd, 0, 1, "SSS WISP (₱)",         "sss_wisp",        default="0")
        self._num_field(gd, 1, 0, "SSS Loan (₱)",         "sss_loan",        default="0")
        self._num_field(gd, 1, 1, "HDMF Con. (₱)",        "pagibig",         default="0")
        self._num_field(gd, 2, 0, "HDMF Loan (₱)",        "hdmf_loan",       default="0")
        self._num_field(gd, 2, 1, "PhilHealth (₱)",       "philhealth",      default="0")
        self._num_field(gd, 3, 0, "COOP Loan (₱)",        "coop_loan",       default="0")
        self._num_field(gd, 3, 1, "Alumni Fee (₱)",       "alumni_fee",      default="0")
        self._num_field(gd, 4, 0, "Cash Advance (₱)",     "cash_advance",    default="0")
        self._num_field(gd, 4, 1, "Uniform (₱)",          "uniform",         default="0")
        self._num_field(gd, 5, 0, "Canteen (₱)",          "canteen",         default="0")
        self._num_field(gd, 5, 1, "Others (₱)",           "other_deductions",default="0")
        gd.grid_columnconfigure(0, weight=1); gd.grid_columnconfigure(2, weight=1)

        # ── Savings ──────────────────────────────────────────────────
        self._sec(body, "💰  Savings  (deducted from NET PAY)")
        gs = tk.Frame(body, bg=C["white"]); gs.pack(fill="x")
        self._num_field(gs, 0, 0, "COOP Savings (₱)", "coop_savings", default="0")
        self._num_field(gs, 0, 1, "Insurance (₱)",    "insurance",    default="0")
        self._num_field(gs, 1, 0, "Travel Fund (₱)",  "travel_fund",  default="0")
        self._num_field(gs, 1, 1, "Sacrificial (₱)",  "sacrificial",  default="0")
        gs.grid_columnconfigure(0, weight=1); gs.grid_columnconfigure(2, weight=1)

        # ── Notes ─────────────────────────────────────────────────────
        self._sec(body, "📝  Notes", top=12)
        self._notes = tk.Text(body, font=F["body"], height=3, bd=0,
                              highlightthickness=1,
                              highlightbackground=C["border"],
                              highlightcolor=C["g500"], bg=C["g100"])
        self._notes.pack(fill="x", ipady=4)

        # Button bar
        bf = tk.Frame(self, bg=C["white"], padx=24, pady=12,
                      highlightbackground=C["border"], highlightthickness=1)
        bf.pack(fill="x")
        button(bf, "Compute & Save", "primary", self._save,
               icon="💾", px=20, py=10).pack(side="right", padx=(8, 0))
        button(bf, "Cancel", "ghost", self.destroy,
               px=16, py=10).pack(side="right")

    # ── Events / Helpers ─────────────────────────────────────────────────────
    def _current_cut(self):
        return DISPLAY_TO_KEY.get(self._cut_var.get(), self._cutoff)

    def _on_cutoff_change(self, _=None):
        self._cutoff = self._current_cut()
        self._refresh_cut_info()
        self._update_banner()
        self._on_emp_select()   # re-auto-fill deductions

    def _refresh_cut_info(self):
        cut  = self._current_cut()
        meta = get_cutoff_meta(cut)
        self._cut_info_lbl.config(
            text=f"{meta['type'].title()}  ·  {meta['days']} days  ·  ÷{meta['divisor']}")

    def _update_banner(self):
        cut   = self._current_cut()
        meta  = get_cutoff_meta(cut)
        ctype = meta["type"]
        disp  = CUTOFF_DISPLAY_MAP.get(cut, cut)
        bcolors = {
            "weekly":       (C["g500"],  C["m800"]),
            "semi-monthly": (C["inf"],   C["white"]),
            "monthly":      (C["ok"],    C["white"]),
        }
        bbg, bfg = bcolors.get(ctype, (C["m600"], C["white"]))
        self._banner_lbl.config(
            text=f"📅  {disp}  ·  {ctype.title()}  "
                 f"·  {meta['days']} days  ·  Deductions ÷{meta['divisor']}",
            bg=bbg, fg=bfg)
        self._banner_lbl.master.config(bg=bbg)

    def _on_emp_select(self, _=None):
        raw = self._emp_var.get()
        if not raw:
            return
        eid = raw.split("–")[0].strip().split(" – ")[0].strip()
        emp = get_employee_by_id(eid)
        if not emp:
            return
        ms      = float(emp["monthly_salary"] or 0)
        cut     = self._current_cut()
        divisor = get_cutoff_divisor(cut)
        days    = get_cutoff_days(cut)

        if "sss"        in self._vars:
            self._vars["sss"].set(f"{round(compute_sss(ms) / divisor, 2):.2f}")
        if "philhealth" in self._vars:
            self._vars["philhealth"].set(f"{round(compute_philhealth(ms) / divisor, 2):.2f}")
        if "pagibig"    in self._vars:
            self._vars["pagibig"].set(f"{round(compute_pagibig(ms) / divisor, 2):.2f}")
        if "days_worked" in self._vars:
            self._vars["days_worked"].set(str(days))



        self._update_earn_preview()

    def _update_earn_preview(self, *_):
        raw = self._emp_var.get()
        if not raw:
            self._earn_lbl.config(text=""); return
        eid = raw.split("–")[0].strip().split(" – ")[0].strip()
        emp = get_employee_by_id(eid)
        if not emp:
            return
        try:
            daily = (float(emp["daily_rate"] or 0) or
                     round(float(emp["monthly_salary"] or 0) / 22, 4))
            days  = float(self._vars["days_worked"].get() or 0)
            ot    = float(self._vars["overtime_hours"].get() or 0)
            basic = round(daily * days, 2)
            ot_pay= round(daily / 8 * 1.25 * ot, 2)
            self._earn_lbl.config(
                text=f"  📊  Daily Rate: ₱{daily:,.2f}  ·  "
                     f"Basic Pay: ₱{basic:,.2f}  ·  "
                     f"OT Pay: ₱{ot_pay:,.2f}  ·  "
                     f"Est. Gross: ₱{basic + ot_pay:,.2f}")
        except (ValueError, ZeroDivisionError):
            self._earn_lbl.config(text="")

    def _apply_cutoff_defaults(self):
        meta = get_cutoff_meta(self._cutoff)
        if "days_worked" in self._vars:
            self._vars["days_worked"].set(str(meta["days"]))

    def _load_rec(self, rec):
        emps = get_all_employees()
        for e in emps:
            if e["employee_id"] == rec["employee_id"]:
                self._emp_var.set(
                    f"{e['employee_id']} – {e['first_name']} {e['last_name']}")
                break

        # Restore cutoff
        disp = CUTOFF_DISPLAY_MAP.get(rec["cutoff"], rec["cutoff"])
        self._cut_var.set(disp)
        self._cutoff = rec["cutoff"]
        self._refresh_cut_info()

        for k in ("days_worked","overtime_hours","late_minutes","absent_days",
                  "sss","sss_wisp","sss_loan","pagibig","hdmf_loan","philhealth",
                  "coop_loan","alumni_fee","cash_advance","uniform","canteen",
                  "other_deductions","coop_savings","insurance",
                  "travel_fund","sacrificial"):
            if k in self._vars:
                self._vars[k].set(str(rec[k] if rec.get(k) else 0))
        if rec.get("notes"):
            self._notes.insert("end", rec["notes"])
        self._update_earn_preview()

    def _save(self):
        raw = self._emp_var.get()
        if not raw:
            messagebox.showerror("Required",
                "Please select an employee.", parent=self); return
        eid = raw.split("–")[0].strip().split(" – ")[0].strip()
        emp = get_employee_by_id(eid)
        if not emp:
            messagebox.showerror("Error",
                "Employee not found.", parent=self); return
        cut = self._current_cut()
        try:
            params = {}
            for k in ("days_worked","overtime_hours","late_minutes","absent_days",
                      "sss","sss_wisp","sss_loan","pagibig","hdmf_loan","philhealth",
                      "coop_loan","alumni_fee","cash_advance","uniform","canteen",
                      "other_deductions","coop_savings","insurance",
                      "travel_fund","sacrificial"):
                params[k] = float(
                    self._vars.get(k, tk.StringVar(value="0")).get() or 0)
        except ValueError:
            messagebox.showerror("Invalid Input",
                "All numeric fields must be valid numbers.", parent=self); return
        params.update({
            "period_month": self._month,
            "period_year":  self._year,
            "cutoff":       cut,
            "notes":        self._notes.get("1.0", "end-1c").strip(),
        })
        save_payroll(compute_payroll(emp, params))
        disp = CUTOFF_DISPLAY_MAP.get(cut, cut)
        messagebox.showinfo("✅  Saved",
            f"Payroll for {eid} saved.\nPeriod: {disp}", parent=self)
        self._on_save()
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
class QuickDeductionEditor(tk.Toplevel):
    """
    Quick editor that opens when you double-click an employee row.
    Shows all deductions and savings fields.
    Live formula: NET = HONORARIUM - TOTAL DEDUCTIONS - TOTAL SAVINGS
    """
    def __init__(self, parent, rec, on_save):
        super().__init__(parent)
        self._rec     = dict(rec)
        self._on_save = on_save
        self._vars    = {}

        emp  = get_employee_by_id(rec["employee_id"])
        name = f"{emp['first_name']} {emp['last_name']}" if emp else rec["employee_id"]
        dept = emp.get("department","") if emp else ""

        self.title(f"Edit Deductions – {name}")
        self.resizable(True, True)
        self.configure(bg=C["white"])
        W, H = 640, 820
        x = (self.winfo_screenwidth()  - W) // 2
        y = (self.winfo_screenheight() - H) // 2
        self.geometry(f"{W}x{H}+{x}+{y}")
        self._build(rec, name, dept, emp)
        self.grab_set()
        self.focus_set()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self, rec, name, dept, emp):
        from ui import MONTHS

        # ── Header ───────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["m700"], height=62)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text=f"  ✏️  Edit Deductions",
                 bg=C["m700"], fg=C["white"],
                 font=("Segoe UI", 13, "bold")).place(x=14, rely=0.35, anchor="w")
        tk.Label(hdr,
                 text=f"  {name}  ·  {dept}  ·  "
                      f"{MONTHS[int(rec['period_month'])]} {rec['period_year']}"
                      f"  |  Cutoff: {rec['cutoff']}",
                 bg=C["m700"], fg=C["g400"],
                 font=("Segoe UI", 9)).place(x=14, rely=0.72, anchor="w")
        tk.Frame(self, bg=C["g500"], height=3).pack(fill="x")

        # ── Button bar (bottom) ───────────────────────────────────────────────
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", side="bottom")
        bf = tk.Frame(self, bg=C["white"], pady=10); bf.pack(fill="x", side="bottom")
        button(bf, "Save & Recompute", "primary", self._save,
               icon="💾", px=20, py=9).pack(side="right", padx=14)
        button(bf, "Cancel", "ghost", self.destroy,
               px=16, py=9).pack(side="right", padx=4)

        # ── Scrollable body ───────────────────────────────────────────────────
        outer = tk.Frame(self, bg=C["white"]); outer.pack(fill="both", expand=True)
        vsb   = ttk.Scrollbar(outer, orient="vertical"); vsb.pack(side="right", fill="y")
        cv    = tk.Canvas(outer, bg=C["white"], yscrollcommand=vsb.set,
                         highlightthickness=0)
        vsb.config(command=cv.yview); cv.pack(side="left", fill="both", expand=True)
        body  = tk.Frame(cv, bg=C["white"])
        bid   = cv.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",   lambda e: cv.itemconfig(bid, width=e.width))
        cv.bind("<MouseWheel>",  lambda e: cv.yview_scroll(int(-1*(e.delta/120)),"units"))

        # ── Helpers ───────────────────────────────────────────────────────────
        def sec(title, bg=C["m700"]):
            f = tk.Frame(body, bg=bg); f.pack(fill="x", pady=(10,0))
            tk.Label(f, text=f"  {title}", bg=bg, fg=C["white"],
                     font=("Segoe UI", 10, "bold"), pady=6).pack(side="left",padx=4)

        def num_row(parent, label, key, default=0, row=0, col=0):
            """Two-column grid number field."""
            r, c = row*2, col*2
            tk.Label(parent, text=label, bg=C["white"], fg=C["t600"],
                     font=("Segoe UI", 9, "bold")
                     ).grid(row=r, column=c, sticky="w",
                            pady=(10,0), padx=(14,8))
            var = tk.StringVar(value=f"{float(rec.get(key) or default):.2f}")
            e = tk.Entry(parent, textvariable=var, font=("Segoe UI",10),
                         width=16, bd=0, highlightthickness=1,
                         highlightbackground=C["border"],
                         highlightcolor=C["g500"], bg=C["g100"],
                         fg=C["m700"])
            e.grid(row=r+1, column=c, sticky="ew",
                   pady=(2,0), padx=(14,8), ipady=6)
            self._vars[key] = var
            var.trace("w", self._update_preview)
            return var

        # Compute daily rate: gross_pay / days_worked
        _days_worked = float(rec.get("days_worked") or 1)
        _gross       = float(rec.get("gross_pay")   or 0)
        _daily_rate  = round(_gross / _days_worked, 4) if _days_worked else 0
        self._daily_rate = _daily_rate

        # ── Earnings info (read-only) ─────────────────────────────────────────
        sec("💵  Earnings (Read-only)")
        earn_f = tk.Frame(body, bg=C["g100"]); earn_f.pack(fill="x", padx=14, pady=4)
        def erow(lbl, val, money=True):
            rf = tk.Frame(earn_f, bg=C["g100"]); rf.pack(fill="x")
            tk.Label(rf, text=lbl, bg=C["g100"], fg=C["t600"],
                     font=("Segoe UI",9,"bold"), width=22, anchor="w"
                     ).pack(side="left", padx=8, pady=3)
            txt = f"₱ {float(val or 0):,.2f}" if money else str(val)
            tk.Label(rf, text=txt, bg=C["g100"],
                     fg=C["m700"], font=("Segoe UI",9,"bold"), anchor="e"
                     ).pack(side="right", padx=12, pady=3)

        erow("Days Worked",            rec["days_worked"], money=False)
        erow("Daily Rate",             _daily_rate)
        erow("Honorarium (Gross Pay)", rec["gross_pay"])

        # ── Days of Absent (editable — auto-computes deduction) ───────────────
        sec("🗓️  Attendance Adjustment", bg=C["m600"])
        ab_frame = tk.Frame(body, bg=C["white"]); ab_frame.pack(fill="x")

        # Left: Days of Absent input
        tk.Label(ab_frame, text="Days of Absent",
                 bg=C["white"], fg=C["t600"],
                 font=("Segoe UI", 9, "bold")
                 ).grid(row=0, column=0, sticky="w", pady=(10,0), padx=(14,8))
        self._vars["absent_days"] = tk.StringVar(
            value=str(int(float(rec.get("absent_days") or 0))))
        ab_entry = tk.Entry(ab_frame,
                            textvariable=self._vars["absent_days"],
                            font=("Segoe UI", 12, "bold"),
                            width=14, bd=0, highlightthickness=2,
                            highlightbackground=C["m500"],
                            highlightcolor=C["g500"],
                            bg="#FFF8EE", fg=C["m700"])
        ab_entry.grid(row=1, column=0, sticky="ew",
                      pady=(2,4), padx=(14,8), ipady=8)
        self._vars["absent_days"].trace("w", self._update_preview)

        # Right: Absent Deduction (auto-computed, live display)
        tk.Label(ab_frame, text="Absent Deduction  (auto-computed)",
                 bg=C["white"], fg=C["t600"],
                 font=("Segoe UI", 9, "bold")
                 ).grid(row=0, column=2, sticky="w", pady=(10,0), padx=(8,14))
        self._absent_ded_var = tk.StringVar(
            value=f"₱ {float(rec.get('absent_deduction') or 0):,.2f}")
        tk.Label(ab_frame, textvariable=self._absent_ded_var,
                 bg=C["g100"], fg=C["m700"],
                 font=("Segoe UI", 12, "bold"),
                 relief="flat", anchor="e", padx=10
                 ).grid(row=1, column=2, sticky="ew",
                        pady=(2,4), padx=(8,14), ipady=8)
        ab_frame.grid_columnconfigure(0, weight=1)
        ab_frame.grid_columnconfigure(2, weight=1)

        # Formula note
        tk.Label(body,
                 text=f"  Formula:  Days of Absent  x  Daily Rate (₱{_daily_rate:,.4f})  =  Absent Deduction",
                 bg="#FFF8EE", fg=C["m700"],
                 font=("Segoe UI", 8), anchor="w", pady=4
                 ).pack(fill="x", padx=14, pady=(0, 4))

        # ── Deductions ────────────────────────────────────────────────────────
        sec("💸  Deductions  (subtracted from Honorarium)")
        gd = tk.Frame(body, bg=C["white"]); gd.pack(fill="x")
        num_row(gd, "SSS Contribution (₱)", "sss",             row=0, col=0)
        num_row(gd, "SSS WISP (₱)",         "sss_wisp",        row=0, col=1)
        num_row(gd, "SSS Loan (₱)",         "sss_loan",        row=1, col=0)
        num_row(gd, "PhilHealth (₱)",       "philhealth",      row=1, col=1)
        num_row(gd, "Pag-IBIG / HDMF Con (₱)","pagibig",      row=2, col=0)
        num_row(gd, "HDMF Loan (₱)",        "hdmf_loan",       row=2, col=1)
        num_row(gd, "Alumni Fee (₱)",        "alumni_fee",      row=3, col=0)
        num_row(gd, "COOP Loan (₱)",         "coop_loan",       row=3, col=1)
        num_row(gd, "Cash Advance (₱)",      "cash_advance",    row=4, col=0)
        num_row(gd, "Uniform (₱)",           "uniform",         row=4, col=1)
        num_row(gd, "Canteen (₱)",           "canteen",         row=5, col=0)
        num_row(gd, "Others (₱)",            "other_deductions",row=5, col=1)
        gd.grid_columnconfigure(0, weight=1); gd.grid_columnconfigure(2, weight=1)

        # Late deduction only (absent deduction moved to editable section above)
        la_f = tk.Frame(body, bg=C["g100"]); la_f.pack(fill="x", padx=14, pady=(4,0))
        def erow2(lbl, val):
            rf = tk.Frame(la_f, bg=C["g100"]); rf.pack(fill="x")
            tk.Label(rf, text=lbl, bg=C["g100"], fg=C["t600"],
                     font=("Segoe UI",8), width=26, anchor="w"
                     ).pack(side="left", padx=8, pady=2)
            tk.Label(rf, text=f"₱ {float(val or 0):,.2f}", bg=C["g100"],
                     fg=C["t600"], font=("Segoe UI",8), anchor="e"
                     ).pack(side="right", padx=12, pady=2)
        erow2("Late Deduction (auto)", rec.get("late_deduction", 0))

        # ── Savings ───────────────────────────────────────────────────────────
        sec("💰  Savings  (also subtracted from Honorarium)", bg="#2D6A2D")
        gs = tk.Frame(body, bg=C["white"]); gs.pack(fill="x")
        num_row(gs, "COOP Savings (₱)",       "coop_savings", row=0, col=0)
        num_row(gs, "Insurance (₱)",           "insurance",    row=0, col=1)
        num_row(gs, "Travel Fund (₱)",         "travel_fund",  row=1, col=0)
        num_row(gs, "Sacrificial Offering (₱)","sacrificial",  row=1, col=1)
        gs.grid_columnconfigure(0, weight=1); gs.grid_columnconfigure(2, weight=1)

        # ── Live computation preview ──────────────────────────────────────────
        sec("📊  Live Computation", bg=C["m600"])
        self._prev_frame = tk.Frame(body, bg=C["m900"])
        self._prev_frame.pack(fill="x", pady=(0,8))
        self._update_preview()

    # ── Live preview ──────────────────────────────────────────────────────────
    def _update_preview(self, *_):
        for w in self._prev_frame.winfo_children():
            w.destroy()

        def fv(k, fallback=0):
            try: return float(self._vars.get(k, tk.StringVar(value="0")).get() or 0)
            except ValueError: return float(fallback)

        gross      = float(self._rec.get("gross_pay", 0))
        late       = float(self._rec.get("late_deduction", 0))
        # Compute absent_deduction live from input
        daily_rate = getattr(self, "_daily_rate", 0)
        absent_days= fv("absent_days")
        absent     = round(absent_days * daily_rate, 2)

        # Update the absent deduction display label
        try:
            self._absent_ded_var.set(f"₱ {absent:,.2f}")
        except Exception:
            pass

        # Deductions
        total_ded = round(
            fv("sss") + fv("sss_wisp") + fv("sss_loan") +
            fv("philhealth") + fv("pagibig") + fv("hdmf_loan") +
            fv("alumni_fee") + fv("coop_loan") + fv("cash_advance") +
            fv("uniform") + fv("canteen") + fv("other_deductions") +
            late + absent, 2)

        # Savings
        total_sav = round(
            fv("coop_savings") + fv("insurance") +
            fv("travel_fund") + fv("sacrificial"), 2)

        net = round(gross - total_ded - total_sav, 2)

        def prow(lbl, val, bg=C["m900"], fg=C["g400"], bold=False, big=False):
            rf = tk.Frame(self._prev_frame, bg=bg); rf.pack(fill="x")
            sz = 10 if big else 9
            tk.Label(rf, text=f"  {lbl}", bg=bg, fg=fg,
                     font=("Segoe UI", sz, "bold" if bold else "normal")
                     ).pack(side="left", pady=4, padx=6)
            clr = C["gold"] if (big and net >= 0) else ("#EF9A9A" if (big and net < 0) else fg)
            tk.Label(rf, text=f"₱ {val:,.2f}  ", bg=bg, fg=clr,
                     font=("Segoe UI", sz, "bold" if (bold or big) else "normal")
                     ).pack(side="right", pady=4, padx=6)

        prow("Honorarium (Gross Pay)",  gross,     bold=True)
        prow("─  Total Deductions",     total_ded, fg="#EF9A9A")
        prow("─  Total Savings",        total_sav, fg="#90CAF9")
        tk.Frame(self._prev_frame, bg=C["g500"], height=1).pack(fill="x")
        prow("=  NET PAY",              net,
             bg=C["m700"] if net >= 0 else "#5A0000",
             fg=C["gold"], bold=True, big=True)

    # ── Save ──────────────────────────────────────────────────────────────────
    def _save(self):
        def fv(k, fallback=0):
            try: return float(self._vars.get(k, tk.StringVar(value="0")).get() or 0)
            except ValueError: return float(fallback)

        rec = dict(self._rec)
        gross      = float(rec.get("gross_pay", 0))
        late       = float(rec.get("late_deduction", 0))
        # Recompute absent deduction from editable input
        daily_rate = getattr(self, "_daily_rate", 0)
        absent_days = fv("absent_days")
        absent      = round(absent_days * daily_rate, 2)
        # Save back to record
        rec["absent_days"]      = absent_days
        rec["absent_deduction"] = absent

        # Update all deduction fields
        for k in ("sss","sss_wisp","sss_loan","philhealth","pagibig","hdmf_loan",
                  "alumni_fee","coop_loan","cash_advance","uniform","canteen",
                  "other_deductions","coop_savings","insurance","travel_fund",
                  "sacrificial"):
            rec[k] = fv(k)

        total_ded = round(
            rec["sss"] + rec["sss_wisp"] + rec["sss_loan"] +
            rec["philhealth"] + rec["pagibig"] + rec["hdmf_loan"] +
            rec["alumni_fee"] + rec["coop_loan"] + rec["cash_advance"] +
            rec["uniform"] + rec["canteen"] + rec["other_deductions"] +
            late + absent, 2)

        total_sav = round(
            rec["coop_savings"] + rec["insurance"] +
            rec["travel_fund"] + rec["sacrificial"], 2)

        rec["total_deductions"] = total_ded
        rec["total_savings"]    = total_sav
        rec["net_pay"]          = round(gross - total_ded - total_sav, 2)

        save_payroll(rec)
        self._on_save()
        self.destroy()
        messagebox.showinfo("✅  Saved",
            f"Deductions updated.\n\nNet Pay: \u20b1{rec['net_pay']:,.2f}",
            parent=self.master)
