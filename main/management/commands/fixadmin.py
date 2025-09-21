import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Reset or create default admin (email & password from env vars)"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # ✅ Password ko hardcode na karein, env vars use karein
        email = os.getenv("ADMIN_EMAIL", "loansaathihub@gmail.com")
        password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")  # fallback default

        try:
            u = User.objects.filter(email=email).first()
            if u:
                u.set_password(password)
                u.is_superuser = True
                u.is_staff = True
                u.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Password reset for {email}"))
            else:
                User.objects.create_superuser(email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"✅ Superuser created: {email}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
