@echo off
REM ============================================================
REM 🚀 Loan Saathi Hub — Local DB Reset Script
REM ============================================================

echo.
echo ============================================
echo 🔁 Resetting Local SQLite Database
echo ============================================

REM -- Activate your virtual environment
call .venv312\Scripts\activate

REM -- Delete existing SQLite DB
if exist db.sqlite3 (
    del db.sqlite3
    echo 🗑️  Deleted old db.sqlite3
) else (
    echo ⚠️  No old database found — continuing...
)

REM -- Make and apply migrations
echo.
echo 🔨 Running migrations...
python manage.py makemigrations
python manage.py migrate

REM -- Create default superuser
echo.
set SUPER_EMAIL=mr.sunnysharma85@gmail.com
set SUPER_PASS=Krishu@1637
echo 👤 Creating default superuser: %SUPER_EMAIL%

python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u=User.objects.filter(is_superuser=True).first() or User.objects.create_superuser('%SUPER_EMAIL%', '%SUPER_PASS%'); u.set_password('%SUPER_PASS%'); u.save(); print('✅ Superuser ready! Email:', u.email)"


echo.
echo ============================================
echo ✅ Local DB reset complete!
echo 👤 Login credentials:
echo     Email:    %SUPER_EMAIL%
echo     Password: %SUPER_PASS%
echo ============================================
echo.

pause
