import sys
import gzip
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from pathlib import Path

# ✅ Force UTF-8 output so Windows consoles handle emojis and Unicode
sys.stdout.reconfigure(encoding="utf-8")

class Command(BaseCommand):
    help = "📦 Create a timestamped JSON backup of all user and loan data (UTF-8 safe, compressed)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-compress",
            action="store_true",
            help="Save as plain .json instead of .json.gz",
        )

    def handle(self, *args, **options):
        timestamp = timezone.now().strftime("%Y_%m_%d_%H_%M")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        # Choose extension based on compression option
        ext = "json" if options["no_compress"] else "json.gz"
        file_path = backup_dir / f"backup_{timestamp}.{ext}"

        if options["no_compress"]:
            with open(file_path, "w", encoding="utf-8") as f:
                call_command("dumpdata", "--indent", 2, stdout=f)
        else:
            with gzip.open(file_path, "wt", encoding="utf-8") as f:
                call_command("dumpdata", "--indent", 2, stdout=f)

        self.stdout.write(self.style.SUCCESS(f"✅ Backup created at: {file_path}"))
        self.stdout.write(self.style.HTTP_INFO("💾 Keep this file safe! Use `loaddata` to restore later."))
