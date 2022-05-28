from __future__ import absolute_import, unicode_literals
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from main.models import Room


@shared_task
def delete_rooms_without_listeners():
    """
    This task will delete room where last_visited date is >1 day.
    So if listeners didn't perform any actions within 1 day the room will be removed.
    """
    expiration_date = timezone.now() - timedelta(days=1)
    rooms = Room.objects.filter(last_visited__lte=expiration_date)
    rooms_count = rooms.count()
    rooms.delete()

    return {"detail": f"{rooms_count} rooms has been deleted."}
