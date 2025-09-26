import multiprocessing

# Address & Port
bind = "0.0.0.0:{}".format(__import__("os").environ.get("PORT", "8000"))

# Worker settings
workers = 2  # Render free tier के लिए safe
threads = 2
worker_class = "gthread"

# Timeouts
timeout = 120
graceful_timeout = 30

# Performance
preload_app = True
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
