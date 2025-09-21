import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create a default superuser in production if it does not exist (password hidden via env vars)"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # ✅ Password hardcode na karein, env vars se read karein
        email = os.getenv("ADMIN_EMAIL", "loansaathihub@gmail.com")
        password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")  # fallback default

        try:
            user = User.objects.filter(email=email).first()
            if not user:
                User.objects.create_superuser(
                    email=email,
                    password=password,
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Superuser created: {email}"))
            else:
                # Safety: ensure staff/superuser flags set ho
                if not user.is_superuser or not user.is_staff:
                    user.is_superuser = True
                    user.is_staff = True
                    user.set_password(password)  # reset password agar needed ho
                    user.save()
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ User {email} existed but updated as superuser")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ Superuser already exists: {email}")
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to create superuser: {e}"))
