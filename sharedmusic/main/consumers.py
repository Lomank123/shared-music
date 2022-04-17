import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from main.models import Room
from asgiref.sync import sync_to_async


class MusicRoomConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope.get('user')
        self.room_name = self.scope['url_route']['kwargs']['code']
        self.room_group_name = f'room_{self.room_name}'
        self.user_group_name = f'user_{user}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        try:
            user_group = self.channel_layer.groups[self.user_group_name].copy()
        except KeyError:
            user_group = None

        same_user_instances = []
        if user_group is not None:
            for us in user_group:
                if us != self.channel_name:
                    same_user_instances.append(us)
                    await self.channel_layer.group_send(self.user_group_name, {
                        'type': 'send_message',
                        'message': "Already connected. Refresh the page",
                        'event': 'ALREADY_CONNECTED'
                    })
                    await self.channel_layer.group_discard(
                        self.user_group_name,
                        us
                    )
            for us in same_user_instances:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    us
                )

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        sync_to_async(print(self.channel_layer.groups))

        # Adding new listener
        
        if user.is_authenticated:
            await Room.add_listener(self.room_name, user)

        await self.accept()

    async def disconnect(self, close_code):
        if self.channel_name in self.channel_layer.groups[self.room_group_name]:
            user = self.scope.get('user')
            # Removing listener
            if user.is_authenticated:
                    await Room.remove_listener(self.room_name, user)
            # Retrieving new list
            listeners = await Room.get_listeners(self.room_name)
            count = await Room.listeners_count(self.room_name)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': f"User {user} disconnected.",
                'event': "DISCONNECT",
                'listeners': listeners,
                'count': count,
            })
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Receive messages from WebSocket and sets appropriate event.
        """
        count = await Room.listeners_count(self.room_name)
        listeners = await Room.get_listeners(self.room_name)
        response = json.loads(text_data)
        event = response.get("event", None)
        message = response.get("message", None)
        user = self.scope.get('user')

        # If event == 'CONNECT' then we should add user to room instance
        if event == 'CONNECT':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': message,
                'event': 'CONNECT',
                'user': user.username,
                'count': count,
                'listeners': listeners,
            })
        elif event == 'DISCONNECT':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': message,
                'event': 'DISCONNECT',
                'count': count,
                'listeners': listeners,
            })
        else:
            # Sending message to room group
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': message,
                'event': event,
                'count': count
            })

    async def send_message(self, res):
        """
        Receive message from room group
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "payload": res,
        }))
