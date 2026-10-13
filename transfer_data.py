import os
import django
from django.db import connections, transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Your local SQLite database
sqlite = connections["default"]

# We'll add PostgreSQL as a separate connection
# using the Railway DATABASE_URL environment variable.