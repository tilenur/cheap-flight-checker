# The Celery app.
#
#   worker = runs our tasks in the background
#   Beat   = the clock that says "it's 9:00, run the task!"

import os

from celery import Celery

# Tell Celery where Django's settings are (so it can use our models)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Create the app. "config" is just its name (same as the project folder).
app = Celery("config")

# Read the settings that start with CELERY_ from settings.py
# (CELERY_BROKER_URL, CELERY_TIMEZONE, CELERY_BEAT_SCHEDULE)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Find tasks.py in every installed app (like flights/tasks.py)
app.autodiscover_tasks()
