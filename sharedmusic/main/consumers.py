import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from main.models import Room, Soundtrack, Playlist, PlaylistTrack
from main import consts
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async


class MusicRoomConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.user = self.scope.get('user')
        self.room_id = self.scope['url_route']['kwargs']['id']
        self.room_group_name = f'{consts.ROOM_GROUP_PREFIX}_{self.room_id}'
        # User group must contain only one user
        self.user_group_name = f'{consts.USER_GROUP_PREFIX}_{self.user.username}'
        self.playlist = await Room.get_room_playlist(self.room_id)
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
        await Room.add_listener(self.room_id, self.user)

    async def remove_old_connections(self):
        """
        Removes all previous (old) channels from room and user groups.
        """
        try:
            # Create copy to iterate through
            u = self.channel_layer._get_group_channel_name(self.user_group_name)
            user_group = self.channel_layer.groups[u].copy()
        except KeyError:
            user_group = {}
        # Remove old channel (if same user or multiple tabs)
        for channel in user_group:
            if channel != self.channel_name:
                # Send message to old channel to show alert
                # Actually this makes no sense to me.
                # If you remove one of these messages no event will be sent
                # if there is more than 1 user connected to ws.
                # And this will send only 1 message to old connection and remove it.
                await self.channel_layer.group_send(self.user_group_name, {
                    'type': 'send_message',
                    'message': consts.USER_ALREADY_IN_ROOM,
                    'event': consts.ALREADY_CONNECTED_EVENT,
                })
                await self.channel_layer.group_send(self.user_group_name, {
                    'type': 'send_message',
                    'message': consts.USER_ALREADY_IN_ROOM,
                    'event': consts.ALREADY_CONNECTED_EVENT,
                })
                # Leave groups
                for group_name in [self.room_group_name, self.user_group_name]:
                    await self.channel_layer.group_discard(group_name, channel)

    async def disconnect(self, close_code):
        u = self.channel_layer._get_group_channel_name(self.room_group_name)
        if self.channel_name in self.channel_layer.groups[u]:
            # Removing listener
            if self.user.is_authenticated:
                await Room.remove_listener(self.room_id, self.user)
            # Send disconnect message to other listeners
            listeners_data = await Room.get_listeners_info(self.room_id)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': f"{self.user} {consts.USER_DISCONNECTED}",
                'event': consts.DISCONNECT_EVENT,
                'listeners': listeners_data,
            })
            # Leave groups
            for group_name in [self.room_group_name, self.user_group_name]:
                await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Receive messages from WebSocket and sets appropriate event.
        """
        response = json.loads(text_data)
        event = response.get("event", None)
        message = response.get("message", None)
        if event == consts.CONNECT_EVENT:
            listeners_data = await Room.get_listeners_info(self.room_id)
            playlist_tracks = await Playlist.get_playlist_tracks(self.playlist)
            data = {
                'type': 'send_message',
                'message': message,
                'event': consts.CONNECT_EVENT,
                'user': self.user.username,
                'listeners': listeners_data,
                'playlist': playlist_tracks,
            }
            await self.channel_layer.group_send(self.room_group_name, data)

            # Here we need to send event from another user to new one
            another_user = None
            if len(listeners_data['users']) > 1:
                for listener in listeners_data['users']:
                    if listener['username'] != self.user.username:
                        another_user = listener['username']
                        break
            if another_user is not None:
                track_sender_data = {
                    'type': 'send_message',
                    'event': consts.SEND_TRACK_TO_NEW_USER,
                    'receiver': self.user.username,
                    'message': "Need to set current track.",
                }
                await self.channel_layer.group_send(
                    f"{consts.USER_GROUP_PREFIX}_{another_user}",
                    track_sender_data
                )
        elif event == consts.ADD_TRACK_EVENT:
            url = response.get("url", None)
            title = response.get("name", None)
            # Get new track and updated tracks list
            new_track, _ = await database_sync_to_async(
                Soundtrack.objects.get_or_create
            )(url=url, name=title)
            # Create new PlaylistTrack
            playlist_track, created = await database_sync_to_async(
                PlaylistTrack.objects.get_or_create
            )(track=new_track, playlist=self.playlist)
            #await Playlist.add_track(new_track, self.playlist)

            # Update last_visited
            await database_sync_to_async(self.playlist.room.save)()

            playlist_tracks = await Playlist.get_playlist_tracks(self.playlist)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'event': consts.ADD_TRACK_EVENT,
                'message': f"New track added by {self.user.username}.",
                'playlist': playlist_tracks,
                'created': created,
            })
        elif event == consts.ADD_TRACK_ERROR_EVENT:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': message,
                'event': consts.ADD_TRACK_ERROR_EVENT,
            })
        elif event == consts.CHANGE_TRACK_EVENT:
            # Get new track data and send to clients
            track_data = response.get("track", None)
            playlist_tracks = await Playlist.get_playlist_tracks(self.playlist)

            # Update last_visited
            await database_sync_to_async(self.playlist.room.save)()

            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'event': consts.CHANGE_TRACK_EVENT,
                'message': f"Track changed by {self.user.username}.",
                'playlist': playlist_tracks,
                'track': track_data,
            })
        elif event == consts.NEW_USER_JOINED_EVENT:
            new_user = response.get("user", None)
            track_data = response.get("track", None)
            loop = response.get("loop", None)
            playlist_tracks = await Playlist.get_playlist_tracks(self.playlist)
            await self.channel_layer.group_send(f"{consts.USER_GROUP_PREFIX}_{new_user}", {
                'type': 'send_message',
                'message': f"Set current track data. {self.user.username}",
                'track': track_data,
                'loop': loop,
                'playlist': playlist_tracks,
                'event': consts.SET_CURRENT_TRACK_EVENT,
            })
        elif event == consts.CHANGE_TIME_EVENT:

            # Update last_visited
            await database_sync_to_async(self.playlist.room.save)()

            time = response.get("time", None)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': f"Set current track data.",
                'time': time,
                'event': event,
            })
        elif event == consts.DELETE_TRACK_EVENT:

            # Update last_visited
            await database_sync_to_async(self.playlist.room.save)()

            track_data = response.get("track", None)
            chosen_track_url = response.get("chosenTrackUrl", None)
            soundtrack = await database_sync_to_async(
                Soundtrack.objects.get
            )(url=track_data["url"], name=track_data["name"])
            playlist_track = await database_sync_to_async(
                PlaylistTrack.objects.get
            )(track=soundtrack, playlist=self.playlist)
            await database_sync_to_async(playlist_track.delete)()
            #await Playlist.remove_track(self.playlist, soundtrack)
            # Get updated playlist
            playlist_tracks = await Playlist.get_playlist_tracks(self.playlist)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'event': consts.DELETE_TRACK_EVENT,
                'message': f"Track removed by {self.user.username}.",
                'playlist': playlist_tracks,
                'chosenTrackUrl': chosen_track_url,
                'deletedTrackInfo': track_data,
            })
        elif event == consts.TRACK_ENDED_EVENT:
            # Get current playlist and current track
            playlist_tracks = await Playlist.get_playlist_tracks(self.playlist)
            current_track_data = response.get("track", None)
            # We need reverse playlist (on client side it is reversed)
            rev_tracks = playlist_tracks.copy()
            rev_tracks.reverse()
            # Find next track from playlist
            next_track_index = rev_tracks.index(current_track_data) + 1
            next_track = rev_tracks[0]
            if next_track_index < len(rev_tracks):
                next_track = rev_tracks[next_track_index]
            # Send change track event with next track
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'event': consts.CHANGE_TRACK_EVENT,
                'message': 'New current track set.',
                'playlist': playlist_tracks,
                'track': {'url': next_track['url']},
            })
        else:
            # Send message to room group
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': message,
                'event': event,
            })

    async def send_message(self, res):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "payload": res,
        }))
