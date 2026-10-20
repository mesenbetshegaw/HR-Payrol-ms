"""
Tests for accounts: auth, permissions per role, user management.
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestAuthentication:

    def test_login_success(self, api_client, admin_user):
        resp = api_client.post("/api/v1/auth/login/", {
            "email": "admin@test.et",
            "password": "Admin@1234",
        })
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["user"]["role"] == "ADMIN"

    def test_login_wrong_password(self, api_client, admin_user):
        resp = api_client.post("/api/v1/auth/login/", {
            "email": "admin@test.et",
            "password": "wrongpassword",
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_increments_failed_attempts(self, api_client, admin_user):
        for _ in range(3):
            api_client.post("/api/v1/auth/login/", {"email": "admin@test.et", "password": "wrong"})
        admin_user.refresh_from_db()
        assert admin_user.failed_login_attempts == 3

    def test_account_lockout_after_5_failures(self, api_client, admin_user):
        from django.conf import settings
        for _ in range(settings.ACCOUNT_LOCKOUT_ATTEMPTS):
            api_client.post("/api/v1/auth/login/", {"email": "admin@test.et", "password": "wrong"})
        # Now attempt with correct password — should be locked (401) or throttled (429)
        resp = api_client.post("/api/v1/auth/login/", {"email": "admin@test.et", "password": "Admin@1234"})
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_me_endpoint_authenticated(self, admin_client, admin_user):
        resp = admin_client.get("/api/v1/auth/me/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["email"] == admin_user.email

    def test_me_endpoint_unauthenticated(self, api_client):
        resp = api_client.get("/api/v1/auth/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPermissionsByRole:
    """Each endpoint should return 403 for roles without access."""

    def test_admin_can_list_users(self, admin_client):
        resp = admin_client.get("/api/v1/auth/users/")
        assert resp.status_code == status.HTTP_200_OK

    def test_employee_cannot_list_users(self, employee_client):
        resp = employee_client.get("/api/v1/auth/users/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_cannot_list_users(self, manager_client):
        resp = manager_client.get("/api/v1/auth/users/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_subadmin_cannot_list_users(self, subadmin_client):
        resp = subadmin_client.get("/api/v1/auth/users/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_access_audit_log(self, employee_client):
        resp = employee_client.get("/api/v1/audit/logs/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_audit_log(self, admin_client):
        resp = admin_client.get("/api/v1/audit/logs/")
        assert resp.status_code == status.HTTP_200_OK

    def test_employee_cannot_access_payroll_tax_brackets(self, employee_client):
        resp = employee_client.get("/api/v1/payroll/tax-brackets/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_payroll_settings(self, admin_client):
        resp = admin_client.get("/api/v1/payroll/tax-brackets/")
        assert resp.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_access_employees(self, api_client):
        resp = api_client.get("/api/v1/employees/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_manager_can_view_employees(self, manager_client):
        resp = manager_client.get("/api/v1/employees/")
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserManagement:

    def test_admin_can_create_user(self, admin_client):
        resp = admin_client.post("/api/v1/auth/users/", {
            "email": "new@test.et",
            "first_name": "New",
            "last_name": "User",
            "role": "EMPLOYEE",
            "password": "NewUser@1234",
            "confirm_password": "NewUser@1234",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["email"] == "new@test.et"

    def test_password_mismatch_rejected(self, admin_client):
        resp = admin_client.post("/api/v1/auth/users/", {
            "email": "new2@test.et",
            "first_name": "New",
            "last_name": "User",
            "role": "EMPLOYEE",
            "password": "Password@1234",
            "confirm_password": "Different@5678",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_unlock_user(self, admin_client, admin_user):
        from accounts.models import User
        from django.utils import timezone
        u = User.objects.create_user(email="locked@test.et", password="Lock@1234",
                                     first_name="Locked", last_name="User", role="EMPLOYEE")
        u.lockout_until = timezone.now() + timezone.timedelta(hours=1)
        u.failed_login_attempts = 5
        u.save()
        resp = admin_client.post(f"/api/v1/auth/users/{u.id}/unlock/")
        assert resp.status_code == status.HTTP_200_OK
        u.refresh_from_db()
        assert u.lockout_until is None

    def test_change_password(self, employee_client):
        resp = employee_client.post("/api/v1/auth/change-password/", {
            "old_password": "Emp@1234",
            "new_password": "NewPass@9876",
            "confirm_new_password": "NewPass@9876",
        })
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestOrganizationAPI:

    def test_anyone_authenticated_can_view_holidays(self, employee_client):
        resp = employee_client.get("/api/v1/organization/holidays/")
        assert resp.status_code == status.HTTP_200_OK

    def test_employee_cannot_create_department(self, employee_client):
        resp = employee_client.post("/api/v1/organization/departments/", {"name": "Test", "code": "T1"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_department(self, admin_client):
        resp = admin_client.post("/api/v1/organization/departments/", {"name": "Finance", "code": "FIN"})
        assert resp.status_code == status.HTTP_201_CREATED
