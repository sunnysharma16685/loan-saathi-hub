#!/usr/bin/env python
import os
import sys
import logging

# ---------------------------------------------------------
# 🚀 Loan Saathi Hub — manage.py
# Purpose: Django management entry point with environment safety.
# ---------------------------------------------------------

def main():
    """Run administrative tasks."""
    # Ensure correct settings module is loaded
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "loan_saathi_hub.settings")

    # ✅ Optional: detect environment automatically
    if "RENDER" in os.environ:
        os.environ.setdefault("DJANGO_ENV", "production")
    else:
        os.environ.setdefault("DJANGO_ENV", "development")

    # ✅ Setup logging for visibility
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [INFO] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ✅ Safe environment info log
    env_mode = os.getenv("DJANGO_ENV", "development")
    razorpay_key = os.getenv("RAZORPAY_KEY_ID", "Not set")
    logging.info(f"✅ Environment loaded | RAZORPAY_KEY_ID: {razorpay_key[:8]}**** | Mode: {env_mode}")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # ✅ Execute the command
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
