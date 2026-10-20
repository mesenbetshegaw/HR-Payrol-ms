"""Dynamic dashboard views — all data live from PostgreSQL, no static values."""
from __future__ import annotations
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import IsAdminOrSubAdmin
import datetime


@extend_schema(tags=["dashboard"])
class AdminDashboardView(APIView):
    """Live dashboard for Admin / Sub Admin — 100% data from PostgreSQL."""
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get(self, request: Request) -> Response:
        from attendance.models import AttendanceRecord, AttendanceStatus
        from employees.models import Employee, EmploymentStatus
        from leave.models import LeaveRequest, LeaveStatus
        from payroll.models import PayrollRun, PayrollStatus, Payslip
        from accounts.models import RegistrationRequest, RegistrationStatus

        today = timezone.now().date()
        year  = today.year
        month = today.month

        # ── Headcount ─────────────────────────────────────────────────────
        total_active     = Employee.objects.filter(status=EmploymentStatus.ACTIVE).count()
        total_inactive   = Employee.objects.filter(status=EmploymentStatus.INACTIVE).count()
        total_terminated = Employee.objects.filter(status=EmploymentStatus.TERMINATED).count()
        new_this_month   = Employee.objects.filter(hire_date__year=year, hire_date__month=month).count()

        # By department (sorted by count)
        by_dept = list(
            Employee.objects.filter(status=EmploymentStatus.ACTIVE)
            .values("department__name", "department__id")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        by_dept = [{"name": d["department__name"] or "Unassigned",
                    "id": d["department__id"], "count": d["count"]} for d in by_dept]

        # By role/position (top 5)
        by_position = list(
            Employee.objects.filter(status=EmploymentStatus.ACTIVE)
            .values("position__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        # ── Attendance today ───────────────────────────────────────────────
        today_records = AttendanceRecord.objects.filter(date=today)
        today_present = today_records.filter(status=AttendanceStatus.PRESENT).count()
        today_absent  = today_records.filter(status=AttendanceStatus.ABSENT).count()
        today_late    = today_records.filter(status=AttendanceStatus.LATE).count()
        attendance_rate = round(today_present / total_active * 100, 1) if total_active else 0

        # Monthly attendance trend (last 6 months)
        monthly_attendance = []
        for i in range(5, -1, -1):
            d = today.replace(day=1) - datetime.timedelta(days=i*28)
            present = AttendanceRecord.objects.filter(
                date__year=d.year, date__month=d.month,
                status=AttendanceStatus.PRESENT
            ).count()
            absent = AttendanceRecord.objects.filter(
                date__year=d.year, date__month=d.month,
                status=AttendanceStatus.ABSENT
            ).count()
            monthly_attendance.append({
                "month": d.strftime("%b %Y"),
                "present": present,
                "absent": absent,
            })

        # Pending overtime approvals
        pending_overtime = AttendanceRecord.objects.filter(
            overtime_status="PENDING", overtime_hours__gt=0
        ).count()

        # ── Leave ─────────────────────────────────────────────────────────
        pending_leaves          = LeaveRequest.objects.filter(status=LeaveStatus.PENDING).count()
        manager_approved_leaves = LeaveRequest.objects.filter(status=LeaveStatus.MANAGER_APPROVED).count()
        approved_today          = LeaveRequest.objects.filter(
            status=LeaveStatus.APPROVED,
            hr_approved_at__date=today
        ).count()
        on_leave_today = Employee.objects.filter(status=EmploymentStatus.ON_LEAVE).count()

        # Leave by type (this month)
        leave_by_type = list(
            LeaveRequest.objects.filter(
                status=LeaveStatus.APPROVED,
                start_date__year=year, start_date__month=month
            ).values("leave_type__name")
            .annotate(count=Count("id"), total_days=Sum("number_of_days"))
            .order_by("-total_days")
        )

        # ── Payroll ───────────────────────────────────────────────────────
        latest_run = PayrollRun.objects.order_by("-year", "-month").first()
        payroll_history = list(
            PayrollRun.objects.order_by("-year", "-month")[:6]
            .values("year", "month", "status", "total_gross", "total_net",
                    "total_tax", "total_employee_pension")
        )
        payroll_history = [{
            **p,
            "period": f"{p['year']}/{str(p['month']).zfill(2)}",
            "total_gross": float(p["total_gross"] or 0),
            "total_net": float(p["total_net"] or 0),
            "total_tax": float(p["total_tax"] or 0),
            "total_employee_pension": float(p["total_employee_pension"] or 0),
        } for p in payroll_history]

        # ── Registration requests ──────────────────────────────────────────
        pending_registrations = RegistrationRequest.objects.filter(
            status=RegistrationStatus.PENDING
        ).count()

        return Response({
            "generated_at": timezone.now().isoformat(),
            "employees": {
                "total_active": total_active,
                "total_inactive": total_inactive,
                "total_terminated": total_terminated,
                "new_this_month": new_this_month,
                "by_department": by_dept,
                "by_position": [{"name": p["position__name"] or "—", "count": p["count"]} for p in by_position],
            },
            "attendance": {
                "today_present": today_present,
                "today_absent": today_absent,
                "today_late": today_late,
                "attendance_rate": attendance_rate,
                "pending_overtime": pending_overtime,
                "monthly_trend": monthly_attendance,
            },
            "leave": {
                "pending": pending_leaves,
                "manager_approved": manager_approved_leaves,
                "approved_today": approved_today,
                "on_leave_today": on_leave_today,
                "by_type": [{"name": l["leave_type__name"], "count": l["count"],
                              "days": float(l["total_days"] or 0)} for l in leave_by_type],
            },
            "payroll": {
                "latest_status": latest_run.status if latest_run else None,
                "latest_period": f"{latest_run.year}/{str(latest_run.month).zfill(2)}" if latest_run else None,
                "latest_total_gross": float(latest_run.total_gross) if latest_run else 0,
                "latest_total_net": float(latest_run.total_net) if latest_run else 0,
                "latest_total_tax": float(latest_run.total_tax) if latest_run else 0,
                "history": payroll_history,
            },
            "registrations": {
                "pending": pending_registrations,
            },
        })


@extend_schema(tags=["dashboard"])
class ManagerDashboardView(APIView):
    """Live dashboard for Manager — own department data only."""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from attendance.models import AttendanceRecord, AttendanceStatus
        from employees.models import Employee, EmploymentStatus
        from leave.models import LeaveRequest, LeaveStatus

        user = request.user
        dept = user.managed_department
        if not dept:
            return Response({"detail": "No department assigned."}, status=400)

        today = timezone.now().date()
        year  = today.year
        month = today.month

        team = Employee.objects.filter(department=dept, status=EmploymentStatus.ACTIVE)
        team_count = team.count()

        today_present = AttendanceRecord.objects.filter(
            employee__in=team, date=today, status=AttendanceStatus.PRESENT
        ).count()
        today_absent = AttendanceRecord.objects.filter(
            employee__in=team, date=today, status=AttendanceStatus.ABSENT
        ).count()
        today_late = AttendanceRecord.objects.filter(
            employee__in=team, date=today, status=AttendanceStatus.LATE
        ).count()

        pending_leaves       = LeaveRequest.objects.filter(employee__in=team, status=LeaveStatus.PENDING).count()
        approved_leaves      = LeaveRequest.objects.filter(
            employee__in=team, status=LeaveStatus.APPROVED,
            start_date__year=year, start_date__month=month
        ).count()
        pending_overtime     = AttendanceRecord.objects.filter(
            employee__in=team, overtime_status="PENDING", overtime_hours__gt=0
        ).count()

        # Monthly trend for this dept
        monthly = []
        for i in range(5, -1, -1):
            d = today.replace(day=1) - datetime.timedelta(days=i*28)
            p = AttendanceRecord.objects.filter(
                employee__in=team, date__year=d.year, date__month=d.month,
                status=AttendanceStatus.PRESENT
            ).count()
            monthly.append({"month": d.strftime("%b"), "present": p})

        # Team list
        team_list = list(team.values("id", "first_name", "last_name", "employee_id", "status")
                         .select_related()[:20])

        return Response({
            "department": dept.name,
            "team_count": team_count,
            "today": {
                "present": today_present,
                "absent": today_absent,
                "late": today_late,
                "attendance_rate": round(today_present / team_count * 100, 1) if team_count else 0,
            },
            "leave": {
                "pending_approvals": pending_leaves,
                "approved_this_month": approved_leaves,
            },
            "overtime": {
                "pending_approvals": pending_overtime,
            },
            "monthly_trend": monthly,
            "team": team_list,
        })


@extend_schema(tags=["dashboard"])
class EmployeeDashboardView(APIView):
    """Live dashboard for Employee — own data only."""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from attendance.models import AttendanceRecord, AttendanceStatus
        from leave.models import LeaveBalance, LeaveRequest, LeaveStatus
        from payroll.models import Payslip

        user = request.user
        if not hasattr(user, "employee") or not user.employee:
            return Response({"detail": "No employee profile linked."}, status=400)

        emp   = user.employee
        today = timezone.now().date()
        year  = today.year
        month = today.month

        # Today's attendance
        today_record = AttendanceRecord.objects.filter(employee=emp, date=today).first()

        # This month attendance summary
        month_records  = AttendanceRecord.objects.filter(employee=emp, date__year=year, date__month=month)
        month_present  = month_records.filter(status=AttendanceStatus.PRESENT).count()
        month_absent   = month_records.filter(status=AttendanceStatus.ABSENT).count()
        month_late     = month_records.filter(status=AttendanceStatus.LATE).count()

        # Leave balances
        balances = list(
            LeaveBalance.objects.filter(employee=emp, year=year)
            .select_related("leave_type")
            .values("leave_type__name", "leave_type__code", "allocated_days", "used_days", "carried_over")
        )
        balances = [{
            **b,
            "remaining": float((b["allocated_days"] or 0) + (b["carried_over"] or 0) - (b["used_days"] or 0)),
            "allocated_days": float(b["allocated_days"] or 0),
            "used_days": float(b["used_days"] or 0),
        } for b in balances]

        # Recent leave requests
        recent_leaves = list(
            LeaveRequest.objects.filter(employee=emp).order_by("-created_at")[:5]
            .values("id", "leave_type__name", "start_date", "end_date", "number_of_days", "status")
        )

        # Payslips
        last_payslip = Payslip.objects.filter(employee=emp).order_by("-payroll_run__year", "-payroll_run__month").first()
        payslip_history = list(
            Payslip.objects.filter(employee=emp).order_by("-payroll_run__year", "-payroll_run__month")[:6]
            .values("id", "payroll_run__year", "payroll_run__month", "gross_salary", "net_pay", "income_tax")
        )
        payslip_history = [{
            **p,
            "period": f"{p['payroll_run__year']}/{str(p['payroll_run__month']).zfill(2)}",
            "net_pay": float(p["net_pay"] or 0),
            "gross_salary": float(p["gross_salary"] or 0),
            "income_tax": float(p["income_tax"] or 0),
        } for p in payslip_history]

        return Response({
            "employee_id": emp.employee_id,
            "name": emp.get_full_name(),
            "department": emp.department.name if emp.department else None,
            "position": emp.position.name if emp.position else None,
            "today_attendance": {
                "check_in": str(today_record.check_in) if today_record and today_record.check_in else None,
                "check_out": str(today_record.check_out) if today_record and today_record.check_out else None,
                "status": today_record.status if today_record else None,
                "overtime_hours": float(today_record.overtime_hours) if today_record else 0,
            },
            "this_month": {
                "present_days": month_present,
                "absent_days": month_absent,
                "late_days": month_late,
            },
            "leave_balances": balances,
            "recent_leaves": recent_leaves,
            "last_payslip": {
                "period": f"{last_payslip.payroll_run.year}/{str(last_payslip.payroll_run.month).zfill(2)}" if last_payslip else None,
                "net_pay": float(last_payslip.net_pay) if last_payslip else None,
                "gross_salary": float(last_payslip.gross_salary) if last_payslip else None,
                "income_tax": float(last_payslip.income_tax) if last_payslip else None,
                "id": last_payslip.id if last_payslip else None,
            },
            "payslip_history": payslip_history,
        })
