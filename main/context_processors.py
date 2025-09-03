# main/context_processors.py
def user_profile(request):
    if request.user.is_authenticated:
        return {"profile": getattr(request.user, "profile", None)}
    return {}
