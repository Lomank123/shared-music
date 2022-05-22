from main.repositories import RoomRepository, PlaylistRepository, SoundtrackRepository, \
    PlaylistTrackRepository, CustomUserRepository
from main import consts
from main.decorators import update_room_expiration_time


class MusicRoomConsumerService():

    __slots__ = (
        'scope',
        'channel_layer',
        'channel_name',
        'user',
        'room_id',
        'room_group_name',
        'user_group_name',
    )

    def __init__(self, scope, channel_layer, channel_name):
        self.channel_layer = channel_layer
        self.channel_name = channel_name
        self.scope = scope
        self.user = self.scope.get('user')
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'{consts.ROOM_GROUP_PREFIX}_{self.room_id}'
        # User group must contain only one user
        self.user_group_name = f'{consts.USER_GROUP_PREFIX}_{self.user.username}'

    def _build_context_data(self, event, message="Message", extra_data={}):
        """
        Builds dict context data.
        """
        context_data = {
            "type": "send_message",
            "event": event,
            "message": message,
        }
        context_data.update(extra_data)
        return context_data

    async def _check_permission(self, event):
        room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        if event in room.permissions.keys():
            if int(room.permissions[event]) > consts.ROOM_ALLOW_ANY:
                return self.user.id == room.host_id
        return True

    async def connect_user(self):
        if self.user.is_authenticated:
            # Remove all previous connections of the same user if they exist
            await self._remove_old_connections()
            # Join groups
            for group_name in [self.room_group_name, self.user_group_name]:
                await self.channel_layer.group_add(group_name, self.channel_name)
            # Add new listener
            await RoomRepository.add_listener(self.room_id, self.user)

    async def disconnect_user(self):
        u = self.channel_layer._get_group_channel_name(self.room_group_name)
        if self.channel_name in self.channel_layer.groups[u]:
            # Removing listener
            await RoomRepository.remove_listener(self.room_id, self.user)
            # Send disconnect message to other listeners
            listeners_data = await RoomRepository.get_listeners_info(self.room_id)
            message = f"{self.user} {consts.USER_DISCONNECTED}"
            data = self._build_context_data(consts.DISCONNECT_EVENT, message, {"listeners": listeners_data})
            await self.channel_layer.group_send(self.room_group_name, data)
            # Leave groups
            for group_name in [self.room_group_name, self.user_group_name]:
                await self.channel_layer.group_discard(group_name, self.channel_name)

    async def _remove_old_connections(self):
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
                data = self._build_context_data(consts.ALREADY_CONNECTED_EVENT, consts.USER_ALREADY_IN_ROOM)
                # Actually this makes no sense to me.
                # If you remove one of these messages no event will be sent
                # if there is more than 1 user connected to ws.
                # And this will send only 1 message to old connection and remove it.
                await self.channel_layer.group_send(self.user_group_name, data)
                await self.channel_layer.group_send(self.user_group_name, data)
                # Leave groups
                for group_name in [self.room_group_name, self.user_group_name]:
                    await self.channel_layer.group_discard(group_name, channel)

    async def handle_connect(self, response):
        """
        Handles connect event. Sends track to new listener and related message to all other users.
        """
        message = response.get("message", None)
        listeners_data = await RoomRepository.get_listeners_info(self.room_id)
        room_playlist = await RoomRepository.get_room_playlist(self.room_id)
        playlist_tracks = await PlaylistRepository.get_playlist_tracks(room_playlist)
        room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        data = self._build_context_data(consts.CONNECT_EVENT, message, {
            "user": self.user.username,
            "listeners": listeners_data,
            "playlist": playlist_tracks,
            "permissions": room.permissions,
        })
        await self.channel_layer.group_send(self.room_group_name, data)
        # Here we need to send event from another user to new one
        await self._get_track_from_listeners(listeners_data)

    async def _get_track_from_listeners(self, listeners):
        another_user = None
        if len(listeners['users']) > 1:
            for listener in listeners['users']:
                if listener['username'] != self.user.username:
                    another_user = listener['username']
                    break
        if another_user is not None:
            track_sender_data = self._build_context_data(
                consts.GET_TRACK_FROM_LISTENERS_EVENT,
                consts.GET_TRACK_FROM_LISTENERS,
                {"receiver": self.user.username, }
            )
            await self.channel_layer.group_send(
                f"{consts.USER_GROUP_PREFIX}_{another_user}",
                track_sender_data
            )

    @update_room_expiration_time
    async def handle_change_track(self, response):
        # Get new track data and send to clients
        track_data = response.get("track", None)
        room_playlist = await RoomRepository.get_room_playlist(self.room_id)
        playlist_tracks = await PlaylistRepository.get_playlist_tracks(room_playlist)
        message = f"Track changed by {self.user.username}."
        data = self._build_context_data(consts.CHANGE_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "track": track_data,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    @update_room_expiration_time
    async def handle_add_track(self, response):
        url = response.get("url", None)
        name = response.get("name", None)
        new_track, _ = await SoundtrackRepository.get_or_create(url, name)
        # We need to know whether new PlaylistTrack instance has been created
        room_playlist = await RoomRepository.get_room_playlist(self.room_id)
        _, created = await PlaylistTrackRepository.get_or_create(new_track, room_playlist)
        # Send message
        playlist_tracks = await PlaylistRepository.get_playlist_tracks(room_playlist)
        message = f"New track added by {self.user.username}."
        data = self._build_context_data(consts.ADD_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "created": created,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    @update_room_expiration_time
    async def handle_delete_track(self, response):
        room_playlist = await RoomRepository.get_room_playlist(self.room_id)
        track_data = response.get("track", None)
        chosen_track_url = response.get("chosenTrackUrl", None)
        # Delete playlist track
        soundtrack = await SoundtrackRepository.get_by_url_and_name(track_data["url"], track_data["name"])
        playlist_track = await PlaylistTrackRepository.get_by_track_and_playlist(soundtrack, room_playlist)
        await PlaylistTrackRepository.delete(playlist_track)
        # Get updated playlist
        playlist_tracks = await PlaylistRepository.get_playlist_tracks(room_playlist)
        message = f"Track removed by {self.user.username}."
        data = self._build_context_data(consts.DELETE_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "chosenTrackUrl": chosen_track_url,
            "deletedTrackInfo": track_data,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_send_track_to_new_user(self, response):
        new_user = response.get("user", None)
        track_data = response.get("track", None)
        loop = response.get("loop", None)
        room_playlist = await RoomRepository.get_room_playlist(self.room_id)
        playlist_tracks = await PlaylistRepository.get_playlist_tracks(room_playlist)
        message = f"Set current track data. {self.user.username}"
        data = self._build_context_data(consts.SET_CURRENT_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "track": track_data,
            "loop": loop,
        })
        await self.channel_layer.group_send(f"{consts.USER_GROUP_PREFIX}_{new_user}", data)

    @update_room_expiration_time
    async def handle_change_time(self, response):
        time = response.get("time", None)
        message = "Set current time."
        data = self._build_context_data(consts.CHANGE_TIME_EVENT, message, {"time": time})
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_track_ended(self, response):
        room_playlist = await RoomRepository.get_room_playlist(self.room_id)
        # Get current playlist and current track
        playlist_tracks = await PlaylistRepository.get_playlist_tracks(room_playlist)
        current_track_data = response.get("track", None)
        # We need reverse playlist
        rev_tracks = playlist_tracks.copy()
        rev_tracks.reverse()
        # Find next track from playlist
        next_track_index = 1
        for index in range(len(rev_tracks)):
            if rev_tracks[index]['url'] == current_track_data['url']:
                next_track_index = index + 1
                break
        next_track = rev_tracks[0]
        if next_track_index < len(rev_tracks):
            next_track = rev_tracks[next_track_index]
        # Send change track event with next track
        message = "New current track set."
        data = self._build_context_data(consts.CHANGE_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "track": {'url': next_track['url']},
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_change_host(self, response):
        """
        Changes host to new one by it's username.
        """
        new_host_username = response.get("new_host", None)
        new_host = await CustomUserRepository.get_by_username_or_none(new_host_username)
        await RoomRepository.change_host(self.room_id, new_host)
        data = self._build_context_data(consts.HOST_CHANGED_EVENT, consts.HOST_CHANGED, {
            "new_host": new_host_username,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_change_permissions(self, response):
        room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        new_permissions = response.get("permissions", None)
        room.permissions = new_permissions
        await RoomRepository.save_room(room)
        data = self._build_context_data(consts.CHANGE_PERMISSIONS_EVENT, consts.PERMISSIONS_CHANGED_MSG, {
            "permissions": room.permissions,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_default(self, response):
        event = response.get("event", None)
        message = response.get("message", None)
        data = self._build_context_data(event, message)
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_not_allowed(self, response):
        data = self._build_context_data(consts.ROOM_NOT_ALLOWED_EVENT, consts.ROOM_NOT_ALLOWED_MSG)
        await self.channel_layer.group_send(self.user_group_name, data)
