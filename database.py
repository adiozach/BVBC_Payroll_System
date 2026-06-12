"""
Baptist Voice Bible College Payroll Management System
Database Module - Handles all SQLite operations
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "bvbc_payroll.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create all tables if they don't exist and seed sample data."""
    conn = get_connection()
    c = conn.cursor()

    # ── USERS ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    NOT NULL UNIQUE,
            password  TEXT    NOT NULL,
            full_name TEXT,
            role      TEXT    DEFAULT 'admin',
            created   TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── EMPLOYEES ─────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id   TEXT    NOT NULL UNIQUE,
            first_name    TEXT    NOT NULL,
            last_name     TEXT    NOT NULL,
            middle_name   TEXT,
            department    TEXT,
            position      TEXT,
            employment_type TEXT  DEFAULT 'Regular',
            hire_date     TEXT,
            monthly_salary REAL   DEFAULT 0,
            daily_rate    REAL    DEFAULT 0,
            sss_no        TEXT,
            philhealth_no TEXT,
            pagibig_no    TEXT,
            tin_no        TEXT,
            status        TEXT    DEFAULT 'Active',
            contact_no    TEXT,
            email         TEXT,
            address       TEXT,
            rent          REAL    DEFAULT 0,
            created       TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── PAYROLL RECORDS ───────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS payroll (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     TEXT    NOT NULL,
            period_month    INTEGER NOT NULL,
            period_year     INTEGER NOT NULL,
            cutoff          TEXT    DEFAULT '1-31',
            days_worked     REAL    DEFAULT 0,
            basic_pay       REAL    DEFAULT 0,
            overtime_hours  REAL    DEFAULT 0,
            overtime_pay    REAL    DEFAULT 0,
            late_minutes    REAL    DEFAULT 0,
            late_deduction  REAL    DEFAULT 0,
            absent_days     REAL    DEFAULT 0,
            absent_deduction REAL   DEFAULT 0,
            sss             REAL    DEFAULT 0,
            philhealth      REAL    DEFAULT 0,
            pagibig         REAL    DEFAULT 0,
            cash_advance    REAL    DEFAULT 0,
            hdmf_loan       REAL    DEFAULT 0,
            sss_loan        REAL    DEFAULT 0,
            other_deductions REAL   DEFAULT 0,
            alumni_fee      REAL    DEFAULT 0,
            coop_loan       REAL    DEFAULT 0,
            uniform         REAL    DEFAULT 0,
            canteen         REAL    DEFAULT 0,
            gross_pay       REAL    DEFAULT 0,
            total_deductions REAL   DEFAULT 0,
            net_pay         REAL    DEFAULT 0,
            notes           TEXT,
            rent            REAL    DEFAULT 0,
            sss_wisp        REAL    DEFAULT 0,
            coop_savings    REAL    DEFAULT 0,
            insurance       REAL    DEFAULT 0,
            travel_fund     REAL    DEFAULT 0,
            sacrificial     REAL    DEFAULT 0,
            total_savings   REAL    DEFAULT 0,
            created         TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
    """)

    # ── DEDUCTION RATES ───────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS deduction_rates (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE,
            rate       REAL    DEFAULT 0,
            is_percent INTEGER DEFAULT 1,
            updated    TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── ATTENDANCE ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id  TEXT    NOT NULL,
            date         TEXT    NOT NULL,
            time_in      TEXT,
            time_out     TEXT,
            status       TEXT    DEFAULT 'Present',
            late_minutes REAL    DEFAULT 0,
            overtime_hrs REAL    DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
    """)

    conn.commit()

    # ── SEED ADMIN ────────────────────────────────────────────────────────
    import hashlib
    default_pw = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password, full_name, role) VALUES (?,?,?,?)",
              ("admin", default_pw, "System Administrator", "admin"))

    # ── SEED DEDUCTION RATES ─────────────────────────────────────────────
    rates = [
        ("SSS Employee", 4.5, 1),
        ("PhilHealth Employee", 2.0, 1),
        ("Pag-IBIG Employee", 2.0, 1),
    ]
    for name, rate, is_pct in rates:
        c.execute("INSERT OR IGNORE INTO deduction_rates (name, rate, is_percent) VALUES (?,?,?)",
                  (name, rate, is_pct))

    # No sample employees seeded — system starts fresh

    # ── MIGRATE: add contact/email/address columns if missing ─────────────
    existing_cols = [row["name"] for row in
                     c.execute("PRAGMA table_info(employees)").fetchall()]
    for col, typedef in [("contact_no", "TEXT"),
                         ("email",      "TEXT"),
                         ("address",    "TEXT"),
                         ("rent",       "REAL DEFAULT 0")]:
        if col not in existing_cols:
            c.execute(f"ALTER TABLE employees ADD COLUMN {col} {typedef}")
    conn.commit()

    # ── MIGRATE: add columns to payroll if missing ────────────────────────
    payroll_cols = [row["name"] for row in
                    c.execute("PRAGMA table_info(payroll)").fetchall()]
    for col, typedef in [("alumni_fee",   "REAL DEFAULT 0"),
                         ("coop_loan",    "REAL DEFAULT 0"),
                         ("uniform",      "REAL DEFAULT 0"),
                         ("canteen",      "REAL DEFAULT 0"),
                         ("rent",         "REAL DEFAULT 0"),
                         ("sss_wisp",     "REAL DEFAULT 0"),
                         ("coop_savings", "REAL DEFAULT 0"),
                         ("insurance",    "REAL DEFAULT 0"),
                         ("travel_fund",  "REAL DEFAULT 0"),
                         ("sacrificial",  "REAL DEFAULT 0"),
                         ("total_savings","REAL DEFAULT 0")]:
        if col not in payroll_cols:
            c.execute(f"ALTER TABLE payroll ADD COLUMN {col} {typedef}")
    conn.commit()

    conn.commit()
    conn.close()


# ── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def generate_employee_id():
    conn = get_connection()
    row = conn.execute("SELECT employee_id FROM employees ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        try:
            num = int(row["employee_id"].split("-")[1]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"EMP-{num:03d}"


def get_all_employees(search="", status_filter="Active"):
    conn = get_connection()
    query = "SELECT * FROM employees WHERE 1=1"
    params = []
    if search:
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR employee_id LIKE ? OR department LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    if status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY last_name, first_name"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_employee_by_id(emp_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM employees WHERE employee_id = ?", (emp_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_employee(data, emp_id=None):
    conn = get_connection()
    if emp_id:
        conn.execute("""
            UPDATE employees SET first_name=?, last_name=?, middle_name=?, department=?,
            position=?, employment_type=?, hire_date=?, monthly_salary=?, daily_rate=?,
            sss_no=?, philhealth_no=?, pagibig_no=?, tin_no=?, status=?,
            contact_no=?, email=?, address=?, rent=?
            WHERE employee_id=?
        """, (*data, emp_id))
    else:
        new_id = generate_employee_id()
        data = (new_id, *data)
        conn.execute("""
            INSERT INTO employees
            (employee_id, first_name, last_name, middle_name, department, position,
             employment_type, hire_date, monthly_salary, daily_rate,
             sss_no, philhealth_no, pagibig_no, tin_no, status,
             contact_no, email, address, rent)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, data)
        emp_id = new_id
    conn.commit()
    conn.close()
    return emp_id


def delete_employee(emp_id):
    """Soft-delete: marks employee as Inactive (reversible)."""
    conn = get_connection()
    conn.execute("UPDATE employees SET status='Inactive' WHERE employee_id=?", (emp_id,))
    conn.commit()
    conn.close()


def permanent_delete_employee(emp_id):
    """
    Hard-delete: permanently removes the employee AND all their payroll records.
    This action is IRREVERSIBLE.
    Returns dict with count of deleted payroll rows.
    """
    conn = get_connection()
    payroll_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM payroll WHERE employee_id=?", (emp_id,)
    ).fetchone()["cnt"]
    attendance_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM attendance WHERE employee_id=?", (emp_id,)
    ).fetchone()["cnt"]
    conn.execute("DELETE FROM payroll    WHERE employee_id=?", (emp_id,))
    conn.execute("DELETE FROM attendance WHERE employee_id=?", (emp_id,))
    conn.execute("DELETE FROM employees  WHERE employee_id=?", (emp_id,))
    conn.commit()
    conn.close()
    return {"payroll_deleted": payroll_count, "attendance_deleted": attendance_count}


def get_payroll_records(month=None, year=None, emp_id=None):
    conn = get_connection()
    q = """
        SELECT p.*, e.first_name, e.last_name, e.department, e.position
        FROM payroll p
        JOIN employees e ON p.employee_id = e.employee_id
        WHERE 1=1
    """
    params = []
    if month:
        q += " AND p.period_month=?"
        params.append(month)
    if year:
        q += " AND p.period_year=?"
        params.append(year)
    if emp_id:
        q += " AND p.employee_id=?"
        params.append(emp_id)
    q += " ORDER BY e.last_name, e.first_name"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    # Convert sqlite3.Row to plain dict so .get() and all dict ops work
    return [dict(r) for r in rows]


def save_payroll(data):
    conn = get_connection()
    # Check if record exists
    existing = conn.execute(
        "SELECT id FROM payroll WHERE employee_id=? AND period_month=? AND period_year=? AND cutoff=?",
        (data["employee_id"], data["period_month"], data["period_year"], data["cutoff"])
    ).fetchone()
    cols = ["employee_id","period_month","period_year","cutoff","days_worked","basic_pay",
            "overtime_hours","overtime_pay","late_minutes","late_deduction","absent_days",
            "absent_deduction","sss","philhealth","pagibig","cash_advance","hdmf_loan",
            "sss_loan","other_deductions","alumni_fee","coop_loan","uniform","canteen",
            "gross_pay","total_deductions","net_pay","notes",
            "rent","sss_wisp","coop_savings","insurance","travel_fund",
            "sacrificial","total_savings"]
    vals = [data.get(c, 0) for c in cols]
    if existing:
        set_clause = ", ".join(f"{c}=?" for c in cols[3:])
        conn.execute(f"UPDATE payroll SET {set_clause} WHERE id=?", vals[3:] + [existing["id"]])
    else:
        ph = ",".join(["?"] * len(cols))
        conn.execute(f"INSERT INTO payroll ({','.join(cols)}) VALUES ({ph})", vals)
    conn.commit()
    conn.close()


def get_deduction_rates():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM deduction_rates").fetchall()
    conn.close()
    return {r["name"]: r["rate"] for r in rows}


def backup_database(dest_folder):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(dest_folder, f"bvbc_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    return dest


def restore_database(src_path):
    shutil.copy2(src_path, DB_PATH)
