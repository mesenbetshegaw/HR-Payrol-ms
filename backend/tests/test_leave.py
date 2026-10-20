"""
Tests for the leave management workflow.

Full flow: employee requests → manager approves → HR confirms → balance updates.
"""
import datetime
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status


@pytest.mark.django_db
class TestLeaveWorkflow:

    def test_employee_can_submit_leave(self, employee_profile, leave_type_annual, leave_balance):
        from leave.services import submit_leave_request
        today = datetime.date.today()
        req = submit_leave_request(
            employee=employee_profile,
            leave_type=leave_type_annual,
            start_date=today + datetime.timedelta(days=7),
            end_date=today + datetime.timedelta(days=9),
            number_of_days=Decimal("3"),
            reason="Vacation",
        )
        assert req.status == "PENDING"
        assert req.number_of_days == Decimal("3")

    def test_submit_fails_if_insufficient_balance(self, employee_profile, leave_type_annual, leave_balance):
        from leave.services import submit_leave_request
        from rest_framework.exceptions import ValidationError
        today = datetime.date.today()
        with pytest.raises(ValidationError):
            submit_leave_request(
                employee=employee_profile,
                leave_type=leave_type_annual,
                start_date=today + datetime.timedelta(days=1),
                end_date=today + datetime.timedelta(days=20),
                number_of_days=Decimal("20"),  # more than allocated 16
            )

    def test_manager_approve(self, manager_user, employee_profile, leave_type_annual, leave_balance):
        from leave.services import submit_leave_request, manager_approve_leave
        today = datetime.date.today()
        req = submit_leave_request(
            employee=employee_profile,
            leave_type=leave_type_annual,
            start_date=today + datetime.timedelta(days=7),
            end_date=today + datetime.timedelta(days=9),
            number_of_days=Decimal("3"),
        )
        approved = manager_approve_leave(req, manager_user, "Looks good")
        assert approved.status == "MANAGER_APPROVED"
        assert approved.manager_approved_by == manager_user

    def test_hr_confirm_updates_balance(self, subadmin_user, manager_user, employee_profile, leave_type_annual, leave_balance):
        from leave.models import LeaveBalance
        from leave.services import submit_leave_request, manager_approve_leave, hr_approve_leave
        today = datetime.date.today()
        req = submit_leave_request(
            employee=employee_profile,
            leave_type=leave_type_annual,
            start_date=today + datetime.timedelta(days=7),
            end_date=today + datetime.timedelta(days=9),
            number_of_days=Decimal("3"),
        )
        manager_approve_leave(req, manager_user)
        hr_approve_leave(req, subadmin_user)

        balance = LeaveBalance.objects.get(
            employee=employee_profile,
            leave_type=leave_type_annual,
            year=today.year,
        )
        assert balance.used_days == Decimal("3")
        assert balance.remaining_days == Decimal("13")

    def test_cannot_approve_own_leave(self, employee_profile, leave_type_annual, leave_balance, employee_user):
        from leave.services import submit_leave_request, manager_approve_leave
        from rest_framework.exceptions import ValidationError
        today = datetime.date.today()
        req = submit_leave_request(
            employee=employee_profile,
            leave_type=leave_type_annual,
            start_date=today + datetime.timedelta(days=7),
            end_date=today + datetime.timedelta(days=8),
            number_of_days=Decimal("2"),
        )
        with pytest.raises(ValidationError):
            manager_approve_leave(req, employee_user)  # employee approving own leave

    def test_reject_leave(self, manager_user, employee_profile, leave_type_annual, leave_balance):
        from leave.services import submit_leave_request, reject_leave
        today = datetime.date.today()
        req = submit_leave_request(
            employee=employee_profile,
            leave_type=leave_type_annual,
            start_date=today + datetime.timedelta(days=7),
            end_date=today + datetime.timedelta(days=8),
            number_of_days=Decimal("2"),
        )
        rejected = reject_leave(req, manager_user, "Team is short-staffed")
        assert rejected.status == "REJECTED"
        assert rejected.rejection_reason == "Team is short-staffed"

    def test_cancel_leave_restores_balance(self, subadmin_user, manager_user, employee_profile, leave_type_annual, leave_balance):
        from leave.models import LeaveBalance
        from leave.services import submit_leave_request, manager_approve_leave, hr_approve_leave, cancel_leave
        today = datetime.date.today()
        req = submit_leave_request(
            employee=employee_profile,
            leave_type=leave_type_annual,
            start_date=today + datetime.timedelta(days=7),
            end_date=today + datetime.timedelta(days=9),
            number_of_days=Decimal("3"),
        )
        manager_approve_leave(req, manager_user)
        hr_approve_leave(req, subadmin_user)
        # Now cancel — balance should be restored
        cancel_leave(req, subadmin_user)

        balance = LeaveBalance.objects.get(employee=employee_profile, leave_type=leave_type_annual, year=today.year)
        assert balance.used_days == Decimal("0")


@pytest.mark.django_db
class TestLeaveAPI:

    def test_employee_can_list_own_requests(self, employee_client, employee_profile, leave_type_annual, leave_balance):
        from leave.models import LeaveRequest
        today = datetime.date.today()
        LeaveRequest.objects.create(
            employee=employee_profile,
            leave_type=leave_type_annual,
            start_date=today + datetime.timedelta(days=7),
            end_date=today + datetime.timedelta(days=8),
            number_of_days=Decimal("2"),
            status="PENDING",
        )
        resp = employee_client.get("/api/v1/leave/requests/")
        assert resp.status_code == status.HTTP_200_OK

    def test_anon_cannot_access(self, api_client):
        resp = api_client.get("/api/v1/leave/requests/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
