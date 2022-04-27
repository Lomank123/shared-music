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


class Soundtrack(models.Model):
    name = models.CharField(default="Soundtrack", max_length=120, verbose_name="Name")
    url = models.URLField(max_length=2000, verbose_name="URL")
    #playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, verbose_name="Playlist")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")

    class Meta:
        verbose_name_plural = 'Soundtracks'
        verbose_name = 'Soundtrack'
        ordering = ['-id']


class Playlist(models.Model):
    name = models.CharField(default="Playlist", max_length=120, verbose_name="Name")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")
    tracks = models.ManyToManyField(Soundtrack, blank=True, related_name='tracks', verbose_name="Tracks")

    def __str__(self):
        return f"{self.name} ({self.id})"

    @classmethod
    @database_sync_to_async
    def get_playlist_tracks(cls, playlist):
        """
        Returns list of urls and names of tracks which are in given playlist.
        """
        soundtracks = cls.objects.filter(id=playlist.id).first().tracks.values("url", "name")
        return list(soundtracks)

    @classmethod
    @database_sync_to_async
    def remove_track(cls, playlist, track):
        """
        Removes track from given playlist.
        """
        playlist.tracks.remove(track)

    @classmethod
    @database_sync_to_async
    def add_track(cls, playlist, track):
        """
        Adds track to given playlist.
        """
        playlist.tracks.add(track)

    class Meta:
        verbose_name_plural = 'Playlists'
        verbose_name = 'Playlist'
        ordering = ['-id']


class Room(models.Model):
    code = models.SlugField(max_length=120, unique=True, verbose_name="Code")
    host = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="host", verbose_name="Host")
    listeners = models.ManyToManyField(get_user_model(), blank=True, related_name="listeners", verbose_name="Listeners")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation date")
    last_visited = models.DateTimeField(auto_now=True, verbose_name="Last visited")
    playlist = models.OneToOneField(Playlist, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Playlist")

    @classmethod
    @database_sync_to_async
    def get_room_playlist(cls, room_name):
        """
        Returns playlist of current room.
        """
        room = cls.objects.filter(code=room_name).select_related("playlist").first()
        playlist = room.playlist
        return playlist

    @classmethod
    @database_sync_to_async
    def add_listener(cls, room_name, user):
        """
        Attaches user to room and returns success message.
        If no room found by room_name then an error message will be returned.
        """
        room = cls.objects.filter(code=room_name).first()
        if room is not None:
            room.listeners.add(user)
            return {consts.SUCCESS_KEY: consts.LISTENER_ADDED}
        return {consts.ERROR_KEY: consts.ROOM_NOT_FOUND}

    @classmethod
    @database_sync_to_async
    def remove_listener(cls, room_name, user):
        """
        Removes user from room and returns success message.
        If no room found by room_name then an error message will be returned.
        """
        room = cls.objects.filter(code=room_name).first()
        if room is not None:
            room.listeners.remove(user)
            return {consts.SUCCESS_KEY: consts.LISTENER_REMOVED}
        return {consts.ERROR_KEY: consts.ROOM_NOT_FOUND}

    @classmethod
    def listeners_count(cls, room_name):
        """
        Returns amount of listeners in the room.
        """
        room = cls.objects.filter(code=room_name).first()
        if room is not None:
            return room.listeners.count()
        return {consts.ERROR_KEY: consts.ROOM_NOT_FOUND}

    @classmethod
    def get_listeners(cls, room_name):
        """
        Returns list of users who are in the room
        """
        listeners = cls.objects.get(code=room_name).listeners.values("username")
        return list(listeners)

    @classmethod
    @database_sync_to_async
    def get_listeners_info(cls, room_name):
        """
        Get all usernames and their count from room.
        """
        count = cls.listeners_count(room_name)
        listeners = cls.get_listeners(room_name)
        data = {
            'count': count,
            'users': listeners,
        }
        return data

    class Meta:
        verbose_name_plural = "Rooms"
        verbose_name = "Room"
        ordering = ["-id"]
