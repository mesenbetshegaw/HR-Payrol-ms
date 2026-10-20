# Ethiopian HR & Payroll Management System

A full-stack, production-quality Human Resource and Payroll Management System built for Ethiopian organizations as a graduation project.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, Django 5.1, Django REST Framework 3.15 |
| Auth | SimpleJWT (access + refresh tokens) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| API Docs | drf-spectacular (OpenAPI / Swagger) |
| PDF | ReportLab |
| Excel | openpyxl |
| Frontend | React 18 + Vite 5 |
| Routing | React Router v6 |
| Data fetching | TanStack Query v5 |
| Forms | React Hook Form + Zod |
| Styling | Tailwind CSS v3 |
| Charts | Recharts |
| i18n | react-i18next (English + Amharic) |
| Tests | pytest-django, 52 tests |

---

## Project Structure

```
Graduation_Project/
├── backend/                  # Django project
│   ├── accounts/             # Auth, users, RBAC, permission matrix
│   ├── organization/         # Departments, positions, branches, holidays
│   ├── employees/            # Employee profiles, contracts, documents
│   ├── attendance/           # Daily records, overtime approval
│   ├── leave/                # Leave types, balances, approval workflow
│   ├── payroll/              # Tax engine, payroll runs, payslip PDF
│   ├── reports/              # Role-scoped dashboards
│   ├── notifications/        # In-app notification system
│   ├── audit/                # Immutable audit log + middleware
│   ├── config/               # Django settings, URLs, exceptions
│   ├── tests/                # 52 pytest tests
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React + Vite SPA
│   ├── src/
│   │   ├── api/              # Axios client + all API functions
│   │   ├── components/       # Reusable UI (Table, Modal, StatCard…)
│   │   ├── context/          # AuthContext
│   │   ├── pages/            # All pages by role
│   │   ├── utils/            # ETB formatter, status badges
│   │   ├── i18n.js           # English + Amharic translations
│   │   └── App.jsx           # Routes + role guards
│   ├── .env.example
│   └── package.json
└── docs/
    ├── ER_diagram.md         # Mermaid ER diagram
    └── API_overview.md       # Endpoint summary
```

---

## Roles

| Role | Access |
|---|---|
| **Admin** | Full access: users, settings, tax rules, final payroll approval, audit log |
| **Sub Admin** | Configurable permission matrix (per module: view/create/edit/delete/approve) |
| **Manager** | Own department only: leave approvals, attendance, overtime approval |
| **Employee** | Self-service: profile, attendance, leave requests, payslips |

---

## Setup — Backend

### Prerequisites
- Python 3.11+ (tested on 3.14)
- pip

### Steps

```bash
cd backend

# 1. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# Edit .env — set SECRET_KEY at minimum

# 4. Run database migrations
python manage.py migrate

# 5. Seed demo data (creates 4 users + sample records)
python manage.py seed_demo

# 6. Start the development server
python manage.py runserver
```

Backend runs at: http://localhost:8000

API Documentation (Swagger): http://localhost:8000/api/docs/

---

## Setup — Frontend

### Prerequisites
- Node.js 18+ (tested on v26)
- npm 10+

### Steps

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# Default: VITE_API_URL=http://localhost:8000/api/v1

# 3. Start development server
npm run dev
```

Frontend runs at: http://localhost:5173

### Build for production

```bash
npm run build
```

---

## Demo Login Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@hrpayroll.et | Admin@1234 |
| Sub Admin | subadmin@hrpayroll.et | SubAdmin@1234 |
| Manager | manager@hrpayroll.et | Manager@1234 |
| Employee | employee@hrpayroll.et | Employee@1234 |

---

## Running Tests

```bash
cd backend
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

