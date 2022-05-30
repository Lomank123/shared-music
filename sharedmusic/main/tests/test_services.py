from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.test import SimpleTestCase, override_settings
from main.models import CustomUser, Room, RoomPlaylist
from main.tests.utils import build_communicator


class MusicRoomConsumerServiceTestCase(SimpleTestCase):

    __slots__ = ('user', 'room', 'room_playlist')
    databases = '__all__'

    def setUp(self):
        self.user, _ = CustomUser.objects.get_or_create(username="test1", email="test1@gmail.com", password="112345Aa")
        self.user2, _ = CustomUser.objects.get_or_create(username="test2", email="test2@gmail.com", password="112345Aa")
        self.room, _ = Room.objects.get_or_create(host=self.user)
        self.room_playlist, _ = RoomPlaylist.objects.get_or_create(room=self.room)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_connect_user(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_disconnect_user(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_connect(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_change_track(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_add_track(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_delete_track(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_send_track_to_new_user(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_change_time(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_set_next_track(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_chat_message(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_change_host(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_change_permissions(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_not_allowed(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_mute(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_unmute(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_listener_muted(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_ban(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    def test_handle_unban(self):
        pass
