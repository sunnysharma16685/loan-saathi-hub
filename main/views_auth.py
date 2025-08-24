from django.shortcuts import render, redirect
from main.supabase_client import supabase_public, supabase_admin
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class SupabaseAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        pass  # Yahan apna Supabase auth logic daal sakte hain

def _set_auth_cookies(resp, session):
    resp.set_cookie(settings.SUPABASE_ACCESS_COOKIE, session.access_token)
    resp.set_cookie(settings.SUPABASE_REFRESH_COOKIE, session.refresh_token)

def _clear_auth_cookies(resp):
    resp.delete_cookie(settings.SUPABASE_ACCESS_COOKIE)
    resp.delete_cookie(settings.SUPABASE_REFRESH_COOKIE)

def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        res = supabase_public().auth.sign_up({"email": email, "password": password})
        user = getattr(res, "user", None)
        session = getattr(res, "session", None)

        if user:
            supabase_admin().table("main_profile").insert({
                "user_id": user.id,
                "email": email,
                "role": role,
            }).execute()

        if session:
            resp = redirect("dashboard_router")
            _set_auth_cookies(resp, session)
            return resp

        return render(request, "auth/check_email.html", {"email": email})

    return render(request, "auth/signup.html")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        res = supabase_public().auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

        user = getattr(res, "user", None)
        session = getattr(res, "session", None)

        if not session:
            return render(request, "auth/login.html", {"error": "Invalid credentials"})

        if user:
            admin = supabase_admin()
            prof = admin.table("main_profile").select("id").eq("user_id", user.id).limit(1).execute().data
            if not prof:
                admin.table("main_profile").insert({
                    "user_id": user.id,
                    "email": user.email,
                }).execute()

            resp = redirect("dashboard_router")
            _set_auth_cookies(resp, session)
            return resp

    return render(request, "auth/login.html")

def logout_view(request):
    try:
        supabase_public().auth.sign_out()
    except Exception:
        pass
    resp = redirect("login")
    _clear_auth_cookies(resp)
    return resp

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        redirect_to = request.build_absolute_uri("/auth/reset-password/")
        supabase_public().auth.reset_password_for_email(email, {"redirect_to": redirect_to})
        return render(request, "auth/check_email.html", {"email": email})
    return render(request, "auth/forgot_password.html")