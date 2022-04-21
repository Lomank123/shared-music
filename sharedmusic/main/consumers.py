import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from main.models import Room, Soundtrack, Playlist, PlaylistItem
from main import consts
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async


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
            # Update current track
            playlist_item = await self.find_playlist_item()
            if playlist_item is not None:
                await self.channel_layer.group_send(self.user_group_name, {
                    'type': 'send_message',
                    'event': consts.CHANGE_SONG_EVENT,
                    'playlist_item': {
                        'order': playlist_item.order,
                        'name': playlist_item.soundtrack.name,
                        'url': playlist_item.soundtrack.url,
                    }
                })
        elif event == consts.CHANGE_SONG_EVENT:
            playlist_item = await self.add_track(message)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'event': consts.CHANGE_SONG_EVENT,
                'message': f"Song changed by {self.user.username}.",
                'playlist_item': {
                    'order': playlist_item.order,
                    'name': playlist_item.soundtrack.name,
                    'url': playlist_item.soundtrack.url,
                },
            })
        elif event == consts.CHANGE_SONG_ERROR_EVENT:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': message,
                'event': consts.CHANGE_SONG_ERROR_EVENT,
            })
        elif event == consts.NEW_USER_JOINED_EVENT:
            new_user = response.get("user", None)
            await self.channel_layer.group_send(f"user_{new_user}", {
                'type': 'send_message',
                'message': f"Retrieving current time.",
                'current_time': message,
                'is_paused': response.get("is_paused", None),
                'event': consts.CHANGE_CURRENT_TIME_EVENT,
            })
        else:
            # Send message to room group
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': message,
                'event': event,
                'count': count,
            })
        
    async def add_track(self, url):
        # Get room playlist
        playlist = await Room.get_room_playlist(self.room_name)
        # Get or create soundtrack (by given url)
        soundtrack, created = await database_sync_to_async(Soundtrack.objects.get_or_create)(url=url)
        # Set new current track
        playlist.current_track = soundtrack
        await database_sync_to_async(playlist.save)()
        # Create and return PlaylistItem
        playlist_item = await database_sync_to_async(PlaylistItem.objects.create)(soundtrack=soundtrack, playlist=playlist)
        return playlist_item

    async def find_playlist_item(self):
        playlist = await Room.get_room_playlist(self.room_name)
        playlist_item = await PlaylistItem.get_playlist_item(playlist)
        return playlist_item

    async def send_message(self, res):
        """
        Receive message from room group
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "payload": res,
        }))