pytest tests/ -v
```

Expected: **52 passed**

Run with coverage:

```bash
pytest tests/ --cov=. --cov-report=term-missing
```

---

## Ethiopian Payroll Rules

All rates are stored in the database and editable by Admin.

### Income Tax Brackets (Monthly, ETB)

| Income Range | Rate | Deduction |
|---|---|---|
| 0 – 2,000 | 0% | 0 |
| 2,001 – 4,000 | 15% | 300 |
| 4,001 – 7,000 | 20% | 500 |
| 7,001 – 10,000 | 25% | 850 |
| 10,001 – 14,000 | 30% | 1,350 |
| Above 14,000 | 35% | 2,050 |

### Pension
- Employee: 7% of basic salary
- Employer: 11% of basic salary

### Overtime Multipliers
- Normal day: ×1.25
- Night: ×1.50
- Weekly rest day: ×2.00
- Public holiday: ×2.50
- Hourly rate = basic salary ÷ 208

### Calculation Order
```
Gross  = basic + taxable_allowances + overtime + bonus
Tax    = income_tax(gross)
Net    = gross + non_taxable_allowances − income_tax − employee_pension − other_deductions
```

### Verification Example
- Basic: ETB 10,000, no allowances
- Employee pension: ETB 700 (7%)
- Employer pension: ETB 1,100 (11%)
- Income tax: ETB 1,650 (bracket 25% − 850)
- **Net pay: ETB 7,650** ✓

---

## API Endpoints Overview

All endpoints are prefixed with `/api/v1/`.

| Module | Endpoints |
|---|---|
| Auth | `/auth/login/`, `/auth/logout/`, `/auth/refresh/`, `/auth/me/`, `/auth/change-password/`, `/auth/forgot-password/`, `/auth/reset-password/` |
| Users | `/auth/users/`, `/auth/users/{id}/`, `/auth/users/{id}/unlock/` |
| Permissions | `/auth/permissions/`, `/auth/permissions/matrix/{id}/` |
| Organization | `/organization/departments/`, `/organization/positions/`, `/organization/branches/`, `/organization/holidays/` |
| Employees | `/employees/`, `/employees/{id}/`, `/employees/{id}/status/`, `/employees/{id}/contracts/`, `/employees/{id}/documents/`, `/employees/export/` |
| Attendance | `/attendance/`, `/attendance/check-in/`, `/attendance/{id}/check-out/`, `/attendance/{id}/overtime-approval/`, `/attendance/summary/` |
| Leave | `/leave/types/`, `/leave/balances/`, `/leave/requests/`, `/leave/requests/{id}/manager-approve/`, `/leave/requests/{id}/hr-approve/`, `/leave/requests/{id}/reject/`, `/leave/requests/{id}/cancel/`, `/leave/calendar/` |
| Payroll | `/payroll/tax-brackets/`, `/payroll/pension-settings/`, `/payroll/overtime-rules/`, `/payroll/salary/`, `/payroll/runs/`, `/payroll/runs/{id}/generate/`, `/payroll/runs/{id}/advance/`, `/payroll/runs/{id}/bank-transfer/`, `/payroll/payslips/`, `/payroll/payslips/{id}/pdf/` |
| Reports | `/reports/dashboard/admin/`, `/reports/dashboard/manager/`, `/reports/dashboard/employee/` |
| Notifications | `/notifications/`, `/notifications/unread-count/`, `/notifications/mark-all-read/`, `/notifications/{id}/read/` |
| Audit | `/audit/logs/` |

Full interactive docs: http://localhost:8000/api/docs/

---

## Leave Approval Workflow

```
Employee submits request (PENDING)
    ↓
Manager approves (MANAGER_APPROVED) — cannot approve own request
    ↓
HR (Sub Admin) confirms (APPROVED) — balance deducted automatically
    ↓
Employee notified ✓
```

## Payroll Workflow

```
Sub Admin creates run (DRAFT)
    ↓
Sub Admin generates payslips → reviews (REVIEWED)
    ↓
Admin approves (APPROVED) — locked, no further edits
    ↓
Employees notified, PDFs available
    ↓
Admin marks as paid (PAID) + bank transfer Excel export
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Django secret key (required) |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `DB_ENGINE` | `django.db.backends.sqlite3` | Database engine |
| `DB_NAME` | `db.sqlite3` | Database name / path |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Refresh token lifetime |
| `ACCOUNT_LOCKOUT_ATTEMPTS` | `5` | Failed logins before lockout |
| `ACCOUNT_LOCKOUT_MINUTES` | `30` | Lockout duration |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Allowed CORS origins |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max file upload size |
