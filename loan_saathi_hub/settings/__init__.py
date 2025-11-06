import os

# =====================================================
# 🌍 Detect current environment
# =====================================================
env = os.getenv("DJANGO_ENV", "local").lower()  # 👈 define 'env' safely

# =====================================================
# 🧩 Load settings file based on environment
# =====================================================
if env == "production":
    from .render import *
elif env == "staging":
    from .staging import *
else:
    from .local import *

# =====================================================
# ✅ Optional Debug Info (only prints in console)
# =====================================================
print(f"🔧 Django Environment loaded: {env.upper()}")
