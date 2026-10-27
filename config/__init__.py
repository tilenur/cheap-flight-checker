# This file runs when Django starts.
# Importing the Celery app here makes it start together with Django,
# so @shared_task in flights/tasks.py knows which app to use.
from .celery import app as celery_app

# The names this package shares when someone imports it
__all__ = ("celery_app",)
