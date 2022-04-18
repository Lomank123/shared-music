import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from main.models import Room
from main import consts


class MusicRoomConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.user = self.scope.get('user')
        self.room_name = self.scope['url_route']['kwargs']['code']
        self.room_group_name = f'{consts.ROOM_GROUP_PREFIX}_{self.room_name}'
        # User group must contain only one user
        self.user_group_name = f'{consts.USER_GROUP_PREFIX}_{self.user}'
        # Handle authenticated user connection
        if self.user.is_authenticated:
            await self.connect_user()
        await self.accept()

    async def connect_user(self):
        # Remove all previous connections of the same user if they exist
        await self.remove_old_connections()
        # Join groups
        for group_name in [self.room_group_name, self.user_group_name]:
            await self.channel_layer.group_add(group_name, self.channel_name)
        # Add new listener
        await Room.add_listener(self.room_name, self.user)

    async def remove_old_connections(self):
        """
        Removes all previous (old) channels from room and user groups.
        """
        try:
            # Create copy to iterate through
            user_group = self.channel_layer.groups[self.user_group_name].copy()
        except KeyError:
            user_group = {}
        # Remove old channel (if same user or multiple tabs)
        for channel in user_group:
            if channel != self.channel_name:
                # Send message to old channel to show alert
                await self.channel_layer.group_send(self.user_group_name, {
                    'type': 'send_message',
                    'message': consts.USER_ALREADY_IN_ROOM,
                    'event': consts.ALREADY_CONNECTED_EVENT,
                })
                # Leave groups
                for group_name in [self.room_group_name, self.user_group_name]:
                    await self.channel_layer.group_discard(group_name, channel)

    async def disconnect(self, close_code):
        if self.channel_name in self.channel_layer.groups[self.room_group_name]:
            # Removing listener
            if self.user.is_authenticated:
                await Room.remove_listener(self.room_name, self.user)
            # Send disconnect message to other listeners
            listeners = await Room.get_listeners(self.room_name)
            count = await Room.listeners_count(self.room_name)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': f"{self.user} {consts.USER_DISCONNECTED}",
                'event': consts.DISCONNECT_EVENT,
                'listeners': listeners,
                'count': count,
            })
            # Leave groups
            for group_name in [self.room_group_name, self.user_group_name]:
                await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Receive messages from WebSocket and sets appropriate event.
        """
        count = await Room.listeners_count(self.room_name)
        listeners = await Room.get_listeners(self.room_name)
        response = json.loads(text_data)
        event = response.get("event", None)
        message = response.get("message", None)

        if event == consts.CONNECT_EVENT:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': message,
                'event': consts.CONNECT_EVENT,
                'user': self.user.username,
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
