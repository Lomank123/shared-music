import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class MusicRoomConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['code']
        self.room_group_name = f'room_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print("Disconnected")

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Receive messages from WebSocket and sets appropriate event.
        """
        response = json.loads(text_data)
        event = response.get("event", None)
        message = response.get("message", None)

        # Sending message to room group
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'send_message',
            'message': message,
            'event': event,
        })

    async def send_message(self, res):
        """
        Receive message from room group
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "payload": res,
        }))
