from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    # ------------------------
    # CUSTOM ADMIN FLOW
    # ------------------------
    path("dashboard-login/", views.admin_login_view, name="admin_login"),  
    path("complete-profile-admin/", views.complete_profile_admin, name="complete_profile_admin"),
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),

    # ------------------------
    # USER FLOW
    # ------------------------
    path("login/", views.login_view, name="login"),     # user + agent login
    path("dashboard/user/", views.dashboard_user, name="dashboard_user"),
    path("profile/user/", views.complete_profile_user, name="complete_profile_user"),

    # ------------------------
    # AGENT FLOW
    # ------------------------
    path("dashboard/agent/", views.dashboard_agent, name="dashboard_agent"),
    path("profile/agent/", views.complete_profile_agent, name="complete_profile_agent"),

    # ------------------------
    # COMMON
    # ------------------------
    path("", views.index, name="index"),
    path("logout/", views.logout_view, name="logout"),
    path("loan-request/", views.loan_request, name="loan_request"),
    path("payment/<int:loan_id>/", views.payment_page, name="payment_page"),

    # ------------------------
    # DJANGO BUILT-IN ADMIN (for developer)
    # ------------------------
    path("admin/", admin.site.urls),
]
