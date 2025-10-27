import os
from django.core.management.base import BaseCommand
from pathlib import Path

class Command(BaseCommand):
    help = "📜 View latest 100 lines of app and error logs."

    def add_arguments(self, parser):
        parser.add_argument("--errors", action="store_true", help="Show only errors.log")
        parser.add_argument("--app", action="store_true", help="Show only app_events.log")

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        log_dir = base_dir / "logs"

        app_log = log_dir / "app_events.log"
        error_log = log_dir / "errors.log"

        # Determine which files to show
        if options["errors"]:
            files_to_show = [error_log]
        elif options["app"]:
            files_to_show = [app_log]
        else:
            files_to_show = [app_log, error_log]

        for log_file in files_to_show:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n--- {log_file.name} ---"))
            if not log_file.exists():
                self.stdout.write(self.style.WARNING("⚠️  File not found."))
                continue

            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-100:]
                if not lines:
                    self.stdout.write(self.style.WARNING("⚠️  No log entries yet."))
                else:
                    for line in lines:
                        self.stdout.write(line.strip())
