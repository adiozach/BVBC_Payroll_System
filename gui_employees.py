"""
BVBC Payroll – Employee Management (Full Rewrite)
All buttons functional · Calendar date-picker working · Clean layout
"""
import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from datetime import date as _date, datetime as _dt

from database import (get_all_employees, save_employee, delete_employee,
                      permanent_delete_employee, get_employee_by_id,
                      get_connection)
from ui import C, F, page_header, button

# ── Constants ─────────────────────────────────────────────────────────────────
DEPT_SEPARATORS = [
    "── Church ──────────────",
    "── College ─────────────",
    "── Basic Education ─────",
]
DEPT_VALID = ["GBC - Church", "BVBC - College", "BVBC - Elementary"]
DEPT_OPTIONS = [
    "── Church ──────────────",
    "GBC - Church",
    "── College ─────────────",
    "BVBC - College",
    "── Basic Education ─────",
    "BVBC - Elementary",
]
EMPLOY_TYPES = [
    "Regular", "Full-time", "Full Time", "Part-time",
    "Contractual", "Casual", "Volunteer",
    "Loyalty (1)", "Loyalty (2)", "Loyalty (3)",
]
MONTHS_LONG = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


# ═════════════════════════════════════════════════════════════════════════════
# CALENDAR POPUP
# Fixed bugs:
#   1. NO grab_set on the popup — parent form owns the grab.
#      grab_set on a child Toplevel causes combobox dropdowns inside it to
#      freeze/hang because the grab blocks their internal Listbox events.
#   2. NO FocusOut binding — FocusOut fires every time a combobox inside
#      the popup opens its dropdown, which was closing the calendar.
#   3. Click-outside detection via a root-level binding on <Button-1> instead.
#   4. _mo_sel index fix — MONTHS_LONG[0]="" so index can never be 0 for a
#      valid month; removed the erroneous `or 1` fallback.
# ═════════════════════════════════════════════════════════════════════════════
class CalendarPopup(tk.Toplevel):
    """Stable floating calendar. No grab_set, no FocusOut. Click-outside closes."""

    def __init__(self, parent, var, anchor=None):
        super().__init__(parent)
        self._var      = var
        self._anchor   = anchor
        self._closed   = False          # guard double-destroy
        self._click_id = None           # root <Button-1> binding id

        self.overrideredirect(True)     # borderless
        self.configure(bg=C["m700"])
        self.resizable(False, False)

        try:
            d = _dt.strptime(var.get().strip(), "%Y-%m-%d").date()
        except Exception:
            d = _date.today()
        self._yr = d.year
        self._mo = d.month

        self._build()
        self._place()
        self.lift()
        self.focus_force()

        # Escape key closes
        self.bind("<Escape>", lambda e: self._close())

        # Click-outside detection: bind to the root window's <Button-1>.
        # We schedule it with after() so the current click (that opened the
        # calendar) does not immediately trigger it.
        root = self.winfo_toplevel().master if hasattr(self.winfo_toplevel(), "master") else self
        try:
            root = self._get_root()
            self._click_id = root.bind("<Button-1>",
                                       self._on_root_click, "+")
            self._root_ref = root
        except Exception:
            self._root_ref = None

    def _get_root(self):
        """Walk up widget tree to find the real root Tk window."""
        w = self._anchor or self
        while w.master:
            w = w.master
        return w

    def _on_root_click(self, event):
        """Close if the click is outside this popup window."""
        if self._closed:
            return
        # winfo_containing returns the widget under the cursor
        try:
            target = event.widget
            # Check if target is this popup or a descendant
            t = str(target)
            me = str(self)
            if t == me or t.startswith(me + "."):
                return          # click is inside — stay open
            # Also stay open if the click landed on a Combobox dropdown
            # (those are internal tk::combobox::popdown widgets)
            if "popdown" in t or "listbox" in t.lower():
                return
            self._close()
        except Exception:
            pass

    def _place(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        if self._anchor:
            try:
                ax = self._anchor.winfo_rootx()
                ay = self._anchor.winfo_rooty() + self._anchor.winfo_height() + 4
            except Exception:
                ax, ay = 300, 300
        else:
            ax = self.winfo_screenwidth()  // 2 - w // 2
            ay = self.winfo_screenheight() // 2 - h // 2
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        if ax + w > sw - 4:  ax = sw - w - 4
        if ax < 4:           ax = 4
        if ay + h > sh - 30:
            if self._anchor:
                ay = self._anchor.winfo_rooty() - h - 4
            else:
                ay = sh - h - 30
        if ay < 4: ay = 4
        self.geometry(f"+{ax}+{ay}")

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        today = _date.today()

        # ── Header ───────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["m700"], pady=6)
        hdr.pack(fill="x")

        def nav_btn(parent, txt, cmd):
            b = tk.Button(parent, text=txt, bg=C["m700"], fg=C["g400"],
                          font=("Segoe UI", 13, "bold"), relief="flat",
                          cursor="hand2", padx=10, pady=2,
                          activebackground=C["m500"], activeforeground=C["white"],
                          command=cmd)
            b.bind("<Enter>", lambda e: b.config(bg=C["m500"]))
            b.bind("<Leave>", lambda e: b.config(bg=C["m700"]))
            return b

        nav_btn(hdr, "◀", self._prev).pack(side="left", padx=(6, 0))

        self._mo_var = tk.StringVar(value=MONTHS_LONG[self._mo])
        mo_cb = ttk.Combobox(hdr, textvariable=self._mo_var,
                             values=MONTHS_LONG[1:], width=10,
                             state="readonly", font=("Segoe UI", 9, "bold"))
        mo_cb.pack(side="left", padx=4)
        mo_cb.bind("<<ComboboxSelected>>", self._mo_sel)

        yrs = [str(y) for y in range(today.year - 50, today.year + 11)]
        self._yr_var = tk.StringVar(value=str(self._yr))
        yr_cb = ttk.Combobox(hdr, textvariable=self._yr_var,
                             values=yrs, width=6,
                             state="readonly", font=("Segoe UI", 9, "bold"))
        yr_cb.pack(side="left", padx=4)
        yr_cb.bind("<<ComboboxSelected>>", self._yr_sel)

        nav_btn(hdr, "▶", self._next).pack(side="right", padx=(0, 6))

        # Gold separator
        tk.Frame(self, bg=C["g500"], height=3).pack(fill="x")

        # ── Day grid ─────────────────────────────────────────────────────────
        grid = tk.Frame(self, bg=C["white"], padx=5, pady=5)
        grid.pack()

        for ci, name in enumerate(["Mo","Tu","We","Th","Fr","Sa","Su"]):
            tk.Label(grid, text=name, bg=C["m800"], fg=C["g400"],
                     font=("Segoe UI", 8, "bold"), width=4, pady=5,
                     anchor="center").grid(row=0, column=ci, padx=1, pady=(0,2),
                                           sticky="nsew")

        try:
            sel = _dt.strptime(self._var.get().strip(), "%Y-%m-%d").date()
        except Exception:
            sel = None

        for ri, week in enumerate(calendar.monthcalendar(self._yr, self._mo)):
            for ci, day in enumerate(week):
                if day == 0:
                    tk.Label(grid, text="", bg=C["white"], width=4
                             ).grid(row=ri+1, column=ci, padx=1, pady=2)
                    continue
                d = _date(self._yr, self._mo, day)
                is_sel   = (sel == d)
                is_today = (d == today)
                is_sun   = (ci == 6)
                is_sat   = (ci == 5)
                if   is_sel:   bg, fg, fw = C["m600"], C["white"],  "bold"
                elif is_today: bg, fg, fw = C["g500"], C["m800"],   "bold"
                elif is_sun:   bg, fg, fw = C["white"], "#CC3333",  "normal"
                elif is_sat:   bg, fg, fw = C["white"], "#994400",  "normal"
                else:          bg, fg, fw = C["white"], C["t900"],  "normal"

                b = tk.Button(grid, text=str(day), bg=bg, fg=fg,
                              font=("Segoe UI", 9, fw),
                              width=3, pady=5, relief="flat", cursor="hand2",
                              activebackground=C["m400"],
                              activeforeground=C["white"],
                              command=lambda _d=d: self._pick(_d))
                b.grid(row=ri+1, column=ci, padx=1, pady=2, sticky="nsew")
                orig = bg
                b.bind("<Enter>", lambda e, btn=b: btn.config(bg=C["m400"]))
                b.bind("<Leave>", lambda e, btn=b, ob=orig: btn.config(bg=ob))

        # ── Footer ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        foot = tk.Frame(self, bg=C["m900"], pady=5)
        foot.pack(fill="x")
        tb = tk.Button(foot,
                       text=f"📅  Today: {today.strftime('%B %d, %Y')}",
                       bg=C["m900"], fg=C["g400"],
                       font=("Segoe UI", 8, "bold"), relief="flat",
                       cursor="hand2", padx=10, pady=4,
                       activebackground=C["m700"], activeforeground=C["white"],
                       command=lambda: self._pick(today))
        tb.pack()
        tb.bind("<Enter>", lambda e: tb.config(bg=C["m700"], fg=C["white"]))
        tb.bind("<Leave>", lambda e: tb.config(bg=C["m900"], fg=C["g400"]))

        self.config(highlightbackground=C["g500"], highlightthickness=2)

    # ── Navigation ───────────────────────────────────────────────────────────
    def _prev(self):
        self._mo -= 1
        if self._mo < 1:
            self._mo = 12
            self._yr -= 1
        self._build()
        self._place()

    def _next(self):
        self._mo += 1
        if self._mo > 12:
            self._mo = 1
            self._yr += 1
        self._build()
        self._place()

    def _mo_sel(self, _=None):
        """Month combobox changed. MONTHS_LONG[1..12] are valid months."""
        val = self._mo_var.get()
        try:
            idx = MONTHS_LONG.index(val)   # 1=Jan .. 12=Dec
            if 1 <= idx <= 12:
                self._mo = idx
        except (ValueError, IndexError):
            pass
        self._build()
        self._place()

    def _yr_sel(self, _=None):
        """Year combobox changed."""
        try:
            self._yr = int(self._yr_var.get())
        except (ValueError, TypeError):
            pass
        self._build()
        self._place()

    def _pick(self, d):
        self._var.set(d.strftime("%Y-%m-%d"))
        self._close()

    def _close(self):
        if self._closed:
            return
        self._closed = True
        # Remove the root click binding we installed
        try:
            if self._root_ref and self._click_id:
                self._root_ref.unbind("<Button-1>", self._click_id)
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


# ═════════════════════════════════════════════════════════════════════════════
# DATE PICKER ENTRY WIDGET
# ═════════════════════════════════════════════════════════════════════════════
class DatePickerEntry(tk.Frame):
    """Entry + 📅 button that opens CalendarPopup."""

    def __init__(self, parent, textvariable=None, width=13):
        super().__init__(parent, bg=C["white"], bd=0,
                        highlightbackground=C["border"],
                        highlightthickness=1)
        self._var = textvariable or tk.StringVar()

        self._entry = tk.Entry(
            self, textvariable=self._var,
            font=("Segoe UI", 10), bd=0, relief="flat",
            highlightthickness=0,
            bg=C["g100"], fg=C["m700"],
            insertbackground=C["m600"],
            width=width)
        self._entry.pack(side="left", fill="x", expand=True,
                         ipady=7, padx=(6, 0))
        self._entry.bind("<FocusOut>", self._validate)
        self._entry.bind("<Return>",   self._validate)

        tk.Frame(self, bg=C["border"], width=1).pack(side="left", fill="y")

        self._btn = tk.Button(
            self, text="📅",
            bg=C["m600"], fg=C["white"],
            font=("Segoe UI", 10), relief="flat",
            cursor="hand2", bd=0, padx=9, pady=5,
            activebackground=C["m500"],
            activeforeground=C["white"],
            command=self._open)
        self._btn.pack(side="right")
        self._btn.bind("<Enter>", lambda e: self._btn.config(bg=C["m500"]))
        self._btn.bind("<Leave>", lambda e: self._btn.config(bg=C["m600"]))

    def _open(self):
        CalendarPopup(self.winfo_toplevel(), self._var, anchor=self)

    def _validate(self, _=None):
        raw = self._var.get().strip()
        if not raw:
            self.config(highlightbackground=C["border"]); return
        fmts = ["%Y-%m-%d","%m/%d/%Y","%d/%m/%Y","%m-%d-%Y",
                "%Y/%m/%d","%d-%m-%Y","%B %d, %Y","%b %d, %Y",
                "%B %d %Y","%b %d %Y"]
        for fmt in fmts:
            try:
                self._var.set(_dt.strptime(raw, fmt).date().strftime("%Y-%m-%d"))
                self.config(highlightbackground=C["border"])
                self._entry.config(fg=C["m700"])
                return
            except ValueError:
                continue
        self.config(highlightbackground=C["err"])
        self._entry.config(fg=C["err"])

    def get(self):   return self._var.get()
    def set(self, v): self._var.set(v)


# ═════════════════════════════════════════════════════════════════════════════
# TREEVIEW HELPER
# ═════════════════════════════════════════════════════════════════════════════
def _make_tv(parent, cols, hdrs, widths, height=18, anchors=None):
    _am = {"left":"w","right":"e","center":"center","w":"w","e":"e"}
    anchors = anchors or {}
    s = ttk.Style()
    s.configure("BV.Treeview", font=F["body"], rowheight=28,
                background=C["white"], fieldbackground=C["white"],
                foreground=C["t900"], borderwidth=0)
    s.configure("BV.Treeview.Heading", font=F["label"],
                background=C["m600"], foreground=C["white"],
                relief="flat", padding=7)
    s.map("BV.Treeview",
          background=[("selected", C["g300"])],
          foreground=[("selected", C["m700"])])
    s.map("BV.Treeview.Heading",
          background=[("active", C["m500"])])

    fr = tk.Frame(parent, bg=C["bg"])
    tv = ttk.Treeview(fr, columns=cols, show="headings",
                      height=height, style="BV.Treeview")
    for col, h, w in zip(cols, hdrs, widths):
        tv.heading(col, text=h)
        tv.column(col, width=w,
                  anchor=_am.get(str(anchors.get(col,"center")).lower(),"center"),
                  stretch=(col==cols[-1]))
    vsb = ttk.Scrollbar(fr, orient="vertical",   command=tv.yview)
    hsb = ttk.Scrollbar(fr, orient="horizontal",  command=tv.xview)
    tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tv.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    fr.grid_rowconfigure(0, weight=1)
    fr.grid_columnconfigure(0, weight=1)
    tv.tag_configure("odd",  background=C["g100"])
    tv.tag_configure("even", background=C["white"])
    return fr, tv


# ═════════════════════════════════════════════════════════════════════════════
# EMPLOYEES PAGE
# ═════════════════════════════════════════════════════════════════════════════
class EmployeesPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.pack(fill="both", expand=True)
        self.app   = app
        self._tv   = None
        self._info = None
        self._build()

    def _build(self):
        page_header(self, "👥  Employee Management",
                    "Add · Edit · View · Deactivate · Permanently Delete")

        # ── Toolbar ──────────────────────────────────────────────────────────
        tb = tk.Frame(self, bg=C["white"], padx=12, pady=9,
                      highlightbackground=C["border"], highlightthickness=1)
        tb.pack(fill="x")

        def vsep():
            tk.Frame(tb, bg=C["border"], width=1
                     ).pack(side="left", fill="y", padx=6)

        button(tb, "Add Employee", "primary", self._add,
               icon="➕", px=12, py=7).pack(side="left", padx=3)
        button(tb, "Edit",         "gold",    self._edit,
               icon="✏️", px=12, py=7).pack(side="left", padx=3)
        button(tb, "View Info",    "info",    self._view,
               icon="👁",  px=12, py=7).pack(side="left", padx=3)
        vsep()
        button(tb, "Deactivate",   "danger",  self._deactivate,
               icon="🔒", px=12, py=7).pack(side="left", padx=3)
        button(tb, "Reactivate",   "success", self._reactivate,
               icon="✅", px=12, py=7).pack(side="left", padx=3)
        vsep()

        pd = tk.Button(tb, text="⛔  Perm. Delete",
                       bg="#7A0000", fg=C["white"],
                       font=("Segoe UI", 10, "bold"), relief="flat",
                       cursor="hand2", padx=12, pady=7,
                       activebackground="#5A0000",
                       command=self._perm_delete)
        pd.pack(side="left", padx=3)
        pd.bind("<Enter>", lambda e: pd.config(bg="#5A0000"))
        pd.bind("<Leave>", lambda e: pd.config(bg="#7A0000"))

        # Search + filter
        tk.Frame(tb, bg=C["white"]).pack(side="left", fill="x", expand=True)
        tk.Label(tb, text="🔍", bg=C["white"],
                 fg=C["t600"], font=("Segoe UI", 12)).pack(side="left", padx=(0,4))
        self._sv = tk.StringVar()
        self._sv.trace("w", lambda *_: self._refresh())
        tk.Entry(tb, textvariable=self._sv, font=F["body"], width=20,
                 bd=0, highlightthickness=1,
                 highlightbackground=C["border"],
                 highlightcolor=C["g500"], bg=C["g100"]
                 ).pack(side="left", padx=4, ipady=5)
        tk.Label(tb, text="Filter:", bg=C["white"],
                 fg=C["t600"], font=F["label"]).pack(side="left", padx=(10,4))
        self._st = tk.StringVar(value="All")
        cb = ttk.Combobox(tb, textvariable=self._st,
                          values=["All","Active","Inactive"],
                          width=10, state="readonly", font=F["body"])
        cb.pack(side="left", padx=4, ipady=3)
        cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # ── Split pane ────────────────────────────────────────────────────────
        split = tk.PanedWindow(self, orient="horizontal",
                               bg=C["border"], sashwidth=5)
        split.pack(fill="both", expand=True, padx=14, pady=(8,4))

        left = tk.Frame(split, bg=C["bg"])
        split.add(left, minsize=540)

        cols   = ("id","name","dept","pos","type","salary","status")
        hdrs   = ["Emp ID","Full Name","Department",
                  "Position","Type","Monthly Salary","Status"]
        widths = [88,200,140,150,100,130,78]
        ancs   = {"id":"center","name":"w","dept":"w","pos":"w",
                  "type":"center","salary":"e","status":"center"}
        tf, self._tv = _make_tv(left, cols, hdrs, widths,
                                  height=20, anchors=ancs)
        tf.pack(fill="both", expand=True)
        self._tv.bind("<<TreeviewSelect>>", self._on_sel)
        self._tv.bind("<Double-1>", lambda e: self._edit())

        right = tk.Frame(split, bg=C["white"])
        split.add(right, minsize=300)
        self._build_detail(right)

        self._info = tk.Label(self, text="", bg=C["bg"],
                              fg=C["t400"], font=F["small"])
        self._info.pack(anchor="w", padx=18, pady=(0,5))
        self._refresh()

    # ── Detail panel ──────────────────────────────────────────────────────────
    def _build_detail(self, parent):
        tk.Frame(parent, bg=C["m700"], height=5).pack(fill="x")
        tk.Label(parent, text="👤  Employee Profile",
                 bg=C["white"], fg=C["m700"],
                 font=F["h2"], padx=14, pady=10).pack(anchor="w")
        tk.Frame(parent, bg=C["g500"], height=2).pack(fill="x", padx=14)
        cv  = tk.Canvas(parent, bg=C["white"], highlightthickness=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); cv.pack(fill="both", expand=True)
        self._db = tk.Frame(cv, bg=C["white"], padx=16, pady=10)
        self._dw = cv.create_window((0,0), window=self._db, anchor="nw")
        self._db.bind("<Configure>",
            lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",
            lambda e: cv.itemconfig(self._dw, width=e.width))
        tk.Label(self._db,
                 text="← Select an employee\nto view their profile",
                 bg=C["white"], fg=C["t400"],
                 font=F["body"], justify="center").pack(expand=True, pady=40)

    # ── Refresh ───────────────────────────────────────────────────────────────
    def _refresh(self):
        if self._tv is None: return
        for r in self._tv.get_children(): self._tv.delete(r)
        emps = get_all_employees(self._sv.get(), self._st.get())
        for i, e in enumerate(emps):
            tag = "even" if i%2==0 else "odd"
            self._tv.insert("","end", iid=e["employee_id"], tag=tag, values=(
                e["employee_id"],
                f"{e['last_name']}, {e['first_name']}",
                e["department"]      or "—",
                e["position"]        or "—",
                e["employment_type"] or "—",
                f"₱ {e['monthly_salary']:,.2f}",
                e["status"]))
        if self._info:
            act = sum(1 for e in emps if e["status"]=="Active")
            ina = len(emps) - act
            self._info.config(
                text=f"  {len(emps)} employee(s)  ·  Active: {act}  ·  "
                     f"Inactive: {ina}  ·  Double-click to edit")
        self._show_detail(None)

    # ── Selection ─────────────────────────────────────────────────────────────
    def _on_sel(self, _=None):
        sel = self._tv.selection()
        if sel: self._show_detail(sel[0])

    def _sel_id(self):
        s = self._tv.selection()
        if not s:
            messagebox.showinfo("No Selection",
                "Click an employee row first.", parent=self)
            return None
        return s[0]

    # ── Detail content ────────────────────────────────────────────────────────
    def _show_detail(self, eid):
        for w in self._db.winfo_children(): w.destroy()
        if not eid:
            tk.Label(self._db,
                     text="← Select an employee\nto view their profile",
                     bg=C["white"], fg=C["t400"],
                     font=F["body"], justify="center").pack(expand=True, pady=40)
            return
        emp = get_employee_by_id(eid)
        if not emp: return

        nf = tk.Frame(self._db, bg=C["m700"], padx=14, pady=12)
        nf.pack(fill="x", pady=(0,10))
        st_c = C["ok"] if emp["status"]=="Active" else C["err"]
        tk.Label(nf, text=f"  {emp['status']}  ",
                 bg=st_c, fg=C["white"],
                 font=("Segoe UI",8,"bold"), pady=3).pack(anchor="e")
        clr = C["gold"] if emp["status"]=="Active" else "#EF9A9A"
        tk.Label(nf, text=f"{emp['first_name']} {emp['last_name']}",
                 bg=C["m700"], fg=clr,
                 font=("Segoe UI",13,"bold")).pack(anchor="w")
        tk.Label(nf, text=emp["position"]   or "—",
                 bg=C["m700"], fg=C["g400"], font=("Segoe UI",9)).pack(anchor="w")
        tk.Label(nf, text=emp["department"] or "—",
                 bg=C["m700"], fg=C["white"],font=("Segoe UI",9)).pack(anchor="w")

        def sec(t):
            f=tk.Frame(self._db,bg=C["white"]); f.pack(fill="x",pady=(10,0))
            tk.Label(f,text=t,bg=C["white"],fg=C["m700"],font=F["h3"]).pack(anchor="w")
            tk.Frame(f,bg=C["g500"],height=2).pack(fill="x",pady=(2,6))

        def row(lbl, val, hi=False):
            rf=tk.Frame(self._db,bg=C["g100"] if hi else C["white"]); rf.pack(fill="x",pady=1)
            tk.Label(rf,text=lbl,bg=rf["bg"],fg=C["t600"],
                     font=("Segoe UI",9,"bold"),width=18,anchor="w"
                     ).pack(side="left",padx=(8,4),pady=4)
            tk.Label(rf,text=str(val or "—"),bg=rf["bg"],fg=C["t900"],
                     font=("Segoe UI",9),anchor="w",wraplength=160
                     ).pack(side="left",padx=(0,8),pady=4)

        sec("📋  Employment")
        row("Employee ID", emp["employee_id"],       hi=True)
        row("Type",        emp["employment_type"])
        row("Hire Date",   emp["hire_date"],          hi=True)
        row("Status",      emp["status"])

        sec("💰  Salary")
        ms = float(emp["monthly_salary"] or 0)
        dr = float(emp["daily_rate"] or (ms/22 if ms else 0))
        row("Monthly",    f"₱ {ms:,.2f}", hi=True)
        row("Daily Rate", f"₱ {dr:,.2f}")

        sec("📞  Contact")
        row("Contact No.",   emp.get("contact_no"),hi=True)
        row("Email",         emp.get("email"))
        row("Address",       emp.get("address"),   hi=True)

        sec("🏛️  Gov Numbers")
        row("SSS No.",       emp["sss_no"],        hi=True)
        row("PhilHealth No.",emp["philhealth_no"])
        row("Pag-IBIG No.",  emp["pagibig_no"],    hi=True)
        row("TIN No.",       emp["tin_no"])

        sec("📊  Est. Deductions")
        from computation import compute_sss, compute_philhealth, compute_pagibig
        sss=compute_sss(ms); ph=compute_philhealth(ms); pig=compute_pagibig(ms)
        row("SSS",       f"₱ {sss:,.2f}", hi=True)
        row("PhilHealth",f"₱ {ph:,.2f}")
        row("Pag-IBIG",  f"₱ {pig:,.2f}", hi=True)
        row("Total Ded.",f"₱ {sss+ph+pig:,.2f}")

        # Action buttons
        bf = tk.Frame(self._db, bg=C["white"]); bf.pack(fill="x", pady=(14,4))
        button(bf,"Edit","primary",
               lambda e=eid: self._edit_direct(e),
               icon="✏️",px=10,py=6).pack(side="left",padx=(0,4))
        if emp["status"]=="Active":
            button(bf,"Deactivate","danger",
                   lambda e=eid: self._deactivate_direct(e),
                   icon="🔒",px=10,py=6).pack(side="left",padx=3)
        else:
            button(bf,"Reactivate","success",
                   lambda e=eid: self._reactivate_direct(e),
                   icon="✅",px=10,py=6).pack(side="left",padx=3)
        pdb=tk.Button(bf,text="⛔  Delete",bg="#7A0000",fg=C["white"],
                      font=("Segoe UI",9,"bold"),relief="flat",cursor="hand2",
                      padx=10,pady=6,activebackground="#5A0000",
                      command=lambda e=eid: self._perm_delete_direct(e))
        pdb.pack(side="left",padx=3)
        pdb.bind("<Enter>",lambda ev:pdb.config(bg="#5A0000"))
        pdb.bind("<Leave>",lambda ev:pdb.config(bg="#7A0000"))

    # ── Actions ───────────────────────────────────────────────────────────────
    def _add(self):          EmployeeForm(self, None, self._refresh)
    def _edit(self):
        e=self._sel_id();
        if e: EmployeeForm(self, e, self._refresh)
    def _edit_direct(self,e): EmployeeForm(self, e, self._refresh)
    def _view(self):
        e=self._sel_id();
        if e: EmployeeDetailWindow(self, e)

    def _deactivate(self):
        e=self._sel_id()
        if e: self._deactivate_direct(e)

    def _deactivate_direct(self, eid):
        emp=get_employee_by_id(eid)
        name=f"{emp['first_name']} {emp['last_name']}" if emp else eid
        if messagebox.askyesno("Confirm Deactivate",
                f"Deactivate  {name}?\n\nThey will be excluded from active payroll.\n"
                "You can reactivate them later.", parent=self):
            delete_employee(eid); self._refresh()

    def _reactivate(self):
        e=self._sel_id()
        if e: self._reactivate_direct(e)

    def _reactivate_direct(self, eid):
        conn=get_connection()
        conn.execute("UPDATE employees SET status='Active' WHERE employee_id=?",(eid,))
        conn.commit(); conn.close()
        self._refresh()
        messagebox.showinfo("✅  Reactivated",
            f"Employee {eid} is now Active.", parent=self)

    def _perm_delete(self):
        e=self._sel_id()
        if e: self._perm_delete_direct(e)

    def _perm_delete_direct(self, eid):
        emp=get_employee_by_id(eid)
        if not emp:
            messagebox.showerror("Error","Employee not found.",parent=self); return
        name=f"{emp['first_name']} {emp['last_name']}"
        conn=get_connection()
        pc=conn.execute("SELECT COUNT(*) FROM payroll WHERE employee_id=?",(eid,)).fetchone()[0]
        conn.close()
        PermanentDeleteDialog(self, eid, name, pc, self._do_perm_delete)

    def _do_perm_delete(self, eid):
        emp=get_employee_by_id(eid)
        if not emp: return
        name=f"{emp['first_name']} {emp['last_name']}"
        result=permanent_delete_employee(eid)
        self._refresh()
        messagebox.showinfo("🗑️  Permanently Deleted",
            f"{name}  ({eid})  permanently removed.\n\n"
            f"Payroll records deleted : {result['payroll_deleted']}\n"
            f"Attendance records      : {result['attendance_deleted']}",
            parent=self)


# ═════════════════════════════════════════════════════════════════════════════
# PERMANENT DELETE DIALOG
# ═════════════════════════════════════════════════════════════════════════════
class PermanentDeleteDialog(tk.Toplevel):
    def __init__(self, parent, emp_id, emp_name, payroll_count, on_confirm):
        super().__init__(parent)
        self._eid=emp_id; self._name=emp_name
        self._pc=payroll_count; self._ok=on_confirm
        self.title("⛔  Permanent Delete")
        self.resizable(False, False)
        self.configure(bg=C["white"])
        self._build()
        self.update_idletasks()
        w,h=520,620
        x=(self.winfo_screenwidth()-w)//2; y=(self.winfo_screenheight()-h)//2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.grab_set()
        self._entry.focus_set()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        # Row 0: header
        hdr=tk.Frame(self,bg="#7A0000",height=58)
        hdr.grid(row=0,column=0,sticky="ew"); hdr.pack_propagate(False)
        tk.Label(hdr,text="⛔  PERMANENT DELETE WARNING",
                 bg="#7A0000",fg=C["white"],
                 font=("Segoe UI",13,"bold")).place(x=18,rely=0.5,anchor="w")
        # Row 1: gold bar
        tk.Frame(self,bg=C["g500"],height=3).grid(row=1,column=0,sticky="ew")
        # Row 2: warning box
        warn=tk.Frame(self,bg="#FFF0F0",
                      highlightbackground="#CC0000",highlightthickness=2)
        warn.grid(row=2,column=0,sticky="ew",padx=22,pady=(16,0))
        tk.Label(warn,text="⚠️",bg="#FFF0F0",font=("Segoe UI",24)).pack(pady=(12,2))
        tk.Label(warn,text="This action is PERMANENT and CANNOT be undone!",
                 bg="#FFF0F0",fg="#7A0000",
                 font=("Segoe UI",11,"bold")).pack()
        tk.Label(warn,text="All data below will be erased forever:",
                 bg="#FFF0F0",fg=C["t600"],
                 font=("Segoe UI",9)).pack(pady=(3,12))
        # Row 3: info table
        info=tk.Frame(self,bg=C["bg2"],
                      highlightbackground=C["border"],highlightthickness=1)
        info.grid(row=3,column=0,sticky="ew",padx=22,pady=(10,0))
        def ir(icon,lbl,val,bold=False):
            rf=tk.Frame(info,bg=C["bg2"]); rf.pack(fill="x",padx=14,pady=5)
            tk.Label(rf,text=icon,bg=C["bg2"],font=("Segoe UI",12),
                     width=3).pack(side="left")
            tk.Label(rf,text=lbl,bg=C["bg2"],fg=C["t600"],
                     font=("Segoe UI",10),width=22,
                     anchor="w").pack(side="left",padx=(4,0))
            tk.Label(rf,text=str(val),bg=C["bg2"],
                     fg="#7A0000" if bold else C["t900"],
                     font=("Segoe UI",10,"bold" if bold else "normal"),
                     anchor="w").pack(side="left",padx=(6,0))
        ir("👤","Employee:",          self._name, bold=True)
        ir("🆔","Employee ID:",       self._eid,  bold=True)
        ir("💰","Payroll records:",   f"{self._pc} record(s) will be deleted")
        ir("📋","Attendance records:","All records will be deleted")
        ir("👥","Employee profile:",  "Permanently removed from system")
        # Row 4: divider
        tk.Frame(self,bg=C["border"],height=1).grid(
            row=4,column=0,sticky="ew",padx=22,pady=(14,0))
        # Row 5: label
        tk.Label(self,text=f'Type the Employee ID  "{self._eid}"  to confirm:',
                 bg=C["white"],fg=C["t600"],
                 font=("Segoe UI",10,"bold"),anchor="w"
                 ).grid(row=5,column=0,sticky="ew",padx=22,pady=(12,0))
        # Row 6: entry
        self._cv=tk.StringVar(); self._cv.trace("w",self._on_type)
        self._entry=tk.Entry(self,textvariable=self._cv,
                             font=("Segoe UI",13,"bold"),
                             bd=0,highlightthickness=2,
                             highlightbackground="#CC0000",
                             highlightcolor=C["ok"],
                             bg="#FFF5F5",fg="#7A0000",justify="center")
        self._entry.grid(row=6,column=0,sticky="ew",
                         padx=22,pady=(6,0),ipady=9)
        self._entry.bind("<Return>",self._try_delete)
        # Row 7: validation label
        self._vlbl=tk.Label(self,text="",bg=C["white"],
                            font=("Segoe UI",9),anchor="w")
        self._vlbl.grid(row=7,column=0,sticky="ew",padx=22,pady=(4,0))
        # Row 8: spacer
        tk.Frame(self,bg=C["white"],height=8).grid(row=8,column=0)
        # Row 9: button bar
        bar=tk.Frame(self,bg="#2A0000")
        bar.grid(row=9,column=0,sticky="ew")
        cancel=tk.Button(bar,text="✖  Cancel",bg="#555",fg=C["white"],
                         font=("Segoe UI",10,"bold"),relief="flat",
                         cursor="hand2",padx=20,pady=12,
                         activebackground="#333",command=self.destroy)
        cancel.pack(side="left",padx=(16,0),pady=12)
        cancel.bind("<Enter>",lambda e:cancel.config(bg="#333"))
        cancel.bind("<Leave>",lambda e:cancel.config(bg="#555"))
        self._del=tk.Button(bar,text="⛔  YES, PERMANENTLY DELETE",
                            bg="#3A0000",fg="#888",
                            font=("Segoe UI",11,"bold"),relief="flat",
                            cursor="arrow",padx=20,pady=12,state="disabled",
                            activebackground="#CC0000",activeforeground=C["white"],
                            command=self._try_delete)
        self._del.pack(side="right",padx=(0,16),pady=12)

    def _on_type(self,*_):
        typed=self._cv.get().strip()
        if typed==self._eid:
            self._del.config(state="normal",bg="#CC0000",fg=C["white"],cursor="hand2")
            self._del.bind("<Enter>",lambda e:self._del.config(bg="#FF0000"))
            self._del.bind("<Leave>",lambda e:self._del.config(bg="#CC0000"))
            self._vlbl.config(text="✅  ID confirmed — click DELETE to proceed.",fg=C["ok"])
            self._entry.config(highlightbackground=C["ok"])
        else:
            self._del.config(state="disabled",bg="#3A0000",fg="#888",cursor="arrow")
            self._entry.config(highlightbackground="#CC0000")
            self._vlbl.config(
                text="❌  ID does not match..." if typed else "",fg=C["err"])

    def _try_delete(self,_=None):
        if self._cv.get().strip()!=self._eid:
            messagebox.showerror("ID Mismatch",
                f'Typed ID does not match "{self._eid}".',parent=self); return
        self.destroy(); self._ok(self._eid)


# ═════════════════════════════════════════════════════════════════════════════
# EMPLOYEE DETAIL WINDOW  — grid-only, no Canvas, no Text embedding
# Uses grid geometry on root + inner scrollable listbox of label pairs
# ═════════════════════════════════════════════════════════════════════════════
class EmployeeDetailWindow(tk.Toplevel):
    def __init__(self, parent, emp_id):
        super().__init__(parent)
        emp = get_employee_by_id(emp_id)
        if not emp:
            self.destroy()
            return

        name = f"{emp['first_name']} {emp['last_name']}"
        self.title(f"Profile – {name}")
        self.resizable(True, True)
        self.configure(bg=C["white"])
        W, H = 660, 740
        x = (self.winfo_screenwidth()  - W) // 2
        y = (self.winfo_screenheight() - H) // 2
        self.geometry(f"{W}x{H}+{x}+{y}")
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build(emp)
        self.grab_set()
        self.focus_set()

    def _build(self, emp):
        from computation import compute_sss, compute_philhealth, compute_pagibig
        from database import get_payroll_records
        from ui import MONTHS

        ms      = float(emp["monthly_salary"] or 0)
        dr      = float(emp["daily_rate"] or (ms / 22 if ms else 0))
        sss     = compute_sss(ms)
        ph      = compute_philhealth(ms)
        pig     = compute_pagibig(ms)
        net_est = ms - sss - ph - pig
        recs    = get_payroll_records(emp_id=emp["employee_id"])

        # Row 0 — header
        hdr = tk.Frame(self, bg=C["m700"], height=62)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        n = " ".join(filter(None, [
            emp["first_name"], emp.get("middle_name") or "", emp["last_name"]
        ])).strip()
        tk.Label(hdr, text=f"  👤  {n}",
                 bg=C["m700"], fg=C["white"],
                 font=("Segoe UI", 13, "bold")).place(x=14, rely=0.38, anchor="w")
        tk.Label(hdr,
                 text=f"  {emp.get('position') or ''}  |  {emp.get('department') or ''}",
                 bg=C["m700"], fg=C["g400"],
                 font=("Segoe UI", 9)).place(x=14, rely=0.72, anchor="w")
        st_bg = C["ok"] if emp["status"] == "Active" else C["err"]
        tk.Label(hdr, text=f"  {emp['status']}  ",
                 bg=st_bg, fg=C["white"],
                 font=("Segoe UI", 9, "bold"), pady=3
                 ).place(relx=1.0, rely=0.5, anchor="e", x=-14)

        # Row 1 — gold bar
        tk.Frame(self, bg=C["g500"], height=3).grid(row=1, column=0, sticky="ew")

        # Row 2 — scrollable content (fills remaining space)
        scroll_frame = tk.Frame(self, bg=C["white"])
        scroll_frame.grid(row=2, column=0, sticky="nsew")
        scroll_frame.grid_rowconfigure(0, weight=1)
        scroll_frame.grid_columnconfigure(0, weight=1)

        vsb = ttk.Scrollbar(scroll_frame, orient="vertical")
        vsb.grid(row=0, column=1, sticky="ns")

        # The canvas holds the inner frame — standard Tkinter scroll pattern
        cv = tk.Canvas(scroll_frame, bg=C["white"],
                       yscrollcommand=vsb.set, highlightthickness=0)
        cv.grid(row=0, column=0, sticky="nsew")
        vsb.config(command=cv.yview)

        inner = tk.Frame(cv, bg=C["white"])
        inner_id = cv.create_window((0, 0), window=inner, anchor="nw")

        # Keep inner frame width = canvas width
        def _cv_resize(e):
            cv.itemconfig(inner_id, width=e.width)
        cv.bind("<Configure>", _cv_resize)

        # Update scroll region when inner frame changes size
        def _inner_resize(e):
            cv.configure(scrollregion=cv.bbox("all"))
        inner.bind("<Configure>", _inner_resize)

        # Mousewheel
        def _wheel(e):
            cv.yview_scroll(int(-1*(e.delta/120)), "units")
        cv.bind("<MouseWheel>",    _wheel)
        inner.bind("<MouseWheel>", _wheel)

        # Row 3 — separator
        tk.Frame(self, bg=C["border"], height=1).grid(row=3, column=0, sticky="ew")

        # Row 4 — button bar
        bf = tk.Frame(self, bg=C["white"], pady=10)
        bf.grid(row=4, column=0, sticky="ew")
        button(bf, "Close", "ghost", self.destroy,
               px=20, py=8).pack(side="right", padx=14)
        button(bf, "Edit Employee", "primary",
               lambda: (self.destroy(),
                        EmployeeForm(self.master, emp["employee_id"], lambda: None)),
               icon="✏️", px=16, py=8).pack(side="right", padx=4)

        # ── Content helpers ───────────────────────────────────────────────────
        def sec(title):
            f = tk.Frame(inner, bg=C["m700"])
            f.pack(fill="x", pady=(10, 0))
            tk.Label(f, text=f"  {title}",
                     bg=C["m700"], fg=C["white"],
                     font=("Segoe UI", 10, "bold"), pady=6
                     ).pack(side="left", padx=4)

        def row(lbl, val, alt=False):
            bg = C["g100"] if alt else C["white"]
            rf = tk.Frame(inner, bg=bg)
            rf.pack(fill="x")
            tk.Label(rf, text=lbl, bg=bg, fg=C["t600"],
                     font=("Segoe UI", 9, "bold"),
                     width=22, anchor="w"
                     ).pack(side="left", padx=(14, 6), pady=5)
            tk.Label(rf, text=str(val) if val else "—",
                     bg=bg, fg=C["t900"], font=("Segoe UI", 9),
                     anchor="w", wraplength=420
                     ).pack(side="left", padx=(0, 14), pady=5,
                            fill="x", expand=True)
            rf.bind("<MouseWheel>",
                    lambda e: cv.yview_scroll(int(-1*(e.delta/120)),"units"))

        def money_row(lbl, amount, bgc, fgc):
            f = tk.Frame(inner, bg=bgc)
            f.pack(fill="x", pady=(1, 0))
            tk.Label(f, text=f"  {lbl}", bg=bgc, fg=C["g400"],
                     font=("Segoe UI", 9, "bold")
                     ).pack(side="left", padx=14, pady=6)
            tk.Label(f, text=f"₱ {amount:,.2f}  ", bg=bgc, fg=fgc,
                     font=("Segoe UI", 11, "bold")
                     ).pack(side="right", padx=14, pady=6)

        # ── Section 1: Identity & Employment ─────────────────────────────────
        sec("🪪  Identity & Employment")
        row("Employee ID",     emp["employee_id"],                            alt=True)
        row("Full Name",       n)
        row("Department",      emp["department"],                             alt=True)
        row("Position",        emp["position"])
        row("Employment Type", emp["employment_type"],                        alt=True)
        row("Hire Date",       emp["hire_date"])
        row("Status",          emp["status"],                                 alt=True)

        # ── Section 2: Contact Details ────────────────────────────────────────
        sec("📞  Contact Details")
        row("Contact Number",  emp.get("contact_no"),                        alt=True)
        row("Email Address",   emp.get("email"))
        row("Address",         emp.get("address"),                           alt=True)

        # ── Section 3: Salary ─────────────────────────────────────────────────
        sec("💰  Salary & Compensation")
        row("Monthly Salary",  f"₱ {ms:,.2f}",                         alt=True)
        row("Daily Rate",      f"₱ {dr:,.2f}")
        row("Hourly Rate",     f"₱ {dr/8:,.4f}",                        alt=True)

        # ── Section 4: Statutory Deductions ───────────────────────────────────
        sec("📊  Statutory Deductions (Monthly)")
        row("SSS",             f"₱ {sss:,.2f}",                        alt=True)
        row("PhilHealth",      f"₱ {ph:,.2f}")
        row("Pag-IBIG",        f"₱ {pig:,.2f}",                        alt=True)
        row("Total Deductions",f"₱ {sss+ph+pig:,.2f}")
        clr = C["gold"] if emp["status"] == "Active" else "#EF9A9A"
        money_row("Estimated Net Pay (Monthly)", net_est, C["m600"], clr)

        # ── Section 5: Government Numbers ─────────────────────────────────────
        sec("🏛️  Government Numbers")
        row("SSS No.",         emp["sss_no"],                                alt=True)
        row("PhilHealth No.",  emp["philhealth_no"])
        row("Pag-IBIG No.",    emp["pagibig_no"],                            alt=True)
        row("TIN No.",         emp["tin_no"])

        # ── Section 6: Payroll History ────────────────────────────────────────
        sec("📁  Payroll History")
        row("Total Records",  str(len(recs)),                                alt=True)
        if recs:
            tot = sum(r["net_pay"] for r in recs)
            lat = recs[-1]
            row("Total Net Paid",  f"₱ {tot:,.2f}")
            row("Latest Period",
                f"{MONTHS[int(lat['period_month'])]} {lat['period_year']}",  alt=True)
            row("Last Net Pay",    f"₱ {lat['net_pay']:,.2f}")

        tk.Frame(inner, bg=C["white"], height=20).pack()


# ═════════════════════════════════════════════════════════════════════════════
# EMPLOYEE ADD / EDIT FORM
# ═════════════════════════════════════════════════════════════════════════════
class EmployeeForm(tk.Toplevel):
    def __init__(self, parent, emp_id, on_save):
        super().__init__(parent)
        self._eid=emp_id; self._on_save=on_save
        self.title("Edit Employee" if emp_id else "Add New Employee")
        self.geometry("680x800"); self.minsize(600,700)
        self.configure(bg=C["white"])
        self._vars={}
        x=(self.winfo_screenwidth()-680)//2; y=(self.winfo_screenheight()-800)//2
        self.geometry(f"680x800+{x}+{y}")
        self._build()
        if emp_id: self._load(emp_id)
        self.grab_set(); self.focus_set()

    def _sec(self,p,t,top=14):
        f=tk.Frame(p,bg=C["white"]); f.pack(fill="x",pady=(top,0))
        tk.Label(f,text=t,bg=C["white"],fg=C["m700"],font=F["h3"]).pack(anchor="w")
        tk.Frame(f,bg=C["g500"],height=2).pack(fill="x",pady=(2,8))

    def _lbl(self,p,t,r,c):
        tk.Label(p,text=t,bg=C["white"],fg=C["t600"],font=F["label"]
                 ).grid(row=r*2,column=c*2,sticky="w",pady=(10,0),padx=(0,10))

    def _ent(self,p,r,c,lbl,key,w=22,ro=False):
        self._lbl(p,lbl,r,c)
        var=tk.StringVar()
        e=tk.Entry(p,textvariable=var,font=F["body"],width=w,bd=0,
                   highlightthickness=1,highlightbackground=C["border"],
                   highlightcolor=C["g500"],
                   readonlybackground=C["bg2"],
                   bg=C["bg2"] if ro else C["g100"],
                   state="readonly" if ro else "normal")
        e.grid(row=r*2+1,column=c*2,sticky="ew",pady=(2,0),padx=(0,10),ipady=6)
        self._vars[key]=var; return var

    def _build(self):
        hdr=tk.Frame(self,bg=C["m700"],height=58)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        title="✏️  Edit Employee" if self._eid else "➕  Add New Employee"
        tk.Label(hdr,text=f"  {title}",bg=C["m700"],fg=C["white"],
                 font=F["h1"]).place(x=14,rely=0.5,anchor="w")
        tk.Frame(self,bg=C["g500"],height=4).pack(fill="x")
        cv=tk.Canvas(self,bg=C["white"],highlightthickness=0)
        vsb=ttk.Scrollbar(self,orient="vertical",command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right",fill="y"); cv.pack(fill="both",expand=True)
        body=tk.Frame(cv,bg=C["white"],padx=28,pady=14)
        win=cv.create_window((0,0),window=body,anchor="nw")
        body.bind("<Configure>",lambda e:cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",lambda e:cv.itemconfig(win,width=e.width))

        # Identity
        self._sec(body,"🪪  Employee Identity",top=4)
        g1=tk.Frame(body,bg=C["white"]); g1.pack(fill="x")
        self._ent(g1,0,0,"Employee ID (auto)","employee_id",w=18,ro=True)
        self._lbl(g1,"Status",0,1)
        self._vars["status"]=tk.StringVar(value="Active")
        ttk.Combobox(g1,textvariable=self._vars["status"],
                     values=["Active","Inactive"],width=14,state="readonly",font=F["body"]
                     ).grid(row=1,column=2,sticky="ew",pady=(2,0),padx=(0,10),ipady=5)
        g1.grid_columnconfigure(0,weight=1); g1.grid_columnconfigure(2,weight=1)
        g2=tk.Frame(body,bg=C["white"]); g2.pack(fill="x")
        self._ent(g2,0,0,"First Name *","first_name",w=22)
        self._ent(g2,0,1,"Last Name *","last_name",w=22)
        self._ent(g2,1,0,"Middle Name","middle_name",w=22)
        g2.grid_columnconfigure(0,weight=1); g2.grid_columnconfigure(2,weight=1)

        # Contact Details — moved here below Identity
        self._sec(body,"📞  Contact Details")
        g7=tk.Frame(body,bg=C["white"]); g7.pack(fill="x")
        self._ent(g7,0,0,"Contact Number","contact_no",w=22)
        self._ent(g7,0,1,"Email Address","email",w=22)
        g7.grid_columnconfigure(0,weight=1); g7.grid_columnconfigure(2,weight=1)

        # Address — full width
        tk.Label(body,text="Home / Mailing Address",bg=C["white"],
                 fg=C["t600"],font=F["label"]).pack(anchor="w",pady=(10,0))
        self._vars["address"]=tk.StringVar()
        addr_entry=tk.Entry(body,textvariable=self._vars["address"],
                            font=F["body"],bd=0,
                            highlightthickness=1,
                            highlightbackground=C["border"],
                            highlightcolor=C["g500"],
                            bg=C["g100"])
        addr_entry.pack(fill="x",ipady=7,pady=(2,0))

        # Employment
        self._sec(body,"📋  Employment Details")
        g3=tk.Frame(body,bg=C["white"]); g3.pack(fill="x")
        self._lbl(g3,"Department *",0,0)
        self._vars["department"]=tk.StringVar()
        dc=ttk.Combobox(g3,textvariable=self._vars["department"],
                        values=DEPT_OPTIONS,width=26,
                        font=("Segoe UI",10,"bold"),state="readonly")
        dc.grid(row=1,column=0,sticky="ew",pady=(2,0),padx=(0,10),ipady=6)
        def _gd(e,var=self._vars["department"],cb=dc):
            if var.get() in DEPT_SEPARATORS: var.set(""); cb.set("")
        dc.bind("<<ComboboxSelected>>",_gd)
        self._ent(g3,0,1,"Position","position",w=22)
        g3.grid_columnconfigure(0,weight=1); g3.grid_columnconfigure(2,weight=1)
        g4=tk.Frame(body,bg=C["white"]); g4.pack(fill="x")
        self._lbl(g4,"Employment Type",0,0)
        self._vars["employment_type"]=tk.StringVar(value="Regular")
        ttk.Combobox(g4,textvariable=self._vars["employment_type"],
                     values=EMPLOY_TYPES,width=20,state="readonly",font=F["body"]
                     ).grid(row=1,column=0,sticky="ew",pady=(2,0),padx=(0,10),ipady=5)
        # Hire Date — DatePickerEntry
        self._lbl(g4,"Hire Date",0,1)
        self._vars["hire_date"]=tk.StringVar()
        dpf=tk.Frame(g4,bg=C["white"])
        dpf.grid(row=1,column=2,sticky="ew",pady=(2,0),padx=(0,10))
        DatePickerEntry(dpf,textvariable=self._vars["hire_date"],width=13).pack(fill="x")
        g4.grid_columnconfigure(0,weight=1); g4.grid_columnconfigure(2,weight=1)

        # Salary
        self._sec(body,"💰  Salary")
        g5=tk.Frame(body,bg=C["white"]); g5.pack(fill="x")
        self._ent(g5,0,0,"Monthly Salary (₱)",    "monthly_salary", w=22)
        self._ent(g5,0,1,"Daily Rate (₱) — auto", "daily_rate",     w=22)
        self._ent(g5,1,0,"Rent (₱) — deducted from monthly before computing daily",
                  "rent", w=22)
        g5.grid_columnconfigure(0,weight=1); g5.grid_columnconfigure(2,weight=1)
        self._vars["monthly_salary"].trace("w",self._auto_dr)
        self._vars["rent"].trace("w",self._auto_dr)
        self._dp=tk.Label(body,text="",bg=C["g100"],fg=C["m700"],
                          font=("Segoe UI",9),anchor="w",padx=10,pady=6)
        self._dp.pack(fill="x",pady=(4,0))
        self._vars["monthly_salary"].trace("w",self._upd_ded)
        self._vars.setdefault("rent",tk.StringVar(value="0")).trace("w",self._upd_ded)

        # Gov IDs
        self._sec(body,"🏛️  Government Numbers")
        g6=tk.Frame(body,bg=C["white"]); g6.pack(fill="x")
        self._ent(g6,0,0,"SSS No.","sss_no",w=22)
        self._ent(g6,0,1,"PhilHealth No.","philhealth_no",w=22)
        self._ent(g6,1,0,"Pag-IBIG No.","pagibig_no",w=22)
        self._ent(g6,1,1,"TIN No.","tin_no",w=22)
        g6.grid_columnconfigure(0,weight=1); g6.grid_columnconfigure(2,weight=1)

        bf=tk.Frame(self,bg=C["white"],padx=28,pady=14,
                    highlightbackground=C["border"],highlightthickness=1)
        bf.pack(fill="x")
        button(bf,"Save Employee","primary",self._save,
               icon="💾",px=20,py=10).pack(side="right",padx=(8,0))
        button(bf,"Cancel","ghost",self.destroy,px=16,py=10).pack(side="right")

    def _auto_dr(self,*_):
        try:
            ms   = float(self._vars['monthly_salary'].get() or 0)
            rent = float(self._vars.get('rent', tk.StringVar(value='0')).get() or 0)
            gross_sal = ms - rent
            self._vars["daily_rate"].set(f"{max(gross_sal,0)/22:.2f}")
        except ValueError: pass

    def _upd_ded(self,*_):
        try:
            from computation import compute_sss,compute_philhealth,compute_pagibig,compute_daily_rate
            ms   = float(self._vars["monthly_salary"].get() or 0)
            rent = float(self._vars.get("rent",tk.StringVar(value="0")).get() or 0)
            gs   = max(ms - rent, 0)          # gross salary after rent
            dr   = compute_daily_rate(gs) if gs else 0
            sss  = compute_sss(ms)
            ph   = compute_philhealth(ms)
            pig  = compute_pagibig(ms)
            self._dp.config(
                text=f"  Gross Salary (after rent): ₱{gs:,.2f}  ·  "
                     f"Daily Rate: ₱{dr:,.2f}  ·  "
                     f"SSS ₱{sss:,.2f}  ·  PhilHealth ₱{ph:,.2f}  ·  "
                     f"Pag-IBIG ₱{pig:,.2f}")
        except Exception: pass

    def _load(self,eid):
        emp=get_employee_by_id(eid)
        if not emp: return
        for k in ("employee_id","first_name","last_name","middle_name",
                  "department","position","employment_type","hire_date",
                  "monthly_salary","daily_rate","sss_no","philhealth_no",
                  "pagibig_no","tin_no","status",
                  "contact_no","email","address","rent"):
            if k in self._vars:
                self._vars[k].set(str(emp.get(k) or ""))

    def _save(self):
        fn=self._vars["first_name"].get().strip()
        ln=self._vars["last_name"].get().strip()
        dept=self._vars["department"].get().strip()
        if not fn or not ln:
            messagebox.showerror("Required",
                "First Name and Last Name are required.",parent=self); return
        if not dept or dept not in DEPT_VALID:
            messagebox.showerror("Department Required",
                "Please select a valid Department:\n\n"
                "  • GBC - Church\n  • BVBC - College\n  • BVBC - Elementary",
                parent=self); return
        try:
            ms=float(self._vars["monthly_salary"].get() or 0)
            dr=float(self._vars["daily_rate"].get()     or 0)
        except ValueError:
            messagebox.showerror("Invalid","Salary must be a number.",parent=self); return
        try:
            rent_val = float(self._vars.get("rent", tk.StringVar(value="0")).get() or 0)
        except ValueError:
            rent_val = 0.0
        data=(fn,ln,
              self._vars["middle_name"].get().strip(),dept,
              self._vars["position"].get().strip(),
              self._vars["employment_type"].get(),
              self._vars["hire_date"].get().strip(),
              ms,dr,
              self._vars["sss_no"].get().strip(),
              self._vars["philhealth_no"].get().strip(),
              self._vars["pagibig_no"].get().strip(),
              self._vars["tin_no"].get().strip(),
              self._vars["status"].get() or "Active",
              self._vars.get("contact_no", tk.StringVar()).get().strip(),
              self._vars.get("email",      tk.StringVar()).get().strip(),
              self._vars.get("address",    tk.StringVar()).get().strip(),
              rent_val)
        nid=save_employee(data,self._eid)
        messagebox.showinfo("✅  Saved",
            f"Employee  {nid}  saved successfully.",parent=self)
        self._on_save(); self.destroy()
