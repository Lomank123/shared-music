from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'sharedmusic.settings')

app = Celery("sharedmusic")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    'delete-rooms-without-listeners': {
        'task': 'main.tasks.delete_rooms_without_listeners',
        'schedule': 3600.0,
    },
}

app.autodiscover_tasks()