from main.models import Room, Playlist, Soundtrack, PlaylistTrack, CustomUser
from channels.db import database_sync_to_async
from django.db.models import F


class RoomRepository():

    @staticmethod
    @database_sync_to_async
    def get_room_by_id_or_none(room_id):
        """
        Returns room by it's id or None.
        """
        room = Room.objects.filter(id=room_id).first()
        return room

    @staticmethod
    @database_sync_to_async
    def save_room(room):
        """
        Saves room.
        """
        room.save()

    @staticmethod
    @database_sync_to_async
    def get_room_playlist(room_id):
        """
        Returns playlist of current room.
        """
        room = Room.objects.select_related("playlist").get(id=room_id)
        playlist = room.playlist
        return playlist

    @staticmethod
    @database_sync_to_async
    def add_listener(room_id, user):
        """
        Attaches user to room.
        """
        room = Room.objects.get(id=room_id)
        room.listeners.add(user)

    @staticmethod
    @database_sync_to_async
    def remove_listener(room_id, user):
        """
        Removes user from room.
        """
        room = Room.objects.get(id=room_id)
        room.listeners.remove(user)

    @staticmethod
    @database_sync_to_async
    def get_listeners_info(room_id):
        """
        Get all usernames and their count from room.
        """
        room = Room.objects.get(id=room_id)
        data = {
            'count': room.listeners.count(),
            'users': list(room.listeners.values("username")),
        }
        return data

    @staticmethod
    @database_sync_to_async
    def change_host(room_id, new_host):
        """
        Changes host of room.
        """
        room = Room.objects.get(id=room_id)
        room.host = new_host
        room.save()


class PlaylistRepository():

    @staticmethod
    @database_sync_to_async
    def get_playlist_tracks(playlist):
        """
        Returns list of urls and names of tracks which are in given playlist.
        """
        soundtracks = Playlist.objects.get(id=playlist.id).tracks.annotate(
            name=F('track__name'),
            url=F('track__url')
        ).values("url", "name")
        return list(soundtracks)


class SoundtrackRepository():

    @staticmethod
    @database_sync_to_async
    def get_or_create(url, name):
        new_track, created = Soundtrack.objects.get_or_create(url=url, name=name)
        return new_track, created

    @staticmethod
    @database_sync_to_async
    def get_by_url_and_name(url, name):
        track = Soundtrack.objects.get(url=url, name=name)
        return track


class PlaylistTrackRepository():

    @staticmethod
    @database_sync_to_async
    def get_or_create(track, playlist):
        new_playlist_track, created = PlaylistTrack.objects.get_or_create(track=track, playlist=playlist)
        return new_playlist_track, created

    @staticmethod
    @database_sync_to_async
    def get_by_track_and_playlist(soundtrack, playlist):
        playlist_track = PlaylistTrack.objects.get(track=soundtrack, playlist=playlist)
        return playlist_track

    @staticmethod
    @database_sync_to_async
    def delete(playlist_track):
        playlist_track.delete()


class CustomUserRepository():

    @staticmethod
    @database_sync_to_async
    def get_by_username_or_none(username):
        """
        Returns user by it's username or None.
        """
        user = CustomUser.objects.filter(username=username).first()
        return user
