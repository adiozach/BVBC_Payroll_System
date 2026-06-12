"""BVBC Payroll – Payslip Generator (Format matching actual BVBC payslip)"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, sys, os
from datetime import datetime
from database import get_all_employees, get_payroll_records, get_employee_by_id
from ui import C, F, MONTHS, page_header, section_header, card, button, treeview


# ─────────────────────────────────────────────────────────────────────────────
# PAYSLIP TEXT FORMATTER
# Format matches the actual BVBC payslip photo:
#   Grace Baptist Church / BVBC / BVBC Elementary header
#   Employee name + Monthly Allowance
#   Rent / TOTAL
#   PAYROLL section: daily, days, absents, GROSS PAY
#   Deductions section (SSS, WISP, HDMF Con., HDMF Loan, PhilHealth,
#                       COOP Loan, Alumni Fee, Uniform)
#   Savings section  (Travel, Insurance, COOP Savings, Sacrificial, Others)
#   NET PAY + Date Claimed
# ─────────────────────────────────────────────────────────────────────────────

DEPT_HEADER = {
    "GBC - Church":      "Grace Baptist Church",
    "BVBC - College":    "Baptist Voice Bible College",
    "BVBC - Elementary": "Baptist Voice Bible College\n     Basic Education Department",
}

def _dash(val):
    """Return formatted money or dash if zero."""
    if val is None or float(val) == 0:
        return "         -"
    return f"{float(val):>10,.2f}"

def _payslip_lines(rec):
    """Build BVBC-format payslip text matching the photo."""
    m      = int(rec["period_month"])
    yr     = rec["period_year"]
    ct     = rec["cutoff"]
    ln     = rec["last_name"]
    fn     = rec["first_name"]
    mn     = rec.get("middle_initial","")
    dept   = rec.get("department","") or ""
    pos    = rec.get("position","")   or ""
    eid    = rec["employee_id"]
    ms     = float(rec.get("basic_pay", 0))        # weekly basic pay used as allowance base
    gross  = float(rec["gross_pay"])
    days   = rec["days_worked"]
    absent = float(rec.get("absent_days", 0))

    # Determine org header
    org = DEPT_HEADER.get(dept, "Baptist Voice Bible College")

    # Extract middle initial from middle_name if available
    emp = get_employee_by_id(eid)
    middle = ""
    if emp and emp.get("middle_name"):
        middle = emp["middle_name"].strip()
        if middle and not middle.endswith("."):
            middle = middle[0].upper() + "."
    full_name = f"{fn} {middle} {ln}".strip().replace("  "," ")

    # ── Line format helpers ───────────────────────────────────────────────────
    W  = 40   # total inner width
    def hline(ch="─"): return "  " + ch * W
    def dline():       return "  " + "=" * W
    def cline(txt):    return "  " + txt.center(W)
    def rrow(label, val, bold=False):
        lw = 24
        marker = "" if not bold else ""
        return f"  {label:<{lw}} {val:>14}"
    def blank(): return ""

    # ── Build payslip ─────────────────────────────────────────────────────────
    lines = [
        blank(),
        hline("─"),
        cline(org),
        hline("─"),
        blank(),
        cline(f"◆  {full_name}  ◆"),
        hline("─"),
        rrow("Monthly Allowance", f"{float(rec.get('basic_pay',0))*4:,.2f}"),
        blank(),
        "  Other Benefits:",
        rrow("  Rent", _dash(0)),
        hline("─"),
        rrow("TOTAL", f"{float(rec.get('basic_pay',0))*4:,.2f}", bold=True),
        blank(),
        hline("═"),
        cline("PAYROLL"),
        cline(f"{MONTHS[m]} {yr}  |  Cutoff: {ct}"),
        hline("─"),
        rrow("Daily Wage/Salary",    f"{float(rec.get('basic_pay',0)/max(float(days),1)):,.2f}"),
        rrow("# of Working Days:",   str(days)),
        rrow("# of Absent/s:",       str(int(absent)) if absent else "-"),
        hline("─"),
        rrow("GROSS PAY:",            f"{gross:,.2f}", bold=True),
        blank(),
        hline("─"),
        cline("Deductions:"),
        hline("─"),
        rrow("SSS Contribution",      _dash(rec.get("sss",             0))),
        rrow("SSS WISP",              _dash(rec.get("sss_wisp",        0))),
        rrow("SSS Loan",              _dash(rec.get("sss_loan",        0))),
        rrow("HDMF Con.",             _dash(rec.get("pagibig",         0))),
        rrow("HDMF Loan",             _dash(rec.get("hdmf_loan",       0))),
        rrow("Philhealth",            _dash(rec.get("philhealth",      0))),
        rrow("COOP Loan",             _dash(rec.get("coop_loan",       0))),
        rrow("Alumni Fee",            _dash(rec.get("alumni_fee",      0))),
        rrow("CA",                    _dash(rec.get("cash_advance",    0))),
        rrow("Uniform",               _dash(rec.get("uniform",         0))),
        rrow("Canteen",               _dash(rec.get("canteen",         0))),
        rrow("Others",                _dash(rec.get("other_deductions",0))),
        blank(),
        hline("─"),
        cline("Savings:"),
        hline("─"),
        rrow("COOP Savings",         _dash(rec.get("coop_savings", 0))),
        rrow("Insurance",            _dash(rec.get("insurance",    0))),
        rrow("Travel Fund",          _dash(rec.get("travel_fund",  0))),
        rrow("Sacrificial Offering", _dash(rec.get("sacrificial",  0))),
        rrow("TOTAL SAVINGS",        _dash(rec.get("total_savings",0))),
        blank(),
        hline("═"),
        rrow("NET PAY",              f"{float(rec['net_pay']):,.2f}", bold=True),
        rrow("Date Claimed",         datetime.now().strftime("%m/%d/%Y")),
        hline("═"),
        blank(),
        blank(),
    ]
    return lines


# ─────────────────────────────────────────────────────────────────────────────
class PayslipPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.pack(fill="both", expand=True)
        self.app    = app
        now         = datetime.now()
        self._month = tk.IntVar(value=now.month)
        self._year  = tk.StringVar(value=str(now.year))
        self._emp   = tk.StringVar()
        self._build()

    def _build(self):
        page_header(self, "📄  Payslip Generator",
                    "BVBC payslip format — Preview and export")

        # ── Controls ─────────────────────────────────────────────────────────
        ctrl = tk.Frame(self, bg=C["white"], padx=16, pady=10,
                        highlightbackground=C["border"], highlightthickness=1)
        ctrl.pack(fill="x")

        def lbl(t):
            tk.Label(ctrl, text=t, bg=C["white"],
                     fg=C["t600"], font=F["label"]).pack(side="left")
        def vsep():
            tk.Frame(ctrl, bg=C["border"], width=1
                     ).pack(side="left", fill="y", padx=12)

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
        lbl("Employee:")
        emps     = get_all_employees()
        emp_opts = ["All Employees"] + [
            f"{e['employee_id']} – {e['first_name']} {e['last_name']}"
            for e in emps
        ]
        cb = ttk.Combobox(ctrl, textvariable=self._emp,
                          values=emp_opts, width=30,
                          state="readonly", font=F["body"])
        cb.pack(side="left", padx=(4, 12), ipady=4)
        cb.set("All Employees")
        cb.bind("<<ComboboxSelected>>", lambda e: self._preview())
        vsep()
        button(ctrl, "Preview",    "ghost",   self._preview,    icon="🔍", py=6).pack(side="left", padx=3)
        button(ctrl, "Export",     "success", self._export,     icon="📥", py=6).pack(side="left", padx=3)
        button(ctrl, "Export All", "primary", self._export_all, icon="📦", py=6).pack(side="left", padx=3)

        # ── Body ─────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Left — employee list
        left = tk.Frame(body, bg=C["bg"])
        left.pack(side="left", fill="y", padx=(0, 14))
        section_header(left, "👥  Employees", bg=C["bg"]).pack(fill="x")

        tf, self._etv = treeview(left, ("id","name"), ["ID","Name"],
                                  [84, 186], height=20,
                                  anchors={"id":"center","name":"w"})
        tf.pack(fill="y")
        self._etv.bind("<<TreeviewSelect>>", self._on_emp)

        # Right — preview
        r_out, r_in = card(body, padx=20, pady=18)
        r_out.pack(side="left", fill="both", expand=True)
        section_header(r_in, "📄  Payslip Preview", bg=C["card"]).pack(fill="x")

        txt_wrap = tk.Frame(r_in, bg=C["card"])
        txt_wrap.pack(fill="both", expand=True)
        self._txt = tk.Text(txt_wrap, font=("Consolas", 10),
                            bg=C["g100"], fg=C["t900"],
                            relief="flat", wrap="none",
                            state="disabled", padx=14, pady=12)
        vsb = ttk.Scrollbar(txt_wrap, orient="vertical",   command=self._txt.yview)
        hsb = ttk.Scrollbar(txt_wrap, orient="horizontal",  command=self._txt.xview)
        self._txt.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        txt_wrap.grid_rowconfigure(0, weight=1)
        txt_wrap.grid_columnconfigure(0, weight=1)

        self._load_emp_list()
        self._preview()

    # ── Employee list ─────────────────────────────────────────────────────────
    def _load_emp_list(self):
        for r in self._etv.get_children(): self._etv.delete(r)
        for i, e in enumerate(get_all_employees()):
            tag = "even" if i % 2 == 0 else "odd"
            self._etv.insert("", "end", iid=e["employee_id"], tag=tag,
                             values=(e["employee_id"],
                                     f"{e['last_name']}, {e['first_name']}"))

    def _on_emp(self, _):
        sel = self._etv.selection()
        if sel:
            emps = get_all_employees()
            e    = next((x for x in emps if x["employee_id"] == sel[0]), None)
            if e:
                self._emp.set(f"{e['employee_id']} – {e['first_name']} {e['last_name']}")
        self._preview()

    def _get_recs(self):
        m   = self._month.get()
        y   = int(self._year.get())
        raw = self._emp.get()
        eid = None
        if raw and raw != "All Employees":
            for e in get_all_employees():
                disp = f"{e['employee_id']} – {e['first_name']} {e['last_name']}"
                if disp == raw:
                    eid = e["employee_id"]; break
        return get_payroll_records(month=m, year=y, emp_id=eid)

    def _preview(self):
        recs  = self._get_recs()
        m     = self._month.get()
        y     = int(self._year.get())
        lines = []
        for rec in recs:
            lines.extend(_payslip_lines(rec))
        if not lines:
            lines = [
                "",
                f"  No payroll records for {MONTHS[m]} {y}.",
                "",
                "  How to generate payslips:",
                "  1. Go to  💰 Payroll Processing",
                "  2. Select month, year and cutoff",
                "  3. Click  ⚡ Process All",
                "  4. Return here to preview and export",
                "",
            ]
        self._txt.config(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.insert("end", "\n".join(lines))
        self._txt.config(state="disabled")

    def _export(self):
        from reports_export import export_payslip_excel
        recs = self._get_recs()
        if not recs:
            messagebox.showinfo("No Records",
                "No payroll records found.\nProcess payroll first.", parent=self); return
        paths = []
        for rec in recs:
            emp = get_employee_by_id(rec["employee_id"])
            if not emp: continue
            try:
                paths.append(export_payslip_excel(dict(rec), dict(emp)))
            except RuntimeError as e:
                messagebox.showerror("openpyxl Missing", str(e), parent=self); return
            except Exception as e:
                messagebox.showerror("Export Error", str(e), parent=self); return
        if paths:
            messagebox.showinfo("✅  Exported",
                f"{len(paths)} payslip(s) saved to:\n{os.path.dirname(paths[0])}",
                parent=self)
            self._open(os.path.dirname(paths[0]))

    def _export_all(self):
        from reports_export import export_payslip_excel
        m    = self._month.get()
        y    = int(self._year.get())
        recs = get_payroll_records(month=m, year=y)
        if not recs:
            messagebox.showinfo("No Records",
                "No payroll records for this period.", parent=self); return
        if not messagebox.askyesno("Export All Payslips",
                f"Export {len(recs)} payslip(s) for {MONTHS[m]} {y}?",
                parent=self): return
        paths = []
        for rec in recs:
            emp = get_employee_by_id(rec["employee_id"])
            if not emp: continue
            try:
                paths.append(export_payslip_excel(dict(rec), dict(emp)))
            except RuntimeError as e:
                messagebox.showerror("openpyxl Missing", str(e), parent=self); return
            except Exception as e:
                messagebox.showerror("Export Error", str(e), parent=self); return
        if paths:
            messagebox.showinfo("✅  Done",
                f"{len(paths)} payslips exported to:\n{os.path.dirname(paths[0])}",
                parent=self)
            self._open(os.path.dirname(paths[0]))

    def _open(self, folder):
        try:
            if   sys.platform == "win32":  os.startfile(folder)
            elif sys.platform == "darwin": subprocess.Popen(["open",     folder])
            else:                          subprocess.Popen(["xdg-open", folder])
        except Exception: pass
