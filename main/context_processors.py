# main/context_processors.py

from django.conf import settings

def user_profile(request):
    if request.user.is_authenticated:
        return {"profile": getattr(request.user, "profile", None)}
    return {}

def testing_mode(request):
    """
    Provides IS_TESTING and DEBUG to templates globally.
    """
    return {
        "IS_TESTING": getattr(settings, "IS_TESTING", False),
        "DEBUG": settings.DEBUG,
    }

