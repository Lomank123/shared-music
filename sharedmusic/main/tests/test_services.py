from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.test import SimpleTestCase, override_settings
from main.models import CustomUser, Room, RoomPlaylist, Soundtrack, RoomPlaylistTrack
from main.tests.utils import build_communicator
from main.services import MusicRoomConsumerService
from main import consts


class MusicRoomConsumerServiceTestCase(SimpleTestCase):

    databases = '__all__'

    def setUp(self):
        self.user = CustomUser.objects.create(username="test1", email="test1@gmail.com", password="112345Aa")
        self.user2 = CustomUser.objects.create(username="test2", email="test2@gmail.com", password="112345Aa")
        self.host = CustomUser.objects.create(username="host", email="host@gmail.com", password="112345Aa")
        self.room = Room.objects.create(host=self.host)
        self.room_playlist = RoomPlaylist.objects.create(room=self.room)
        self.soundtrack = Soundtrack.objects.create(
            name="Test track 1",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        self.room_playlist_track = RoomPlaylistTrack.objects.create(track=self.soundtrack, playlist=self.room_playlist)

    def tearDown(self):
        # To avoid IntegrityError and MultipleObjectsReturned
        self.user.delete()
        self.user2.delete()
        self.host.delete()
        self.room.delete()
        self.soundtrack.delete()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_check_permission(self):
        communicator = await build_communicator(self.user, self.room.id)
        # Add track action will be permitted
        self.room.permissions[consts.ADD_TRACK_EVENT] = consts.ROOM_ADMIN_ONLY
        await sync_to_async(self.room.save)()
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
        # Reset
        self.room.permissions[consts.ADD_TRACK_EVENT] = consts.ROOM_ALLOW_ANY
        await sync_to_async(self.room.save)()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_is_user_muted(self):
        await sync_to_async(self.room.mute_list.add)(self.user2.id)
        communicator = await build_communicator(self.user2, self.room.id)
        channel_layer = get_channel_layer()
        service = MusicRoomConsumerService(communicator.scope, channel_layer, "testname1")
        # Check as muted user
        is_muted = await service._is_user_muted()
        self.assertTrue(is_muted)
        # Check as non-muted user
        service.user = self.user
        is_muted = await service._is_user_muted()
        self.assertFalse(is_muted)
        await sync_to_async(self.room.mute_list.remove)(self.user2.id)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_is_user_banned(self):
        await sync_to_async(self.room.ban_list.add)(self.user2.id)
        communicator = await build_communicator(self.user2, self.room.id)
        channel_layer = get_channel_layer()
        service = MusicRoomConsumerService(communicator.scope, channel_layer, "testname1")
        # Check as banned user
        is_banned = await service._is_user_banned()
        self.assertTrue(is_banned)
        # Check as non-banned user
        service.user = self.user
        is_banned = await service._is_user_banned()
        self.assertFalse(is_banned)
        await sync_to_async(self.room.ban_list.remove)(self.user2.id)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_is_room_full(self):
        communicator = await build_communicator(self.user, self.room.id)
        channel_layer = get_channel_layer()
        service = MusicRoomConsumerService(communicator.scope, channel_layer, "testname1")
        # max_connections = 0
        self.room.max_connections = 0
        await sync_to_async(self.room.save)()
        is_full = await service._is_room_full()
        self.assertTrue(is_full)
        # max_connections = 20
        self.room.max_connections = 20
        await sync_to_async(self.room.save)()
        is_full = await service._is_room_full()
        self.assertFalse(is_full)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_connect_user(self):
        channel_layer = get_channel_layer()
        # 2 cases, when 2 users connect and when same user connects twice (multiple tabs)
        communicator = await build_communicator(self.user, self.room.id)
        communicator2 = await build_communicator(self.user2, self.room.id)
        communicator3 = await build_communicator(self.user, self.room.id)
        group_channel_name = f'{consts.USER_GROUP_PREFIX}_{self.user.username}'
        room_group_name = f'{consts.ROOM_GROUP_PREFIX}_{self.room.id}'

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        listeners = await sync_to_async(self.room.listeners.all)()
        listeners_count = await sync_to_async(listeners.count)()
        self.assertEqual(listeners_count, 1)
        self.assertEqual(len(channel_layer.groups), 2)

        connected, _ = await communicator2.connect()
        self.assertTrue(connected)
        listeners = await sync_to_async(self.room.listeners.all)()
        listeners_count = await sync_to_async(listeners.count)()
        self.assertEqual(listeners_count, 2)
        self.assertEqual(len(channel_layer.groups), 3)

        # Test remove_old_connections method

        # For now there's 1 channel in user's group
        user_channels_count = len(channel_layer.groups[group_channel_name])
        room_channels_count = len(channel_layer.groups[room_group_name])
        self.assertEqual(user_channels_count, 1)
        self.assertEqual(room_channels_count, 2)
        # Trying to connect as the same user
        connected, _ = await communicator3.connect()
        self.assertTrue(connected)
        # Check if there's still 1 channel
        user_channels_count = len(channel_layer.groups[group_channel_name])
        room_channels_count = len(channel_layer.groups[room_group_name])
        self.assertEqual(user_channels_count, 1)
        self.assertEqual(room_channels_count, 2)
        listeners = await sync_to_async(self.room.listeners.all)()
        listeners_count = await sync_to_async(listeners.count)()
        self.assertEqual(listeners_count, 2)
        await communicator.disconnect()
        await communicator2.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_disconnect_user(self):
        channel_layer = get_channel_layer()
        communicator = await build_communicator(self.user, self.room.id)
        communicator2 = await build_communicator(self.user2, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        connected, _ = await communicator2.connect()
        self.assertTrue(connected)
        listeners = await sync_to_async(self.room.listeners.all)()
        listeners_count = await sync_to_async(listeners.count)()
        self.assertEqual(listeners_count, 2)
        self.assertEqual(len(channel_layer.groups), 3)
        # Disconnect
        await communicator.disconnect()
        self.assertEqual(len(channel_layer.groups), 2)
        response = await communicator2.receive_json_from(timeout=1)
        # Correct event
        self.assertEqual(response["payload"]["event"], consts.DISCONNECT_EVENT)
        # Listeners count changed
        listeners = await sync_to_async(self.room.listeners.all)()
        listeners_count = await sync_to_async(listeners.count)()
        self.assertEqual(listeners_count, 1)
        await communicator2.disconnect()
        self.assertEqual(len(channel_layer.groups), 0)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_connect(self):
        communicator = await build_communicator(self.user, self.room.id)
        communicator2 = await build_communicator(self.user2, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        connected, _ = await communicator2.connect()
        self.assertTrue(connected)
        await communicator2.send_json_to({"message": "Test", "event": consts.CONNECT_EVENT})
        # Here we receive 2 events: connect and get track from listeners
        response = await communicator.receive_json_from(timeout=1)
        response2 = await communicator.receive_json_from(timeout=1)
        response3 = await communicator2.receive_json_from(timeout=1)
        self.assertEqual(response["payload"]["event"], consts.CONNECT_EVENT)
        self.assertTrue('listeners' in response["payload"])
        self.assertTrue('permissions' in response["payload"])
        self.assertTrue('recent_messages' in response["payload"])
        self.assertEqual(response2["payload"]["event"], consts.GET_TRACK_FROM_LISTENERS_EVENT)
        self.assertEqual(response3["payload"]["event"], consts.CONNECT_EVENT)
        await communicator.disconnect()
        await communicator2.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_change_track(self):
        communicator = await build_communicator(self.user, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        track_data = {
            "name": self.soundtrack.name,
            "url": self.soundtrack.url,
        }
        data = {"message": "Test", "track": track_data, "event": consts.CHANGE_TRACK_EVENT}
        await communicator.send_json_to(data)
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response["payload"]["event"], consts.CHANGE_TRACK_EVENT)
        self.assertEqual(response["payload"]["track"], track_data)
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_add_track(self):
        communicator = await build_communicator(self.user, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        data = {
            "message": "Test",
            "name": "Random track name",
            "url": "https://www.youtube.com/watch?v=123123123",
            "event": consts.ADD_TRACK_EVENT
        }
        await communicator.send_json_to(data)
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response["payload"]["event"], consts.ADD_TRACK_EVENT)
        self.assertEqual(len(response["payload"]["playlist"]), 2)
        self.assertTrue(response["payload"]["created"])
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_delete_track(self):
        communicator = await build_communicator(self.user, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        track_data = {
            "name": self.soundtrack.name,
            "url": self.soundtrack.url,
        }
        data = {
            "message": "Test",
            "track": track_data,
            "chosenTrackUrl": self.soundtrack.url,
            "event": consts.DELETE_TRACK_EVENT
        }
        await communicator.send_json_to(data)
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response["payload"]["event"], consts.DELETE_TRACK_EVENT)
        self.assertEqual(len(response["payload"]["playlist"]), 0)
        self.assertEqual(response["payload"]["chosenTrackUrl"], self.soundtrack.url)
        self.assertEqual(response["payload"]["deletedTrackInfo"], track_data)
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_send_track_to_new_user(self):
        communicator = await build_communicator(self.user, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        track_data = {
            "name": self.soundtrack.name,
            "url": self.soundtrack.url,
        }
        data = {
            "message": "Test",
            "track": track_data,
            "user": self.user.username,
            "loop": False,
            "event": consts.SEND_TRACK_TO_NEW_USER_EVENT
        }
        await communicator.send_json_to(data)
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response["payload"]["event"], consts.SET_CURRENT_TRACK_EVENT)
        self.assertEqual(response["payload"]["track"], track_data)
        self.assertFalse(response["payload"]["loop"])
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_change_time(self):
        communicator = await build_communicator(self.user, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        time = "0:17"
        data = {"message": "Test", "time": time, "event": consts.CHANGE_TIME_EVENT}
        await communicator.send_json_to(data)
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response["payload"]["event"], consts.CHANGE_TIME_EVENT)
        self.assertEqual(response["payload"]["time"], time)
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_set_next_track(self):
        # TODO: Add 2 more cases (2 tracks, previous=False)
        communicator = await build_communicator(self.user, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        track_data = {
            "name": self.soundtrack.name,
            "url": self.soundtrack.url,
        }
        data = {
            "message": "Test",
            "track": track_data,
            "previous": True,
            "event": consts.TRACK_ENDED_EVENT
        }
        await communicator.send_json_to(data)
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response["payload"]["event"], consts.CHANGE_TRACK_EVENT)
        self.assertEqual(response["payload"]["track"], track_data)
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_chat_message(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_change_host(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_change_permissions(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_not_allowed(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_mute(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_unmute(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_listener_muted(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_ban(self):
        pass

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_handle_unban(self):
        pass
