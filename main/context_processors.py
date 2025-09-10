# main/context_processors.py
from django.conf import settings

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
