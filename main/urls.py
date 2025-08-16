from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/user/", views.dashboard_user, name="dashboard_user"),
    path("dashboard/agent/", views.dashboard_agent, name="dashboard_agent"),

    path("loan-request/", views.loan_request, name="loan_request"),

    # ✅ Yeh line fix ki gayi (payment → payment_page)
    # urls.py
    path('payment/<int:loan_id>/', views.payment_page, name='payment_page'),

    path("profile/user/", views.complete_profile_user, name="complete_profile_user"),
    path("profile/agent/", views.complete_profile_agent, name="complete_profile_agent"),
]
