"""
Baptist Voice Bible College Payroll Management System
Computation Module — with Weekly Cutoff Support
"""

# ── SSS TABLE (2023 employee share) ──────────────────────────────────────────
SSS_TABLE = [
    (0,      3249.99,  135.00), (3250,   3749.99,  157.50),
    (3750,   4249.99,  180.00), (4250,   4749.99,  202.50),
    (4750,   5249.99,  225.00), (5250,   5749.99,  247.50),
    (5750,   6249.99,  270.00), (6250,   6749.99,  292.50),
    (6750,   7249.99,  315.00), (7250,   7749.99,  337.50),
    (7750,   8249.99,  360.00), (8250,   8749.99,  382.50),
    (8750,   9249.99,  405.00), (9250,   9749.99,  427.50),
    (9750,  10249.99,  450.00), (10250, 10749.99,  472.50),
    (10750, 11249.99,  495.00), (11250, 11749.99,  517.50),
    (11750, 12249.99,  540.00), (12250, 12749.99,  562.50),
    (12750, 13249.99,  585.00), (13250, 13749.99,  607.50),
    (13750, 14249.99,  630.00), (14250, 14749.99,  652.50),
    (14750, 15249.99,  675.00), (15250, 15749.99,  697.50),
    (15750, 16249.99,  720.00), (16250, 16749.99,  742.50),
    (16750, 17249.99,  765.00), (17250, 17749.99,  787.50),
    (17750, 18249.99,  810.00), (18250, 18749.99,  832.50),
    (18750, 19249.99,  855.00), (19250, 19749.99,  877.50),
    (19750, 20249.99,  900.00), (20250, float("inf"), 900.00),
]

# ── CUTOFF DEFINITIONS ───────────────────────────────────────────────────────
# Each entry: (label, default_days_worked, deduction_divisor)
#   deduction_divisor = how many of these cutoffs exist per month
#   so monthly statutory deductions are split evenly across cutoffs
CUTOFF_META = {
    "1-7":   {"days": 5,  "divisor": 4, "type": "weekly",       "week": 1},
    "8-14":  {"days": 5,  "divisor": 4, "type": "weekly",       "week": 2},
    "15-22": {"days": 6,  "divisor": 4, "type": "weekly",       "week": 3},
    "23-30": {"days": 6,  "divisor": 4, "type": "weekly",       "week": 4},
    "1-15":  {"days": 11, "divisor": 2, "type": "semi-monthly", "week": None},
    "16-31": {"days": 11, "divisor": 2, "type": "semi-monthly", "week": None},
    "1-31":  {"days": 22, "divisor": 1, "type": "monthly",      "week": None},
}

ALL_CUTOFFS = list(CUTOFF_META.keys())

WEEKLY_CUTOFFS      = [k for k, v in CUTOFF_META.items() if v["type"] == "weekly"]
SEMIMONTHLY_CUTOFFS = [k for k, v in CUTOFF_META.items() if v["type"] == "semi-monthly"]
MONTHLY_CUTOFFS     = [k for k, v in CUTOFF_META.items() if v["type"] == "monthly"]


def get_cutoff_meta(cutoff: str) -> dict:
    return CUTOFF_META.get(str(cutoff).strip(), CUTOFF_META["1-31"])


def get_cutoff_days(cutoff: str) -> int:
    """Default working days for a given cutoff period."""
    return get_cutoff_meta(cutoff)["days"]


def get_cutoff_divisor(cutoff: str) -> int:
    """
    How many times this cutoff type occurs per month.
    Used to split monthly statutory deductions proportionally.
    Weekly=4, Semi-monthly=2, Monthly=1
    """
    return get_cutoff_meta(cutoff)["divisor"]


def get_cutoff_label(cutoff: str) -> str:
    """Human-readable label for a cutoff period."""
    meta = get_cutoff_meta(cutoff)
    week = meta["week"]
    ctype = meta["type"].title()
    if week:
        return f"Week {week} ({cutoff}) — {ctype}"
    return f"{cutoff} — {ctype}"


# ── STATUTORY COMPUTATION FUNCTIONS ─────────────────────────────────────────

def compute_sss(monthly_salary: float) -> float:
    for lo, hi, ee in SSS_TABLE:
        if lo <= monthly_salary <= hi:
            return ee
    return 900.00


def compute_philhealth(monthly_salary: float) -> float:
    """Employee share = 2.5% of salary, min ₱250, max ₱2,500"""
    total = monthly_salary * 0.05
    total = max(500.00, min(total, 5000.00))
    return round(total / 2, 2)


def compute_pagibig(monthly_salary: float) -> float:
    """Employee share = 2% up to ₱5,000 salary base"""
    return round(min(monthly_salary, 5000.00) * 0.02, 2)


def compute_daily_rate(monthly_salary: float, working_days: int = 22) -> float:
    return round(monthly_salary / working_days, 4)


def compute_hourly_rate(daily_rate: float, hours: int = 8) -> float:
    return round(daily_rate / hours, 4)


def compute_overtime_pay(daily_rate: float, ot_hours: float, rate: float = 1.25) -> float:
    return round(compute_hourly_rate(daily_rate) * rate * ot_hours, 2)


def compute_late_deduction(daily_rate: float, late_minutes: float) -> float:
    per_min = compute_hourly_rate(daily_rate) / 60
    return round(per_min * late_minutes, 2)


def compute_absent_deduction(daily_rate: float, absent_days: float) -> float:
    return round(daily_rate * absent_days, 2)


# ── MAIN PAYROLL COMPUTATION ─────────────────────────────────────────────────

