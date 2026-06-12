"""
BVBC Payroll System — Master Theme & Widget Library
Modern Maroon & Gold Design
"""
import tkinter as tk
from tkinter import ttk

# ═══════════════════════════════════════════════════════════════════
# COLOUR PALETTE
# ═══════════════════════════════════════════════════════════════════
C = {
    # Maroon spectrum
    "m900": "#2A0505",  # darkest
    "m800": "#3D0808",
    "m700": "#4A0909",
    "m600": "#6D0E0E",  # primary maroon
    "m500": "#8B1A1A",
    "m400": "#A52828",
    "m100": "#FDF3F3",  # lightest tint

    # Gold spectrum
    "g700": "#7A5A00",
    "g600": "#A07830",
    "g500": "#C9A84C",  # primary gold
    "g400": "#E8CC80",
    "g300": "#F5E4B0",
    "g100": "#FFF8E7",  # lightest tint

    # Neutrals
    "white":  "#FFFFFF",
    "bg":     "#FAF6F0",      # warm off-white background
    "bg2":    "#F2EBE0",
    "card":   "#FFFFFF",
    "border": "#E8D5A3",
    "bord2":  "#D4B896",

    # Text
    "t900":   "#1A0808",
    "t600":   "#5C3D2E",
    "t400":   "#9E7B5A",
    "t_inv":  "#FFFFFF",

    # Status
    "ok":     "#2D6A2D",
    "ok_bg":  "#E8F5E8",
    "err":    "#8B1A1A",
    "err_bg": "#FDF3F3",
    "inf":    "#1A4A7A",
    "inf_bg": "#E3EEF8",
    "wrn":    "#7A5200",
    "wrn_bg": "#FFF8D6",
}

# ═══════════════════════════════════════════════════════════════════
# FONTS
# ═══════════════════════════════════════════════════════════════════
F = {
    "display":  ("Segoe UI", 18, "bold"),
    "h1":       ("Segoe UI", 15, "bold"),
    "h2":       ("Segoe UI", 12, "bold"),
    "h3":       ("Segoe UI", 11, "bold"),
    "label":    ("Segoe UI", 10, "bold"),
    "body":     ("Segoe UI", 10),
    "small":    ("Segoe UI", 9),
    "tiny":     ("Segoe UI", 8),
    "mono":     ("Consolas",  10),
    "mono_sm":  ("Consolas",  9),
    "btn":      ("Segoe UI", 10, "bold"),
    "btn_lg":   ("Segoe UI", 11, "bold"),
    "stat_n":   ("Segoe UI", 24, "bold"),
    "stat_l":   ("Segoe UI", 9),
    "nav":      ("Segoe UI", 10),
    "nav_a":    ("Segoe UI", 10, "bold"),
}

MONTHS = ["","January","February","March","April","May","June",
          "July","August","September","October","November","December"]


# ═══════════════════════════════════════════════════════════════════
# STYLE SETUP
# ═══════════════════════════════════════════════════════════════════
def apply_global_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure("TFrame",     background=C["bg"])
    s.configure("TLabel",     background=C["bg"], font=F["body"], foreground=C["t900"])
    s.configure("TCombobox",  font=F["body"], padding=5,
                fieldbackground=C["g100"], background=C["white"])
    s.map("TCombobox", fieldbackground=[("readonly", C["g100"])])

    s.configure("TNotebook",  background=C["bg"], borderwidth=0)
    s.configure("TNotebook.Tab", font=F["label"], padding=[16, 7],
                background=C["bg2"], foreground=C["t600"])
    s.map("TNotebook.Tab",
          background=[("selected", C["m600"]), ("active", C["m500"])],
          foreground=[("selected", C["white"]), ("active", C["white"])])

    s.configure("TPanedwindow",        background=C["border"])
    s.configure("Vertical.TScrollbar",   background=C["bg2"],
                troughcolor=C["bg"], arrowcolor=C["m600"], borderwidth=0)
    s.configure("Horizontal.TScrollbar", background=C["bg2"],
                troughcolor=C["bg"], arrowcolor=C["m600"], borderwidth=0)

    # Treeview
    s.configure("BV.Treeview", font=F["body"], rowheight=28,
                background=C["white"], fieldbackground=C["white"],
                foreground=C["t900"], borderwidth=0, relief="flat")
    s.configure("BV.Treeview.Heading", font=F["label"],
                background=C["m600"], foreground=C["white"],
                relief="flat", padding=7)
    s.map("BV.Treeview",
          background=[("selected", C["g300"])],
          foreground=[("selected", C["m700"])])
    s.map("BV.Treeview.Heading",
          background=[("active", C["m500"])])


