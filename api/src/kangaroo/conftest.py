import os

# Force the in-memory backend before any app module is imported. The app builds
# its backends from DATABASE_URL at import time, so this must run first.
os.environ["DATABASE_URL"] = "memory://"
