from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('complete_profile_user/', views.complete_profile_user, name='complete_profile_user'),
    path('complete_profile_agent/', views.complete_profile_agent, name='complete_profile_agent'),
    path('dashboard_user/', views.dashboard_user, name='dashboard_user'),
    path('dashboard_agent/', views.dashboard_agent, name='dashboard_agent'),
    path('loan_request/', views.loan_request, name='loan_request'),
    path('payment/', views.payment, name='payment'),
    path('about/', views.about, name='about'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('faq/', views.faq, name='faq'),
    path('support/', views.support, name='support'),
    path('contacts/', views.contacts, name='contacts'),
    path('feedback/', views.feedback, name='feedback'),
]
