from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.test import SimpleTestCase, override_settings
from main.models import CustomUser, Room
from main.tests.utils import build_communicator
from main.services import MusicRoomConsumerService
from main import consts


class MusicRoomConsumerServiceTestCase(SimpleTestCase):

    __slots__ = ('user', 'room', 'room_playlist')
    databases = '__all__'

    def setUp(self):
        self.user, _ = CustomUser.objects.get_or_create(username="test1", email="test1@gmail.com", password="112345Aa")
        self.user2, _ = CustomUser.objects.get_or_create(username="test2", email="test2@gmail.com", password="112345Aa")
        self.host, _ = CustomUser.objects.get_or_create(username="host", email="host@gmail.com", password="112345Aa")

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_check_permission(self):
        room = await sync_to_async(Room.objects.create)(host=self.host)
        communicator = await build_communicator(self.user, room.id)
        # Add track action will be permitted
        room.permissions[consts.ADD_TRACK_EVENT] = consts.ROOM_ADMIN_ONLY
        await sync_to_async(room.save)()

        channel_layer = get_channel_layer()
        service = MusicRoomConsumerService(communicator.scope, channel_layer, "testname1")
        # Allowed to any listener
        is_allowed = await service._check_permission(consts.CHANGE_TRACK_EVENT)
        self.assertTrue(is_allowed)
        # Not allowed (only host)
        is_allowed = await service._check_permission(consts.ADD_TRACK_EVENT)
        self.assertFalse(is_allowed)
        # Check as host
        service.user = self.host
        is_allowed = await service._check_permission(consts.ADD_TRACK_EVENT)
        self.assertTrue(is_allowed)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_is_user_muted(self):
        room = await sync_to_async(Room.objects.create)(host=self.host)
        await sync_to_async(room.mute_list.add)(self.user2.id)
        communicator = await build_communicator(self.user2, room.id)
        channel_layer = get_channel_layer()
        service = MusicRoomConsumerService(communicator.scope, channel_layer, "testname1")

        # Check as muted user
        is_muted = await service._is_user_muted()
        self.assertTrue(is_muted)
        # Check as non-muted user
        service.user = self.user
        is_muted = await service._is_user_muted()
        self.assertFalse(is_muted)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_is_user_banned(self):
        room = await sync_to_async(Room.objects.create)(host=self.host)
        await sync_to_async(room.ban_list.add)(self.user2.id)
        communicator = await build_communicator(self.user2, room.id)
        channel_layer = get_channel_layer()
        service = MusicRoomConsumerService(communicator.scope, channel_layer, "testname1")

        # Check as banned user
        is_banned = await service._is_user_banned()
        self.assertTrue(is_banned)
        # Check as non-banned user
        service.user = self.user
        is_banned = await service._is_user_banned()
        self.assertFalse(is_banned)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_is_room_full(self):
        room = await sync_to_async(Room.objects.create)(host=self.host, max_connections=0)
        communicator = await build_communicator(self.user, room.id)
        channel_layer = get_channel_layer()
        service = MusicRoomConsumerService(communicator.scope, channel_layer, "testname1")

        # max_connections = 0
        is_full = await service._is_room_full()
        self.assertTrue(is_full)
        # max_connections = 1
        room.max_connections = 1
        await sync_to_async(room.save)()
        is_full = await service._is_room_full()
        self.assertFalse(is_full)

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
