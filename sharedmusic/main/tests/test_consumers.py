from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.test import SimpleTestCase, override_settings
from main.models import CustomUser, Room, RoomPlaylist
from main.tests.utils import build_communicator


class MusicRoomConsumerTestCase(SimpleTestCase):

    __slots__ = ('user', 'room', 'room_playlist')
    databases = '__all__'

    def setUp(self):
        self.user, _ = CustomUser.objects.get_or_create(username="test1", email="test1@gmail.com", password="112345Aa")
        self.user2, _ = CustomUser.objects.get_or_create(username="test2", email="test2@gmail.com", password="112345Aa")
        self.room, _ = Room.objects.get_or_create(host=self.user)
        self.room_playlist, _ = RoomPlaylist.objects.get_or_create(room=self.room)

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_connect_disconnect(self):
        rooms_count = await sync_to_async(Room.objects.count)()
        self.assertEqual(rooms_count, 1)
        communicator = await build_communicator(self.user, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        # In the end we need to manually disconnect (described in the docs)
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_receive(self):
        """
        Most of receive method event handlers covered in test_services.py.
        Here we test default handler.
        """
        communicator = await build_communicator(self.user, self.room.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        # Send event
        await communicator.send_json_to({"message": "Hello world!", "event": "TEST"})
        # Handler result response
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response, {'payload': {'type': 'send_message', 'event': 'TEST', 'message': 'Hello world!'}})
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_channel_layer(self):
        communicator = await build_communicator(self.user, self.room.id)
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        # Channel layer check
        channel_layer = get_channel_layer()
        self.assertEqual(len(channel_layer.groups), 2)
        await communicator.disconnect()