# ═══════════════════════════════════════════════════════════════════
# REUSABLE WIDGET BUILDERS
# ═══════════════════════════════════════════════════════════════════

def page_header(parent, title, subtitle=""):
    """Top header bar with maroon background and gold accent line."""
    hdr = tk.Frame(parent, bg=C["m700"], height=58)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    inner = tk.Frame(hdr, bg=C["m700"])
    inner.place(relx=0, rely=0, relwidth=1, relheight=1)
    tk.Label(inner, text=title, bg=C["m700"], fg=C["white"],
             font=F["display"]).pack(side="left", padx=22, pady=8)
    if subtitle:
        tk.Label(inner, text=f"  ·  {subtitle}", bg=C["m700"],
                 fg=C["g400"], font=F["body"]).pack(side="left", pady=8)
    # Gold gradient line
    gold_bar = tk.Frame(parent, height=4, bg=C["g500"])
    gold_bar.pack(fill="x")
    return hdr


def section_header(parent, text, bg=None):
    """Section title with gold underline."""
    bg = bg or C["bg"]
    frame = tk.Frame(parent, bg=bg)
    tk.Label(frame, text=text, bg=bg, fg=C["m700"],
             font=F["h2"]).pack(anchor="w")
    tk.Frame(frame, bg=C["g500"], height=2).pack(fill="x", pady=(2, 8))
    return frame


def card(parent, padx=20, pady=16, relief=True):
    """White card with gold border."""
    if relief:
        outer = tk.Frame(parent, bg=C["g500"], padx=1, pady=1)
        inner = tk.Frame(outer, bg=C["card"], padx=padx, pady=pady)
        inner.pack(fill="both", expand=True)
        return outer, inner
    else:
        frame = tk.Frame(parent, bg=C["card"], padx=padx, pady=pady,
                         highlightbackground=C["border"], highlightthickness=1)
        return frame, frame


def button(parent, text, style="primary", command=None,
           px=14, py=8, icon="", font_key="btn", **kw):
    """Styled button with hover effect."""
    palette = {
        "primary":  (C["m600"], C["white"],  C["m500"]),
        "gold":     (C["g500"], C["m700"],   C["g600"]),
        "success":  (C["ok"],   C["white"],  "#1E5C1E"),
        "danger":   (C["err"],  C["white"],  C["m500"]),
        "outline":  (C["white"],C["m600"],   C["g100"]),
        "ghost":    (C["bg"],   C["m600"],   C["g300"]),
        "dark":     (C["m800"], C["white"],  C["m700"]),
        "info":     (C["inf"],  C["white"],  "#123760"),
    }
    bg, fg, hbg = palette.get(style, palette["primary"])
    label = f"{icon}  {text}" if icon else text
    b = tk.Button(parent, text=label, bg=bg, fg=fg,
                  font=F[font_key], relief="flat", cursor="hand2",
                  padx=px, pady=py,
                  activebackground=hbg, activeforeground=fg,
                  command=command, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=hbg))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def field(parent, row, col, label_text, var_dict, key,
          width=22, readonly=False, colspan=1, row_span=1):
    """Form label + entry pair placed on a grid."""
    r, c = row * 2, col * 2
    span = colspan * 2
    tk.Label(parent, text=label_text, bg=C["card"],
             fg=C["t600"], font=F["label"]
             ).grid(row=r, column=c, columnspan=span, sticky="w",
                    pady=(10, 0), padx=(0, 12))
    var = tk.StringVar()
    state = "readonly" if readonly else "normal"
    bg_ = C["bg2"] if readonly else C["g100"]
    e = tk.Entry(parent, textvariable=var, font=F["body"],
                 width=width, bd=0, highlightthickness=1,
                 highlightbackground=C["border"],
                 highlightcolor=C["g500"],
                 readonlybackground=C["bg2"],
                 bg=bg_, state=state)
    e.grid(row=r+1, column=c, columnspan=span, sticky="ew",
           pady=(2, 0), padx=(0, 12), ipady=6)
    var_dict[key] = var
    return var


