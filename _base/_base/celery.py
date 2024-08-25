"""Handles the following concurrent tasks
1. Sending of verification mails
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_base.settings")

# create celery instance
app = Celery("_base")


# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
