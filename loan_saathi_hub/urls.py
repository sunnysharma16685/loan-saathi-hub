from django.contrib import admin
from django.urls import path
from main import views
from main import views_auth   # extra auth views agar alag file me rakhe hain

urlpatterns = [
    # -------------------- Home --------------------
    path("", views.home, name="home"),

    # -------------------- Auth --------------------
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-password/<uidb64>/<token>/", views.reset_password_view, name="reset_password"),

    # -------------------- Dashboards --------------------
    path("dashboard/applicant/", views.dashboard_applicant, name="dashboard_applicant"),
    path("dashboard/lender/", views.dashboard_lender, name="dashboard_lender"),
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),

    # -------------------- Complete Profiles --------------------
    path("complete-profile/applicant/", views.complete_profile_applicant, name="complete_profile_applicant"),
    path("complete-profile/lender/", views.complete_profile_lender, name="complete_profile_lender"),
    
    # -------------------- Loan + Payment --------------------
    path("loan-request/", views.loan_request, name="loan_request"),
    path("payment/<uuid:loan_id>/", views.payment_page, name="payment_page"),

    # -------------------- Utility --------------------
    path("send-test-email/", views.send_test_email, name="send_test_email"),
]
