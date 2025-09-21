from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "List all users with their roles and superuser/staff flags (without exposing passwords)"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users = User.objects.all().order_by("created_at")

        if not users.exists():
            self.stdout.write(self.style.WARNING("⚠️ No users found in database"))
            return

        self.stdout.write(self.style.SUCCESS("📋 User List:"))
        self.stdout.write("-" * 70)
        for u in users:
            self.stdout.write(
                f"{u.email:35} | role={u.role:<10} | superuser={u.is_superuser:<5} | staff={u.is_staff:<5}"
            )
        self.stdout.write("-" * 70)
        self.stdout.write(self.style.SUCCESS(f"✅ Total users: {users.count()}"))
