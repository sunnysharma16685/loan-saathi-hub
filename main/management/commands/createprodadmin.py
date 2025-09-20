from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create a default superuser in production if it does not exist"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # 👇 apna email / password yahan set karo
        email = "loansaathihub@gmail.com"
        password = "Ridh@1637"

        try:
            if not User.objects.filter(email=email).exists():
                User.objects.create_superuser(email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"✅ Superuser created: {email}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Superuser already exists: {email}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to create superuser: {e}"))
