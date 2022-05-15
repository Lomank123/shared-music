import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from main import consts
from main.services import MusicRoomConsumerService
# from asgiref.sync import sync_to_async


class MusicRoomConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.service = MusicRoomConsumerService(self.scope, self.channel_layer, self.channel_name)
        # Handle authenticated user connection
        await self.service.connect_user()
        await self.accept()

    async def disconnect(self, close_code):
        await self.service.disconnect_user()

    async def receive(self, text_data):
        """
        Receives messages from WebSocket and calls handler.
        """
        response = json.loads(text_data)
        event = response.get("event", None)
        # Event handlers
        if event == consts.CONNECT_EVENT:
            await self.service.handle_connect(response)
        elif event == consts.ADD_TRACK_EVENT:
            await self.service.handle_add_track(response)
        elif event == consts.CHANGE_TRACK_EVENT:
            await self.service.handle_change_track(response)
        elif event == consts.SEND_TRACK_TO_NEW_USER:
            await self.service.handle_send_track_to_new_user(response)
        elif event == consts.CHANGE_TIME_EVENT:
            await self.service.handle_change_time(response)
        elif event == consts.DELETE_TRACK_EVENT:
            await self.service.handle_delete_track(response)
        elif event == consts.TRACK_ENDED_EVENT:
            await self.service.handle_track_ended(response)
        else:
            await self.service.handle_default(response)

    async def send_message(self, res):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"payload": res}))
