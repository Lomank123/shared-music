from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import SimpleTestCase
from main.models import CustomUser, Room, RoomPlaylist
from sharedmusic.asgi import application


class MusicRoomConsumerTestCase(SimpleTestCase):
    databases = '__all__'

    __slots__ = ('user', 'room', 'room_playlist', 'communicator')

    def setUp(self):
        pass

    async def test_connect(self):
        self.user, _ = await sync_to_async(
            CustomUser.objects.get_or_create
        )(username="test1", email="test1@gmail.com", password="112345Aa")
        self.room, _ = await sync_to_async(Room.objects.get_or_create)(host=self.user)
        self.room_playlist, _ = await sync_to_async(RoomPlaylist.objects.get_or_create)(room=self.room)

        rooms_count = await sync_to_async(Room.objects.count)()
        self.assertEqual(rooms_count, 1)

        # Authentication
        # force_login authenticates user (use exactly force_login(), login() method won't help)
        await sync_to_async(self.client.force_login)(self.user)
        # Then we need to set headers to communicator
        # With this our user will be logged in inside consumer
        # Thus we can receive events (e.g. connect event)
        # output() returns string representation of cookies
        # encode() encodes using UTF-8 by default
        client_cookies = self.client.cookies.output(header='', sep='; ').encode()
        headers = [
            (b'origin', b'...'),
            (b'cookie', client_cookies)
        ]
        self.communicator = WebsocketCommunicator(application, f"/ws/room/{self.room.id}/", headers)

        # Connect
        connected, subprotocol = await self.communicator.connect()
        self.assertTrue(connected)

        # Send event
        await self.communicator.send_json_to({"message": "Hello world!", "event": "1"})

        # Channel layer check
        channel_layer = get_channel_layer()
        await sync_to_async(print)(channel_layer.groups)

        # Handler result response
        response = await self.communicator.receive_json_from(timeout=1)
        await sync_to_async(print)(response)
        # assert response == {'event': 'NOTHING', 'message': 'Hello world!'}

        # In the end we need to manually disconnect (described in the docs)
        await self.communicator.disconnect()

    @database_sync_to_async
    def get_session(self):
        self.client.login(username="test1", password="112345Aa")
        return self.client.session

    async def test_disconnect(self):
        pass

    async def test_default_receive(self):
        """
        Most of receive method event handlers covered in test_services.py.
        """
        pass

    async def test(self):
        self.assertEqual(1, 1)
