#!/usr/bin/env bash
# ===============================================
# 🚀 Loan Saathi Hub — Render Build Script
# Safe, repeatable, and idempotent build setup
# ===============================================

set -o errexit  # Exit immediately on error

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗄️ Checking and applying database migrations safely..."

# Step 1 — Fake initial migrations for existing tables (avoids 'relation already exists' errors)
python manage.py migrate --fake-initial --noinput || true

# Step 2 — Ensure system apps (admin, auth, contenttypes) are marked as migrated
python manage.py migrate --fake admin zero || true
python manage.py migrate --fake-initial --noinput || true

# Step 3 — Apply any new migrations normally
python manage.py migrate --noinput

echo "✅ Build completed successfully!"