def compute_payroll(emp, params: dict) -> dict:
    """
    Compute full payroll for one employee for one cutoff period.

    Weekly cutoff logic:
      - Basic pay  = daily_rate × days_worked  (days reflect the week span)
      - Statutory deductions are MONTHLY amounts split by cutoff divisor
        e.g. SSS ₱405 / 4 weeks = ₱101.25 per weekly payslip
      - Cash advances, loans, other deductions are per-cutoff (entered directly)

    params keys:
      period_month, period_year, cutoff,
      days_worked, overtime_hours, late_minutes, absent_days,
      sss (optional override), philhealth (optional), pagibig (optional),
      cash_advance, hdmf_loan, sss_loan, other_deductions, notes
    """
    monthly  = float(emp["monthly_salary"])
    daily    = (float(emp["daily_rate"])
                if emp["daily_rate"] else compute_daily_rate(monthly))
    cutoff   = str(params.get("cutoff", "1-31")).strip()
    meta     = get_cutoff_meta(cutoff)
    divisor  = meta["divisor"]

    # Days worked — use param or cutoff default
    working  = float(params.get("days_worked", meta["days"]))

    # Earnings
    basic_pay        = round(daily * working, 2)
    ot_hours         = float(params.get("overtime_hours", 0))
    overtime_pay     = compute_overtime_pay(daily, ot_hours)
    late_mins        = float(params.get("late_minutes", 0))
    late_deduction   = compute_late_deduction(daily, late_mins)
    absent_days      = float(params.get("absent_days", 0))
    absent_deduction = compute_absent_deduction(daily, absent_days)

    gross_pay = basic_pay + overtime_pay

    # Statutory deductions — split by divisor for weekly/semi-monthly
    # Allow manual override from params (for editing individual records)
    monthly_sss = compute_sss(monthly)
    monthly_ph  = compute_philhealth(monthly)
    monthly_pig = compute_pagibig(monthly)

    sss        = float(params.get("sss",        round(monthly_sss / divisor, 2)))
    philhealth = float(params.get("philhealth", round(monthly_ph  / divisor, 2)))
    pagibig    = float(params.get("pagibig",    round(monthly_pig / divisor, 2)))

    # ── RENT + HONORARIUM FORMULA ────────────────────────────────────────
    # From actual BVBC payroll:
    #   Gross Salary  = Monthly Salary - Rent
    #   Weekly Honorarium = Gross Salary * 12 / 52   (= gross / 4.333 weeks/month)
    #   Daily Rate    = Gross Salary / (52/12 * 5)   (= gross * 12 / 260)
    #   Honorarium    = Daily Rate * Days Worked
    rent             = float(params.get("rent", float(emp.get("rent") or 0)))
    gross_salary     = round(monthly - rent, 2)
    # Always use the 12/52 weekly formula — matches actual BVBC payslips
    daily            = round(gross_salary * 12 / (52 * 5), 6)  # per day
    basic_pay        = round(daily * working, 2)
    gross_pay        = basic_pay + overtime_pay

    # ── DEDUCTIONS (order matches BVBC payslip) ───────────────────────────
    sss_wisp         = float(params.get("sss_wisp",         0))
    cash_advance     = float(params.get("cash_advance",     0))
    hdmf_loan        = float(params.get("hdmf_loan",        0))
    sss_loan         = float(params.get("sss_loan",         0))
    alumni_fee       = float(params.get("alumni_fee",       0))
    coop_loan        = float(params.get("coop_loan",        0))
    uniform          = float(params.get("uniform",          0))
    canteen          = float(params.get("canteen",          0))
    other_deductions = float(params.get("other_deductions", 0))

    total_deductions = round(
        sss + sss_wisp + sss_loan +
        philhealth + pagibig +
        hdmf_loan + alumni_fee + coop_loan +
        uniform + canteen +
        late_deduction + absent_deduction +
        cash_advance + other_deductions, 2)

    # ── SAVINGS (also reduce net pay) ─────────────────────────────────────
    coop_savings  = float(params.get("coop_savings",  0))
    insurance     = float(params.get("insurance",     0))
    travel_fund   = float(params.get("travel_fund",   0))
    sacrificial   = float(params.get("sacrificial",   0))
    total_savings = round(coop_savings + insurance + travel_fund + sacrificial, 2)

    # NET = GROSS - TOTAL DEDUCTIONS - TOTAL SAVINGS
    net_pay = round(gross_pay - total_deductions - total_savings, 2)

    return {
        "employee_id":      emp["employee_id"],
        "period_month":     params["period_month"],
        "period_year":      params["period_year"],
        "cutoff":           cutoff,
        "days_worked":      working,
        "basic_pay":        basic_pay,
        "overtime_hours":   ot_hours,
        "overtime_pay":     overtime_pay,
        "late_minutes":     late_mins,
        "late_deduction":   late_deduction,
        "absent_days":      absent_days,
        "absent_deduction": absent_deduction,
        "sss":              sss,
        "sss_wisp":         sss_wisp,
        "sss_loan":         sss_loan,
        "philhealth":       philhealth,
        "pagibig":          pagibig,
        "cash_advance":     cash_advance,
        "hdmf_loan":        hdmf_loan,
        "alumni_fee":       alumni_fee,
        "coop_loan":        coop_loan,
        "uniform":          uniform,
        "canteen":          canteen,
        "other_deductions": other_deductions,
        "coop_savings":     coop_savings,
        "insurance":        insurance,
        "travel_fund":      travel_fund,
        "sacrificial":      sacrificial,
        "total_savings":    total_savings,
        "gross_pay":        gross_pay,
        "gross_salary":     gross_salary,
        "rent":             rent,
        "total_deductions": total_deductions,
        "net_pay":          net_pay,
        "notes":            params.get("notes", ""),
    }
