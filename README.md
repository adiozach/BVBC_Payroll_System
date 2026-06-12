# 💼 BVBC Payroll Management System

> A desktop payroll management application built for **Blessed Virgin of the Beautiful Campus (BVBC)** school — designed for HR staff and school administrators to manage employee compensation with accuracy and ease.

---

## 📌 Overview

The **BVBC Payroll Management System** is a full-featured Windows desktop application that automates and streamlines the payroll process for school employees. Built with Python and a professional CustomTkinter UI, it handles everything from employee records to payslip generation — with zero need for internet connectivity.

Developed specifically for BVBC's HR department, the system mirrors the school's actual payslip format and payroll computation workflow, making the transition from manual processing to digital seamless.

---

## ✨ Features

### 👥 Employee Management
- Add, edit, and manage employee profiles
- Store personal information, position, department, and employment type
- Track employment status (active/inactive)

### 💰 Payroll Processing
- Supports **weekly**, **semi-monthly**, and **monthly** pay schedules
- Automatic computation of:
  - Basic pay based on position and rate
  - Government deductions (SSS, PhilHealth, Pag-IBIG)
  - Tax withholding (BIR)
  - Other deductions and allowances
- **QuickDeductionEditor** for fast adjustment of individual deductions
- Payroll formula reverse-engineered from actual BVBC payslips for 100% accuracy

### 🧾 Payslip Generation
- Generate professional payslips matching BVBC's official format
- Export payslips to **PDF** for printing or digital distribution
- Batch generation for all employees in one click

### 📊 Reports & Export
- Export payroll data to **Excel (.xlsx)** for record-keeping and auditing
- Generate summary reports per pay period
- Department-level payroll breakdown

### 🎨 UI & Settings
- Clean, professional interface with **BVBC maroon-and-gold** color theme
- Configurable system settings via GUI settings panel
- Designed for non-technical HR users — no training required

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.x |
| GUI Framework | CustomTkinter |
| Database | SQLite |
| PDF Generation | fpdf2 |
| Excel Export | openpyxl |
| Packaging | PyInstaller (Windows installer) |

---

## 📂 Project Structure

```
BVBC_Payroll_System/
├── main.py                 # App entry point
├── run.pyw                 # Silent launcher (no console window)
├── ui.py                   # Core UI setup and theming
├── gui_dashboard.py        # Main dashboard screen
├── gui_employees.py        # Employee management screen
├── gui_payroll.py          # Payroll processing screen
├── gui_payslip.py          # Payslip generation screen
├── gui_reports.py          # Reports and export screen
├── gui_settings.py         # System settings screen
├── reports_export.py       # PDF and Excel export logic
├── setup.py                # App configuration and build setup
└── requirements.txt        # Python dependencies
```

---

## 🚀 Getting Started

### Requirements
- Windows 10 / 11
- Python 3.10 or higher (for running from source)

### Run from Source

```bash
# Clone the repository
git clone https://github.com/adiozach/BVBC_Payroll_System.git
cd BVBC_Payroll_System

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Run the Windows Installer
Use the provided installer (`BVBC_Payroll_Setup.exe`) for a one-click installation on any Windows machine — no Python required.

---

## 🏫 Intended Users

| User | Role |
|---|---|
| HR Staff | Process payroll, generate payslips, manage deductions |
| School Administrator | Review payroll summaries and approve processing |
| Finance Officer | Export reports and audit payroll records |

---

## 📸 Screenshots

> *(Add screenshots of the dashboard, payroll screen, and payslip here)*

---

## 🙏 Acknowledgements

Developed for **BVBC School** — Lucena City, Quezon, Philippines.  
Built with ❤️ by **adiozach** using Python and CustomTkinter.

---

## 📄 License

This project is proprietary software developed exclusively for BVBC School.  
Unauthorized distribution or modification is not permitted.
