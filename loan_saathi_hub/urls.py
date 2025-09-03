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
    path("profile/<uuid:user_id>/edit/", views.edit_profile, name="edit_profile"),
    
    

    # ---------------- Dashboards ----------------
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("dashboard/applicant/", views.dashboard_applicant, name="dashboard_applicant"),
    path("dashboard/lender/", views.dashboard_lender, name="dashboard_lender"),
    path("dashboard/", views.dashboard_router, name="dashboard_router"),  
    


    # ---------------- Loan + Payment ----------------
    path("loan/request/", views.loan_request, name="loan_request"),
    path("loan/<uuid:loan_id>/reject/", views.reject_loan, name="reject_loan"),
    path("loan/<uuid:loan_id>/payment/", views.payment_page, name="payment_page"),

    # Lender-specific actions
    path("dashboard/lender/partial-profile/<uuid:loan_id>/", views.partial_profile, name="partial_profile"),
    path("dashboard/lender/dummy-payment/<uuid:loan_id>/", views.make_dummy_payment, name="make_dummy_payment"),
    path("profile/<uuid:user_id>/<uuid:loan_id>/", views.view_profile, name="view_profile"),


    # ---------------- Django Admin ----------------
    path("admin/", admin.site.urls),
]
