from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    # ---------------- Home ----------------
    path("", views.home, name="home"),

    # ---------------- Auth ----------------
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ---------------- Forgot / Reset Password ----------------
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-password/<uidb64>/<token>/", views.reset_password_view, name="reset_password"),

    # ---------------- Profile ----------------
    path("profile/<uuid:user_id>/", views.profile_form, name="profile_form"),

    # ---------------- Dashboards ----------------
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("dashboard/applicant/", views.dashboard_applicant, name="dashboard_applicant"),
    path("dashboard/lender/", views.dashboard_lender, name="dashboard_lender"),
    path("dashboard/", views.dashboard_router, name="dashboard_router"),   # auto redirect based on role

    # ---------------- Loan + Payment ----------------
    path("loan/request/", views.loan_request, name="loan_request"),
    path("payment/<uuid:loan_id>/", views.payment_page, name="payment_page"),

    # ---------------- Django Admin ----------------
    path("dashboard-login/", admin.site.urls),   # ✅ Admin login page (separate route)
]
