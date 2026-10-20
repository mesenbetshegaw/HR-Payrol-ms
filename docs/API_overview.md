# API Overview

Base URL: `http://localhost:8000/api/v1`

Interactive Swagger UI: `http://localhost:8000/api/docs/`

## Authentication
All endpoints (except login, forgot-password, reset-password) require:
```
Authorization: Bearer <access_token>
```

---

## Auth & Users

| Method | Endpoint | Role | Description |
|---|---|---|---|
| POST | `/auth/login/` | Public | Get JWT token pair |
| POST | `/auth/refresh/` | Public | Refresh access token |
| POST | `/auth/logout/` | Any | Blacklist refresh token |
| GET/PATCH | `/auth/me/` | Any | Own profile |
| POST | `/auth/change-password/` | Any | Change own password |
| POST | `/auth/forgot-password/` | Public | Request reset email |
| POST | `/auth/reset-password/` | Public | Use reset token |
| GET/POST | `/auth/users/` | Admin | List/create users |
| GET/PATCH/DELETE | `/auth/users/{id}/` | Admin | Manage user |
| POST | `/auth/users/{id}/unlock/` | Admin | Unlock account |
| GET/POST | `/auth/permissions/` | Admin | Permission matrix entries |
| GET/PUT | `/auth/permissions/matrix/{id}/` | Admin | Full matrix for Sub Admin |

---

## Organization

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET/POST | `/organization/departments/` | Admin/SubAdmin | Departments |
| GET/PATCH/DELETE | `/organization/departments/{id}/` | Admin/SubAdmin | Department detail |
| GET/POST | `/organization/positions/` | Admin/SubAdmin | Positions |
| GET/PATCH/DELETE | `/organization/positions/{id}/` | Admin/SubAdmin | Position detail |
| GET/POST | `/organization/branches/` | Admin/SubAdmin | Branches |
| GET/PATCH/DELETE | `/organization/branches/{id}/` | Admin/SubAdmin | Branch detail |
| GET/POST | `/organization/holidays/` | Any (GET) / Admin (POST) | Public holidays |
| GET/PATCH/DELETE | `/organization/holidays/{id}/` | Admin/SubAdmin | Holiday detail |

---

## Employees

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET/POST | `/employees/` | Admin/SubAdmin/Manager | Employee list/create |
| GET | `/employees/export/?format=csv\|xlsx` | Admin/SubAdmin | Export employees |
| GET/PATCH | `/employees/{id}/` | Admin/SubAdmin/Manager | Employee detail |
| POST | `/employees/{id}/status/` | Admin/SubAdmin | Change status |
| GET | `/employees/{id}/status-history/` | Admin/SubAdmin | Status history |
| GET/POST | `/employees/{id}/contracts/` | Admin/SubAdmin | Contracts |
| GET/POST | `/employees/{id}/documents/` | Admin/SubAdmin | Documents |

---

## Attendance

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET/POST | `/attendance/` | Admin/SubAdmin/Manager | Attendance records |
| POST | `/attendance/check-in/` | Any | Record check-in |
| POST | `/attendance/{id}/check-out/` | Any | Record check-out |
| POST | `/attendance/{id}/overtime-approval/` | Admin/Manager | Approve overtime |
| GET | `/attendance/summary/` | Any | Monthly summaries |
| POST | `/attendance/summary/generate/` | Admin/SubAdmin | Generate summary |

---

## Leave

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET/POST | `/leave/types/` | Admin/SubAdmin | Leave types |
| GET/PATCH/DELETE | `/leave/types/{id}/` | Admin/SubAdmin | Leave type detail |
| GET | `/leave/balances/` | Any | Leave balances |
| GET/POST | `/leave/requests/` | Any | Leave requests |
| GET/PATCH | `/leave/requests/{id}/` | Any | Request detail |
| POST | `/leave/requests/{id}/manager-approve/` | Admin/Manager | Manager approval |
| POST | `/leave/requests/{id}/hr-approve/` | Admin/SubAdmin | HR confirmation |
| POST | `/leave/requests/{id}/reject/` | Admin/Manager | Reject request |
| POST | `/leave/requests/{id}/cancel/` | Any | Cancel request |
| GET | `/leave/calendar/` | Any | Approved leaves calendar |

---

## Payroll

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET/POST | `/payroll/tax-brackets/` | Admin | Tax brackets |
| GET/PATCH/DELETE | `/payroll/tax-brackets/{id}/` | Admin | Tax bracket detail |
| GET/POST | `/payroll/pension-settings/` | Admin | Pension settings |
| GET/POST | `/payroll/overtime-rules/` | Admin | Overtime rules |
| GET/PATCH | `/payroll/overtime-rules/{id}/` | Admin | Overtime rule detail |
| GET/POST | `/payroll/salary/` | Admin/SubAdmin | Salary structures |
| GET/PATCH | `/payroll/salary/{id}/` | Admin/SubAdmin | Salary detail |
| GET/POST | `/payroll/runs/` | Admin/SubAdmin | Payroll runs |
| GET | `/payroll/runs/{id}/` | Admin/SubAdmin | Run detail |
| POST | `/payroll/runs/{id}/generate/` | Admin/SubAdmin | Generate payslips |
| POST | `/payroll/runs/{id}/advance/` | Admin/SubAdmin | Advance status |
| GET | `/payroll/runs/{id}/bank-transfer/` | Admin/SubAdmin | Bank transfer Excel |
| GET | `/payroll/payslips/` | Any | Payslips |
| GET/PATCH | `/payroll/payslips/{id}/` | Admin/SubAdmin | Payslip detail |
| GET | `/payroll/payslips/{id}/pdf/` | Any | Download PDF |

---

## Reports & Dashboards

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/reports/dashboard/admin/` | Admin/SubAdmin | Admin dashboard data |
| GET | `/reports/dashboard/manager/` | Manager | Manager dashboard data |
| GET | `/reports/dashboard/employee/` | Employee | Employee dashboard data |

---

## Notifications

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/notifications/` | Any | List notifications |
| GET | `/notifications/unread-count/` | Any | Unread count |
| POST | `/notifications/mark-all-read/` | Any | Mark all read |
| POST | `/notifications/{id}/read/` | Any | Mark one read |

---

## Audit

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/audit/logs/` | Admin | Audit log (read-only) |

---

## Pagination

All list endpoints support:
- `?page=N` — page number
- `?page_size=N` — results per page (max 100, default 20)
- `?search=term` — full-text search
- `?ordering=field` — sort (prefix `-` for descending)

## Error Format

```json
{
  "success": false,
  "errors": { "detail": "Error message here." },
  "status_code": 400
}
```
