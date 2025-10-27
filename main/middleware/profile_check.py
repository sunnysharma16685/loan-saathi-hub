from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from main.models import Profile
from main.views import is_profile_complete  # ✅ Use your improved version

EXEMPT_PATHS = [
    "/login/",
    "/register/",
    "/verify-otp/",
    "/logout/",
    "/admin/",
    "/profile-form/",
    "/static/",
    "/media/",
]

class ProfileCompletionMiddleware:
    """
    Blocks logged-in users from accessing any page
    until their profile is complete and admin-approved.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        path = request.path.lower()

        # ✅ Skip if public path
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return self.get_response(request)

        # ✅ Only for logged-in users (not superuser)
        if user.is_authenticated and not user.is_superuser:
            profile = getattr(user, "profile", None)

            # 🔒 Profile completion check
            if not is_profile_complete(user):
                if "profile-form" not in path:
                    messages.warning(request, "Please complete your profile to continue.")
                    return redirect(reverse("profile_form", args=[user.id]))

            # 🔒 Admin review check
            if profile and not profile.is_reviewed and "review-profile" not in path:
                messages.info(request, "Your profile is under admin review.")
                return redirect("review_profile")

        return self.get_response(request)
