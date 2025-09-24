from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create or reset a superuser (admin) with given email and password."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Admin email")
        parser.add_argument("password", type=str, help="Admin password")

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"]
        password = options["password"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"is_staff": True, "is_superuser": True},
        )

        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Superuser created: {email}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚡ Superuser already existed, password reset: {email}"))
