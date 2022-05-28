from django.test import TestCase
from sharedmusic.celery import app
from main.models import Room, CustomUser
from main.tasks import delete_rooms_without_listeners


class CeleryTasksTestCase(TestCase):

    def setUp(self):
        app.conf.update(CELERY_ALWAYS_EAGER=True, BROKER_BACKEND='memory')
        self.host1 = CustomUser.objects.create(username="test1", password="112345Aa")
        self.room1 = Room.objects.create(host=self.host1)

    def test_delete_rooms_without_listeners(self):
        # Don't know how to test it with deletions
        # Even if you pass last_visited in constructor it'll be overriden in save() method.
        self.assertEqual(Room.objects.count(), 1)
        task = delete_rooms_without_listeners.apply()
        self.assertEqual(task.status, 'SUCCESS')
        deleted_rooms = Room.objects.filter(is_deleted=True).count()
        self.assertEqual(deleted_rooms, 0)
