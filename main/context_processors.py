# main/context_processors.py
from django.conf import settings
from .models import PageAd

def user_profile(request):
    """
    Inject profile and profile completion status into templates.
    """
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        profile_complete = False
        if profile and profile.full_name and profile.mobile:
            # You can expand this check depending on which fields
            # are required to consider the profile "complete".
            profile_complete = True
        return {
            "profile": profile,
            "PROFILE_COMPLETE": profile_complete,
        }
    return {"PROFILE_COMPLETE": False}

def testing_mode(request):
    """
    Provides IS_TESTING and DEBUG to templates globally.
    """
    return {
        "IS_TESTING": getattr(settings, "IS_TESTING", False),
        "DEBUG": settings.DEBUG,
    }




def ads_context(request):
    current_page = request.resolver_match.view_name if request.resolver_match else None
    ads = PageAd.objects.filter(page=current_page, is_active=True)
    return {"ads_for_page": ads}
