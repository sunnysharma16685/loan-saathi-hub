from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard_user/', views.dashboard_user, name='dashboard_user'),
    path('dashboard_agent/', views.dashboard_agent, name='dashboard_agent'),
    path('loan_request/', views.loan_request, name='loan_request'),
    path('payment/<int:loan_id>/', views.payment_page, name='payment'),
    path('complete_profile_user/', views.complete_profile_user, name='complete_profile_user'),
    path('complete_profile_agent/', views.complete_profile_agent, name='complete_profile_agent'),
]
