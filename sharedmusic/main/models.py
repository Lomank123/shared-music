from django.db import models
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.db import connection
from django.core import validators
from django.contrib.auth.models import AbstractUser

from main import consts


class CustomUser(AbstractUser):

    def __str__(self):
        return self.username


class Playlist(models.Model):
    name = models.CharField(default="Playlist", max_length=120, verbose_name="Name")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")

    def __str__(self):
        return f"{self.name} ({self.id})"

    class Meta:
        verbose_name_plural = 'Playlists'
        verbose_name = 'Playlist'
        ordering = ['-id']


class Soundtrack(models.Model):
    name = models.CharField(default="Soundtrack", max_length=120, verbose_name="Name")
    url = models.URLField(max_length=2000, verbose_name="URL")
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, verbose_name="Playlist")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")

    class Meta:
        verbose_name_plural = 'Soundtracks'
        verbose_name = 'Soundtrack'
        ordering = ['-id']


class Room(models.Model):
    code = models.SlugField(max_length=120, unique=True, verbose_name="Code")
    host = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="host", verbose_name="Host")
    listeners = models.ManyToManyField(get_user_model(), blank=True, related_name="listeners", verbose_name="Listeners")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")
    playlist = models.OneToOneField(Playlist, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Playlist")

    @classmethod
    @database_sync_to_async
    def get_room_playlist(cls, room_name):
        room = cls.objects.filter(code=room_name).select_related("playlist").first()
        playlist = room.playlist
        return playlist

    @classmethod
    @database_sync_to_async
    def add_listener(cls, room_name, user):
        room = cls.objects.filter(code=room_name).first()
        if room is not None:
            room.listeners.add(user)
            return {consts.SUCCESS_KEY: consts.LISTENER_ADDED}
        return {consts.ERROR_KEY: consts.ROOM_NOT_FOUND}

    @classmethod
    @database_sync_to_async
    def remove_listener(cls, room_name, user):
        room = cls.objects.filter(code=room_name).first()
        if room is not None:
            room.listeners.remove(user)
            return {consts.SUCCESS_KEY: consts.LISTENER_REMOVED}
        return {consts.ERROR_KEY: consts.ROOM_NOT_FOUND}

    @classmethod
    @database_sync_to_async
    def listeners_count(cls, room_name):
        """
        Returns amount of listeners in the room.
        """
        room = cls.objects.filter(code=room_name).first()
        if room is not None:
            return room.listeners.count()
        return {consts.ERROR_KEY: consts.ROOM_NOT_FOUND}

    @classmethod
    @database_sync_to_async
    def get_listeners(cls, room_name):
        listeners = cls.objects.get(code=room_name).listeners.values("username")
        return list(listeners)

    class Meta:
        verbose_name_plural = "Rooms"
        verbose_name = "Room"
        ordering = ["-id"]