def treeview(parent, cols, headings, widths,
             height=14, anchors=None, stretch_col=None):
    """Styled treeview with vertical + horizontal scrollbars."""
    # Tkinter column anchor must be one of: n ne e se s sw w nw center
    # Map common aliases to valid values
    _anchor_map = {"left": "w", "right": "e", "center": "center",
                   "w": "w", "e": "e", "n": "n", "s": "s",
                   "ne": "ne", "se": "se", "sw": "sw", "nw": "nw"}

    frame = tk.Frame(parent, bg=C["bg"])
    tv = ttk.Treeview(frame, columns=cols, show="headings",
                      height=height, style="BV.Treeview")
    anchors = anchors or {}
    for col, h, w in zip(cols, headings, widths):
        tv.heading(col, text=h)
        raw_anchor = anchors.get(col, "center")
        safe_anchor = _anchor_map.get(str(raw_anchor).lower(), "center")
        tv.column(col, width=w, anchor=safe_anchor,
                  stretch=(col == stretch_col))
    vsb = ttk.Scrollbar(frame, orient="vertical",   command=tv.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal",  command=tv.xview)
    tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tv.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    tv.tag_configure("odd",  background=C["g100"])
    tv.tag_configure("even", background=C["white"])
    return frame, tv


def stat_card(parent, icon, label, value, accent):
    """Dashboard metric card."""
    outer = tk.Frame(parent, bg=accent, padx=2, pady=2)
    inner = tk.Frame(outer, bg=C["white"], padx=18, pady=16)
    inner.pack(fill="both", expand=True)
    # Top accent strip
    tk.Frame(inner, bg=accent, height=5).pack(fill="x", pady=(0, 10))
    tk.Label(inner, text=icon, bg=C["white"], fg=accent,
             font=("Segoe UI", 26)).pack()
    tk.Label(inner, text=str(value), bg=C["white"], fg=accent,
             font=F["stat_n"]).pack(pady=(2, 0))
    tk.Label(inner, text=label, bg=C["white"], fg=C["t400"],
             font=F["stat_l"]).pack()
    return outer


def divider(parent, bg=None, pady=8, height=1):
    tk.Frame(parent, bg=bg or C["border"], height=height).pack(fill="x", pady=pady)


def badge(parent, text, style="ok"):
    colours = {
        "ok":  (C["ok_bg"],  C["ok"]),
        "err": (C["err_bg"], C["err"]),
        "inf": (C["inf_bg"], C["inf"]),
        "wrn": (C["wrn_bg"], C["wrn"]),
        "gold":(C["g100"],   C["g700"]),
    }
    bg_, fg_ = colours.get(style, colours["ok"])
    return tk.Label(parent, text=f"  {text}  ", bg=bg_, fg=fg_,
                    font=F["small"], pady=3)


def separator_line(parent, bg=None):
    tk.Frame(parent, bg=bg or C["border"], height=1).pack(fill="x", padx=16, pady=6)
