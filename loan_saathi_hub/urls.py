from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    path("login/", views.login_view, name="login"),              # user + agent
    path("dashboard-login/", views.admin_login_view, name="admin_login"),  # admin only
    path("dashboard/user/", views.dashboard_user, name="dashboard_user"),
    path("dashboard/agent/", views.dashboard_agent, name="dashboard_agent"),
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("", views.index, name="index"),
    path("logout/", views.logout_view, name="logout"),
    path("loan-request/", views.loan_request, name="loan_request"),

    # ✅ Yeh line fix ki gayi (payment → payment_page)
    # urls.py
    path('payment/<int:loan_id>/', views.payment_page, name='payment_page'),

    path("profile/user/", views.complete_profile_user, name="complete_profile_user"),
    path("profile/agent/", views.complete_profile_agent, name="complete_profile_agent"),
]
