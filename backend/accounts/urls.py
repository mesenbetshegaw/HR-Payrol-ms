from django.urls import path
from accounts import views
from accounts import registration_views as rv

urlpatterns = [
    # Auth
    path("login/",           views.LoginView.as_view(),          name="auth-login"),
    path("refresh/",         views.RefreshView.as_view(),         name="auth-refresh"),
    path("logout/",          views.LogoutView.as_view(),          name="auth-logout"),
    path("me/",              views.MeView.as_view(),              name="auth-me"),
    path("change-password/", views.ChangePasswordView.as_view(),  name="auth-change-password"),
    path("forgot-password/", views.ForgotPasswordView.as_view(),  name="auth-forgot-password"),
    path("reset-password/",  views.ResetPasswordView.as_view(),   name="auth-reset-password"),

    # User management (Admin)
    path("users/",            views.UserListCreateView.as_view(),  name="user-list"),
    path("users/<int:pk>/",   views.UserDetailView.as_view(),      name="user-detail"),
    path("users/<int:pk>/unlock/", views.UnlockUserView.as_view(), name="user-unlock"),

    # Sub Admin permission matrix
    path("permissions/",                    views.SubAdminPermissionListView.as_view(),   name="permission-list"),
    path("permissions/<int:pk>/",           views.SubAdminPermissionDetailView.as_view(), name="permission-detail"),
    path("permissions/matrix/<int:pk>/",    views.UserPermissionMatrixView.as_view(),     name="permission-matrix"),

    # Self-registration workflow
    path("register/",                        rv.RegisterView.as_view(),               name="auth-register"),
    path("registrations/",                   rv.RegistrationRequestListView.as_view(), name="registration-list"),
    path("registrations/pending-count/",     rv.PendingRegistrationCountView.as_view(),name="registration-pending-count"),
    path("registrations/<int:pk>/",          rv.RegistrationRequestDetailView.as_view(),name="registration-detail"),
    path("registrations/<int:pk>/approve/",  rv.ApproveRegistrationView.as_view(),    name="registration-approve"),
    path("registrations/<int:pk>/reject/",   rv.RejectRegistrationView.as_view(),     name="registration-reject"),
]
