from channels.layers import get_channel_layer
from django.test import SimpleTestCase, override_settings
from main.models import CustomUser, Room
from main.tests.utils import build_communicator


class MusicRoomConsumerTestCase(SimpleTestCase):

    databases = '__all__'

    def setUp(self):
        self.user = CustomUser.objects.create(username="test1", email="test1@gmail.com", password="112345Aa")
        self.user2 = CustomUser.objects.create(username="test2", email="test2@gmail.com", password="112345Aa")
        self.room = Room.objects.create(host=self.user)

    def tearDown(self):
        # To avoid IntegrityError
        self.user.delete()
        self.user2.delete()
        self.room.delete()

    @override_settings(CHANNEL_LAYERS={'default': {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
    async def test_connect_disconnect(self):
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
