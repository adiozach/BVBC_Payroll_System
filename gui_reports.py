"""BVBC Payroll – Reports Page"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, sys, os
from datetime import datetime
from database import get_payroll_records, get_all_employees
from ui import C, F, MONTHS, page_header, section_header, card, button, treeview


class ReportsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.pack(fill="both", expand=True)
        self.app   = app
        now        = datetime.now()
        self._month= tk.IntVar(value=now.month)
        self._year = tk.StringVar(value=str(now.year))
        self._build()

    def _build(self):
        page_header(self, "📊  Reports", "Monthly payroll, salary history & deductions")

        ctrl = tk.Frame(self, bg=C["white"], padx=16, pady=10,
                        highlightbackground=C["border"], highlightthickness=1)
        ctrl.pack(fill="x")

        def lbl(t):
            tk.Label(ctrl, text=t, bg=C["white"],
                     fg=C["t600"], font=F["label"]).pack(side="left")
        def vsep():
            tk.Frame(ctrl, bg=C["border"], width=1).pack(side="left", fill="y", padx=12)

        lbl("Month:")
        ttk.Combobox(ctrl, textvariable=self._month,
                     values=list(range(1, 13)), width=5,
                     state="readonly", font=F["body"]
                     ).pack(side="left", padx=(4,0), ipady=4)
        vsep()
        lbl("Year:")
        ttk.Combobox(ctrl, textvariable=self._year,
                     values=[str(y) for y in range(2020, 2031)],
                     width=7, state="readonly", font=F["body"]
                     ).pack(side="left", padx=(4,0), ipady=4)
        vsep()
        button(ctrl, "Load",             "ghost",   self._load,            icon="🔄", py=6).pack(side="left", padx=3)
        button(ctrl, "Export Payroll",   "success", self._export_payroll,  icon="📥", py=6).pack(side="left", padx=3)
        button(ctrl, "Export Deductions","primary", self._export_deductions,icon="📋", py=6).pack(side="left", padx=3)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=12)

        self._t1 = tk.Frame(nb, bg=C["bg"])
        self._t2 = tk.Frame(nb, bg=C["bg"])
        self._t3 = tk.Frame(nb, bg=C["bg"])
        nb.add(self._t1, text="  📋  Monthly Summary  ")
        nb.add(self._t2, text="  📈  Salary History  ")
        nb.add(self._t3, text="  💸  Deductions  ")

        self._build_t1()
        self._build_t2()
        self._build_t3()
        self._load()

    # ── Tab 1: Monthly summary ────────────────────────────────────────
    def _build_t1(self):
        cols   = ("id","name","dept","days","basic","ot","gross","ded","net")
        hdrs   = ["Emp ID","Name","Dept","Days","Basic Pay",
                  "OT Pay","Gross Pay","Total Ded","Net Pay"]
        widths = [84, 180, 110, 54, 112, 96, 112, 112, 114]
        anchors= {"id":"center","name":"w","dept":"w","days":"center",
                  "basic":"right","ot":"right","gross":"right",
                  "ded":"right","net":"right"}
        tf, self._tv1 = treeview(self._t1, cols, hdrs, widths, height=16,
                                  anchors=anchors, stretch_col="name")
        tf.pack(fill="both", expand=True)
        self._sum1 = tk.Label(self._t1, text="", bg=C["g100"],
                               fg=C["m700"], font=F["label"],
                               anchor="w", padx=14, pady=7,
                               highlightbackground=C["border"],
                               highlightthickness=1)
        self._sum1.pack(fill="x")

    # ── Tab 2: Salary history ─────────────────────────────────────────
    def _build_t2(self):
        top = tk.Frame(self._t2, bg=C["bg"])
        top.pack(fill="x", padx=14, pady=10)
        tk.Label(top, text="Employee:", bg=C["bg"],
                 fg=C["t600"], font=F["label"]).pack(side="left")
        emps = get_all_employees()
        emp_opts = [f"{e['employee_id']} – {e['first_name']} {e['last_name']}"
                    for e in emps]
        self._h_emp = tk.StringVar()
        cb = ttk.Combobox(top, textvariable=self._h_emp,
                          values=emp_opts, width=34,
                          state="readonly", font=F["body"])
        cb.pack(side="left", padx=(6, 14), ipady=4)
        button(top, "Show History", "primary",
               self._load_history, icon="📈", py=6).pack(side="left")

        cols   = ("mo","yr","cut","days","gross","ded","net")
        hdrs   = ["Month","Year","Cutoff","Days","Gross Pay","Total Ded","Net Pay"]
        widths = [112, 70, 82, 60, 118, 118, 118]
        anchors= {"mo":"center","yr":"center","cut":"center","days":"center",
                  "gross":"right","ded":"right","net":"right"}
        tf, self._tv2 = treeview(self._t2, cols, hdrs, widths, height=14,
                                  anchors=anchors)
        tf.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    # ── Tab 3: Deductions ─────────────────────────────────────────────
    def _build_t3(self):
        cols   = ("id","name","sss","ph","pig","ca","hdmf","ssl","oth","tot")
        hdrs   = ["Emp ID","Name","SSS","PhilHealth","Pag-IBIG",
                  "Cash Adv","HDMF Loan","SSS Loan","Other","Total Ded"]
        widths = [84, 175, 84, 96, 84, 84, 96, 84, 84, 102]
        anchors= {"id":"center","name":"w",
                  "sss":"right","ph":"right","pig":"right","ca":"right",
                  "hdmf":"right","ssl":"right","oth":"right","tot":"right"}
        tf, self._tv3 = treeview(self._t3, cols, hdrs, widths, height=16,
                                  anchors=anchors, stretch_col="name")
        tf.pack(fill="both", expand=True)
        self._sum3 = tk.Label(self._t3, text="", bg=C["g100"],
                               fg=C["m700"], font=F["label"],
                               anchor="w", padx=14, pady=7,
                               highlightbackground=C["border"],
                               highlightthickness=1)
        self._sum3.pack(fill="x")

    def _load(self):
        m  = self._month.get(); y = int(self._year.get())
        rs = get_payroll_records(month=m, year=y)

        # Tab 1
        for r in self._tv1.get_children(): self._tv1.delete(r)
        tg = td = tn = 0
        for i, rec in enumerate(rs):
            tag = "even" if i % 2 == 0 else "odd"
            self._tv1.insert("", "end", tag=tag, values=(
                rec["employee_id"],
                f"{rec['last_name']}, {rec['first_name']}",
                rec["department"] or "",
                rec["days_worked"],
                f"₱{rec['basic_pay']:,.2f}",
                f"₱{rec['overtime_pay']:,.2f}",
                f"₱{rec['gross_pay']:,.2f}",
                f"₱{rec['total_deductions']:,.2f}",
                f"₱{rec['net_pay']:,.2f}"))
            tg += rec["gross_pay"]; td += rec["total_deductions"]; tn += rec["net_pay"]
        self._sum1.config(
            text=f"  {len(rs)} employees  |  "
                 f"Total Gross: ₱{tg:,.2f}  |  "
                 f"Total Deductions: ₱{td:,.2f}  |  "
                 f"Total Net Pay: ₱{tn:,.2f}")

        # Tab 3
        for r in self._tv3.get_children(): self._tv3.delete(r)
        ttd = 0
        for i, rec in enumerate(rs):
            tag = "even" if i % 2 == 0 else "odd"
            self._tv3.insert("", "end", tag=tag, values=(
                rec["employee_id"],
                f"{rec['last_name']}, {rec['first_name']}",
                f"₱{rec['sss']:,.2f}",
                f"₱{rec['philhealth']:,.2f}",
                f"₱{rec['pagibig']:,.2f}",
                f"₱{rec['cash_advance']:,.2f}",
                f"₱{rec['hdmf_loan']:,.2f}",
                f"₱{rec['sss_loan']:,.2f}",
                f"₱{rec['other_deductions']:,.2f}",
                f"₱{rec['total_deductions']:,.2f}"))
            ttd += rec["total_deductions"]
        self._sum3.config(
            text=f"  {len(rs)} employees  |  Total Deductions: ₱{ttd:,.2f}")

    def _load_history(self):
        raw = self._h_emp.get()
        if not raw:
            messagebox.showinfo("Select Employee",
                "Please select an employee.", parent=self); return
        # Find employee_id
        eid = None
        for e in get_all_employees():
            if f"{e['employee_id']} – {e['first_name']} {e['last_name']}" == raw:
                eid = e["employee_id"]; break
        if not eid:
            eid = raw.split("–")[0].strip().split(" – ")[0].strip()

        for r in self._tv2.get_children(): self._tv2.delete(r)
        recs = get_payroll_records(emp_id=eid)
        for i, rec in enumerate(recs):
            tag = "even" if i % 2 == 0 else "odd"
            self._tv2.insert("", "end", tag=tag, values=(
                MONTHS[int(rec["period_month"])],
                rec["period_year"],
                rec["cutoff"],
                rec["days_worked"],
                f"₱{rec['gross_pay']:,.2f}",
                f"₱{rec['total_deductions']:,.2f}",
                f"₱{rec['net_pay']:,.2f}"))

    def _export_payroll(self):
        from reports_export import export_payroll_excel
        m  = self._month.get(); y = int(self._year.get())
        rs = get_payroll_records(month=m, year=y)
        if not rs:
            messagebox.showinfo("No Records",
                "No payroll records to export.", parent=self); return
        try:
            path = export_payroll_excel(rs, m, y)
        except RuntimeError as e:
            messagebox.showerror("openpyxl Missing", str(e), parent=self); return
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self); return
        messagebox.showinfo("✅  Exported",
            f"Payroll report saved:\n{os.path.basename(path)}\n\n"
            f"Location: {os.path.dirname(path)}", parent=self)
        self._open(os.path.dirname(path))

    def _export_deductions(self):
        from reports_export import export_deductions_excel
        m  = self._month.get(); y = int(self._year.get())
        rs = get_payroll_records(month=m, year=y)
        if not rs:
            messagebox.showinfo("No Records",
                "No deduction records to export.", parent=self); return
        try:
            path = export_deductions_excel(rs, m, y)
        except RuntimeError as e:
            messagebox.showerror("openpyxl Missing", str(e), parent=self); return
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self); return
        messagebox.showinfo("✅  Exported",
            f"Deductions report saved:\n{os.path.basename(path)}", parent=self)
        self._open(os.path.dirname(path))

    def _open(self, folder):
        try:
            if sys.platform   == "win32": os.startfile(folder)
            elif sys.platform == "darwin": subprocess.Popen(["open", folder])
            else:                          subprocess.Popen(["xdg-open", folder])
        except Exception: pass
