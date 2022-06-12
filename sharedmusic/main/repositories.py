from main.models import Room, RoomPlaylist, Soundtrack, RoomPlaylistTrack, CustomUser, ChatMessage
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
    def is_user_muted(room_id, user_id):
        """
        Returns True if room's mute_list contains user.
        """
        mute_list = Room.objects.filter(id=room_id).values_list('mute_list', flat=True)
        return user_id in mute_list

    @staticmethod
    @database_sync_to_async
    def is_user_banned(room_id, user_id):
        """
        Returns True if room's ban_list contains user.
        """
        ban_list = Room.objects.filter(id=room_id).values_list('ban_list', flat=True)
        return user_id in ban_list

    @staticmethod
    @database_sync_to_async
    def add_listener(room_id, user_id):
        """
        Attaches user to room as listener.
        """
        room = Room.objects.get(id=room_id)
        room.listeners.add(user_id)

    @staticmethod
    @database_sync_to_async
    def remove_listener(room_id, user_id):
        """
        Removes user from room.
        """
        room = Room.objects.get(id=room_id)
        room.listeners.remove(user_id)

    @staticmethod
    @database_sync_to_async
    def get_listeners_info(room_id):
        """
        Get all usernames and their count from room.
        """
        listeners = (
            Room.objects.filter(id=room_id)
            .annotate(username=F("listeners__username"))
            .values("username")
        )
        data = {
            'count': listeners.count(),
            'users': list(listeners),
        }
        return data

    @staticmethod
    @database_sync_to_async
    def change_host(room_id, new_host_id):
        """
        Changes host of room.
        """
        room = Room.objects.get(id=room_id)
        room.host_id = new_host_id
        room.save()

    @staticmethod
    @database_sync_to_async
    def mute_user(room_id, user_id):
        """
        Adds user to mute list.
        """
        room = Room.objects.get(id=room_id)
        room.mute_list.add(user_id)

    @staticmethod
    @database_sync_to_async
    def unmute_user(room_id, user_id):
        """
        Removes user from mute list.
        """
        room = Room.objects.get(id=room_id)
        room.mute_list.remove(user_id)

    @staticmethod
    @database_sync_to_async
    def ban_user(room_id, user_id):
        """
        Adds user to ban list.
        """
        room = Room.objects.get(id=room_id)
        room.ban_list.add(user_id)

    @staticmethod
    @database_sync_to_async
    def unban_user(room_id, user_id):
        """
        Removes user from ban list.
        """
        room = Room.objects.get(id=room_id)
        room.ban_list.remove(user_id)

    @staticmethod
    @database_sync_to_async
    def get_room_mute_list(room_id):
        """
        Returns room's mute list.
        """
        mute_list = list(
            Room.objects.filter(id=room_id)
            .annotate(username=F("mute_list__username"))
            .values("username")
        )
        if mute_list[0]["username"] is None:
            return list()
        return mute_list

    @staticmethod
    @database_sync_to_async
    def get_room_ban_list(room_id):
        """
        Returns room's ban list.
        """
        ban_list = list(
            Room.objects.filter(id=room_id)
            .annotate(username=F("ban_list__username"))
            .values("username")
        )
        if ban_list[0]["username"] is None:
            return list()
        return ban_list


class RoomPlaylistRepository():

    @staticmethod
    @database_sync_to_async
    def get_playlist_tracks(room_id):
        """
        Returns list of urls and names of tracks which are in given playlist.
        """
        # IMHO this query can be optimized
        soundtracks = RoomPlaylist.objects.get(room_id=room_id).tracks.annotate(
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
        return Soundtrack.objects.get(url=url, name=name)


class RoomPlaylistTrackRepository():

    @staticmethod
    @database_sync_to_async
    def get_or_create(track_id, playlist_id):
        new_playlist_track, created = RoomPlaylistTrack.objects.get_or_create(
            track_id=track_id,
            playlist_id=playlist_id
        )
        return new_playlist_track, created

    @staticmethod
    @database_sync_to_async
    def get_by_track_and_playlist(track_id, playlist_id):
        return RoomPlaylistTrack.objects.get(track_id=track_id, playlist_id=playlist_id)

    @staticmethod
    @database_sync_to_async
    def delete(playlist_track):
        playlist_track.delete()


class CustomUserRepository():

    @staticmethod
    @database_sync_to_async
    def get_by_username_or_none(username):
        return CustomUser.objects.filter(username=username).first()


class ChatMessageRepository():

    @staticmethod
    @database_sync_to_async
    def create(room_id, user_id, message):
        chat_message = ChatMessage.objects.create(room_id=room_id, sender_id=user_id, message=message)
        return chat_message

    @staticmethod
    @database_sync_to_async
    def get_recent_messages(room_id, amount=20):
        """
        Returns the list of recent messages. The number depends on amount arg.
        """
        chat_messages = list(
            ChatMessage.objects
            .filter(room_id=room_id)
            .order_by("timestamp")[:amount]
            .annotate(username=F('sender__username'))
            .values("username", "message", "timestamp")
        )
        return chat_messages
