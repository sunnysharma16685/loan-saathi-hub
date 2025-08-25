from django.core.management.base import BaseCommand
from main.supabase_client import supabase, supabase_admin


class Command(BaseCommand):
    help = "Check Supabase connectivity (anon + admin)"

    def handle(self, *args, **kwargs):
        try:
            # ✅ test anon client
            anon_tables = supabase.table("main_user").select("*").limit(1).execute()
            self.stdout.write(self.style.SUCCESS("✅ Anon client connected successfully"))
            self.stdout.write(str(anon_tables))

            # ✅ test admin client
            admin_tables = supabase_admin.table("main_user").select("*").limit(1).execute()
            self.stdout.write(self.style.SUCCESS("✅ Admin client connected successfully"))
            self.stdout.write(str(admin_tables))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Supabase connection failed: {e}"))
