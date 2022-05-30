from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import Client, SimpleTestCase, override_settings
from main.models import CustomUser, Room, RoomPlaylist
from sharedmusic.asgi import application


class MusicRoomConsumerTestCase(SimpleTestCase):
    databases = '__all__'

    __slots__ = ('user', 'room', 'room_playlist')

    def setUp(self):
        self.user, _ = CustomUser.objects.get_or_create(username="test1", email="test1@gmail.com", password="112345Aa")
        self.room, _ = Room.objects.get_or_create(host=self.user)
        self.room_playlist, _ = RoomPlaylist.objects.get_or_create(room=self.room)

    async def build_communicator(self, user, room_id) -> WebsocketCommunicator:
        """
        Constructs WebsocketCommunicator with authenticated user.
        """
        client = Client()
        # Authentication
        # force_login authenticates user (use exactly force_login(), login() method won't help)
        await sync_to_async(client.force_login)(user)
        # Then we need to set headers to communicator
        # With this our user will be logged in inside consumer
        # Thus we can receive events (e.g. connect event)
        # output() returns string representation of cookies
        # encode() encodes using UTF-8 by default
        client_cookies = client.cookies.output(header='', sep='; ').encode()
        headers = [
            (b'origin', b'...'),
            (b'cookie', client_cookies)
        ]
        # Communicator instance represent 1 connected user
        # If you want more than 1 user then create multiple communicators
        communicator = WebsocketCommunicator(application, f"/ws/room/{self.room.id}/", headers)
        # Return communicator with authenticated user
        return communicator

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_connect(self):
        rooms_count = await sync_to_async(Room.objects.count)()
        self.assertEqual(rooms_count, 1)

        communicator = await self.build_communicator(self.user, self.room.id)
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Send event
        await communicator.send_json_to({"message": "Hello world!", "event": "TEST"})
        # Handler result response
        response = await communicator.receive_json_from(timeout=1)
        await sync_to_async(print)(response)
        self.assertEqual(response, {'payload': {'type': 'send_message', 'event': 'TEST', 'message': 'Hello world!'}})

        # In the end we need to manually disconnect (described in the docs)
        await communicator.disconnect()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_channel_layer(self):
        communicator = await self.build_communicator(self.user, self.room.id)
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Channel layer check
        channel_layer = get_channel_layer()
        await sync_to_async(print)(channel_layer.groups)
        self.assertEqual(len(channel_layer.groups), 2)
        await communicator.disconnect()

    async def test_disconnect(self):
        pass

    async def test_default_receive(self):
        """
        Most of receive method event handlers covered in test_services.py.
        """
        pass

    async def test(self):
        self.assertEqual(1, 1)
