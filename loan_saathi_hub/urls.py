from django.contrib import admin
from django.urls import path
from main import views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from main import views as main_views

urlpatterns = [
    # ---------------- Home ----------------
    path("", views.index, name="index"),

    # ---------------- Auth ----------------
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ---------------- Forgot / Reset Password ----------------
    path("forgot_password/", views.forgot_password_view, name="forgot_password"),
    path("reset_password/<uidb64>/<token>/", views.reset_password_view, name="reset_password"),

    # ---------------- Profile ----------------
    path("profile/<uuid:user_id>/", views.profile_form, name="profile_form"),
    path("profile/<uuid:user_id>/edit/", views.edit_profile, name="edit_profile"),
    path("dashboard/lender/view_profile/<uuid:loan_id>/", views.view_profile, name="view_profile"),
    path("dashboard/lender/partial_profile/<uuid:loan_id>/", views.partial_profile, name="partial_profile"),
    path("review_profile/", views.review_profile, name="review_profile"),

    # ---------------- Dashboards ----------------
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("dashboard/applicant/", views.dashboard_applicant, name="dashboard_applicant"),
    path("dashboard/lender/", views.dashboard_lender, name="dashboard_lender"),
    path("dashboard/", views.dashboard_router, name="dashboard_router"),  # auto redirect based on role
    path("dashboard/lender/cibil/generate/<uuid:loan_id>/", main_views.generate_cibil_score, name="generate_cibil_score"),

    # ---------------- Loan + Payment ----------------
    path("loan/request/", views.loan_request, name="loan_request"),
    path("dashboard/lender/payment/<uuid:loan_id>/", views.payment_page, name="payment_page"),
    path("dashboard/lender/dummy-payment/<uuid:loan_id>/", views.make_dummy_payment, name="make_dummy_payment"),
    path("dashboard/lender/reject/<uuid:loan_id>/", views.reject_loan, name="reject_loan"),
    path("dashboard/lender/approve/<uuid:loan_id>/", views.approve_loan, name="approve_loan"),

    # ---------------- Applicant Loan Actions ----------------
    path("applicant/accept/<uuid:loan_id>/<uuid:lender_id>/", views.applicant_accept_loan, name="applicant_accept_loan"),
    

    # ---------------- Custom Admin ----------------
    path("admin_login/", views.admin_login, name="admin_login"),
    path("dashboard_admin/", views.dashboard_admin, name="dashboard_admin"),
    path("admin/user_action/<uuid:user_id>/", views.admin_user_action, name="admin_user_action"),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path("admin/full_profile/<uuid:user_id>/", views.admin_view_profile, name="admin_full_profile"),


    # -------Support, complaint, feedback routes------------------------
    path("support/", main_views.support_view, name="support"),
    path("complaint/", main_views.complaint_view, name="complaint"),
    path("feedback/", main_views.feedback_view, name="feedback"),

    # ---------------- Footer static pages ----------------
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("terms/", TemplateView.as_view(template_name="terms.html"), name="terms"),
    path("privacy/", TemplateView.as_view(template_name="privacy.html"), name="privacy"),
    path("faq/", TemplateView.as_view(template_name="faq.html"), name="faq"),
    path("support/", TemplateView.as_view(template_name="support.html"), name="support"),
    path("complaint/", TemplateView.as_view(template_name="complaint.html"), name="complaint"),
    path("feedback/", TemplateView.as_view(template_name="feedback.html"), name="feedback"),
    path("contact/", TemplateView.as_view(template_name="contact.html"), name="contact"),  # ✅ add this

]

# ---------------- Static & Media (development only) ----------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

