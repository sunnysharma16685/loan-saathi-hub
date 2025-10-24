from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

# ✅ Import all your main app views
from main import views


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
    path("dashboard/", views.dashboard_router, name="dashboard_router"),

  
    # ---------------------- Payment Gateway ---------------------
    path("payment/initiate/", views.initiate_payment, name="initiate_payment"),
    path("payment/callback/", views.payment_callback, name="payment_callback"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/failure/", views.payment_failure, name="payment_failure"),
    path("payment/invoice/", views.invoice_view, name="invoice"),


    # ---------------- Email OTP ----------------
    path("verify-email-otp/", views.verify_email_otp_view, name="verify_email_otp"),
    path("resend-email-otp/", views.resend_email_otp_view, name="resend_email_otp"),

    # ---------------- Loan + Payment ----------------
    path("loan/request/", views.loan_request, name="loan_request"),
    path("dashboard/lender/reject/<uuid:loan_id>/", views.reject_loan, name="reject_loan"),
    path("dashboard/lender/approve/<uuid:loan_id>/", views.approve_loan, name="approve_loan"),

    # ---------------- Applicant Loan Actions ----------------
    path("applicant/accept/<uuid:loan_id>/<uuid:lender_id>/", views.applicant_accept_loan, name="applicant_accept_loan"),

    # ---------------- Custom Admin ----------------
    path("admin_login/", views.admin_login, name="admin_login"),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path("admin/full_profile/<uuid:user_id>/", views.admin_view_profile, name="admin_full_profile"),
    path("admin/user_action/<uuid:user_id>/", views.admin_user_action, name="admin_user_action"),
    path("pricing-projection/", views.pricing_projection, name="pricing_projection"),

    # ---------------- Gmail (Admin Dashboard) ----------------
    path("dashboard/admin/emails/", views.admin_emails, name="admin_emails"),
    path("dashboard/admin/emails/compose/", views.admin_email_compose, name="admin_email_compose"),

    # ---------------- Support / Complaint / Feedback ----------------
    path("support/", views.support_view, name="support"),
    path("complaint/", views.complaint_view, name="complaint"),
    path("feedback/", views.feedback_view, name="feedback"),

    # ---------------- Static Footer Pages ----------------
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("terms/", TemplateView.as_view(template_name="terms.html"), name="terms"),
    path("privacy/", TemplateView.as_view(template_name="privacy.html"), name="privacy"),
    path("faq/", TemplateView.as_view(template_name="faq.html"), name="faq"),
    path("contact/", TemplateView.as_view(template_name="contact.html"), name="contact"),

    # ---------------- Django Admin (keep this at bottom) ----------------
    path("admin/", admin.site.urls),

    # ---------------- logo and images ---------------
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json')),

    # ----------------Offline fallback message ---------------
    path("offline/", views.offline_page, name="offline_page"),
    
]


# ---------------- Static & Media (development only) ----------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
