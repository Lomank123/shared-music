from main.repositories import RoomRepository, RoomPlaylistRepository, SoundtrackRepository, \
    RoomPlaylistTrackRepository, CustomUserRepository, ChatMessageRepository
from main import consts
from main.decorators import update_room_expiration_time
from django.forms.models import model_to_dict
from sharedmusic.settings.settings import CHANNEL_LAYERS


class MusicRoomConsumerService:

    """
    Consumer service which provides event handlers for music rooms.
    """

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
        self.user_group_name = self._get_user_group(self.user.username)

    @staticmethod
    def _get_user_group(username):
        return f'{consts.USER_GROUP_PREFIX}_{username}'

    def _build_context_data(self, event, message="Message", extra_data={}):
        """
        Builds dict context data with given event, message and extras.
        """
        context_data = {
            "type": "send_message",
            "event": event,
            "message": message,
        }
        context_data.update(extra_data)
        return context_data

    async def _check_permission(self, event):
        """
        Returns True if event is not in permissions list or if permission is lower or equal to allow any.
        Otherwise returns whether user is host.
        """
        room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        if event in room.permissions.keys():
            if int(room.permissions[event]) > consts.ROOM_ALLOW_ANY:
                return self.user.id == room.host_id
        return True

    async def _is_user_muted(self):
        """
        Returns True if user is muted, otherwise False.
        """
        return await RoomRepository.is_user_muted(self.room_id, self.user.id)

    async def _is_user_banned(self):
        """
        Returns True if user is banned, otherwise False.
        """
        return await RoomRepository.is_user_banned(self.room_id, self.user.id)

    async def _is_room_full(self):
        """
        Return True if the number or online listeners >= room's max_connections number.
        Otherwise return False.
        """
        room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        listeners_info = await RoomRepository.get_listeners_info(self.room_id)
        return listeners_info["count"] >= room.max_connections

    async def _remove_old_connections(self):
        """
        Removes all previous (old) connections from room and user groups.
        """
        try:
            group_channel_name = self.user_group_name
            if CHANNEL_LAYERS["default"]["BACKEND"] == 'main.channel_layers.CustomChannelLayer':
                group_channel_name = self.channel_layer._get_group_channel_name(self.user_group_name)
        except AttributeError:
            pass

        user_group = {}
        try:
            # Create copy to iterate through
            user_group = self.channel_layer.groups[group_channel_name].copy()
        except KeyError:
            pass
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

    async def _get_recent_chat_messages(self):
        """
        Returns recent chat messages.
        """
        recent_messages = await ChatMessageRepository.get_recent_messages(self.room_id)
        return recent_messages

    async def _send_track_from_listeners(self, listeners):
        """
        Finds first online listener in the room and sends them event
        to get track data for new one. If no listeners found nothing happens.
        """
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
                self._get_user_group(another_user),
                track_sender_data
            )

    async def _send_extra_info(self, username, extra_data):
        """
        Sends additional info (ban list, mute list).
        """
        message = "Send additional info to user."
        data = self._build_context_data(consts.SEND_EXTRA_INFO_EVENT, message, extra_data)
        group_name = self._get_user_group(username)
        await self.channel_layer.group_send(group_name, data)

    async def _find_next_track(self, playlist_tracks, current_track, previous=False):
        """
        Finds next track in the playlist (after current_track) and returns it.
        If it is the last track then it falls back to the first.

        if previous is set to True, then previous track will be returned.
        """
        # We need reverse playlist
        rev_tracks = playlist_tracks.copy()
        if not previous:
            rev_tracks.reverse()
        # Find next track from playlist
        next_track_index = 1
        for index in range(len(rev_tracks)):
            if rev_tracks[index]['url'] == current_track['url']:
                next_track_index = index + 1
                break
        next_track = rev_tracks[0]
        if next_track_index < len(rev_tracks):
            next_track = rev_tracks[next_track_index]
        return next_track

    async def connect_user(self):
        """
        Removes old connections of the same user and adds them as listener.
        """
        if self.user.is_authenticated:
            # Remove all previous connections of the same user if they exist
            await self._remove_old_connections()
            # Join groups
            for group_name in [self.room_group_name, self.user_group_name]:
                await self.channel_layer.group_add(group_name, self.channel_name)
            # Add new listener
            await RoomRepository.add_listener(self.room_id, self.user.id)

    async def disconnect_user(self):
        """
        Handles disconnect event. Removes user from listeners list and sends related message
        with updated list to others.
        """
        try:
            group_channel_name = self.room_group_name
            if CHANNEL_LAYERS["default"]["BACKEND"] == 'main.channel_layers.CustomChannelLayer':
                group_channel_name = self.channel_layer._get_group_channel_name(self.room_group_name)
        except AttributeError:
            # In case of different channel layer
            group_channel_name = self.room_group_name
        try:
            groups = self.channel_layer.groups[group_channel_name]
        except KeyError:
            return
        if self.channel_name in groups:
            # Removing listener
            await RoomRepository.remove_listener(self.room_id, self.user.id)
            # Send disconnect message to other listeners
            listeners_data = await RoomRepository.get_listeners_info(self.room_id)
            message = f"{self.user} {consts.USER_DISCONNECTED}"
            data = self._build_context_data(consts.DISCONNECT_EVENT, message, {"listeners": listeners_data})
            await self.channel_layer.group_send(self.room_group_name, data)
            # Leave groups
            for group_name in [self.room_group_name, self.user_group_name]:
                await self.channel_layer.group_discard(group_name, self.channel_name)

    async def handle_connect(self, response):
        """
        Handles connect event. Sends track to new listener and related message to all other listeners.
        """
        message = response.get("message", None)
        listeners_data = await RoomRepository.get_listeners_info(self.room_id)
        playlist_tracks = await RoomPlaylistRepository.get_playlist_tracks(self.room_id)
        room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        recent_messages = await self._get_recent_chat_messages()
        data = self._build_context_data(consts.CONNECT_EVENT, message, {
            "user": self.user.username,
            "listeners": listeners_data,
            "playlist": playlist_tracks,
            "permissions": room.permissions,
            "recent_messages": recent_messages,
            "max_connections": room.max_connections,
        })
        await self.channel_layer.group_send(self.room_group_name, data)
        # Here we need to send event from another user to new one
        await self._send_track_from_listeners(listeners_data)
        # Send extra info if user is host
        if self.user.id == room.host_id:
            ban_list = await RoomRepository.get_room_ban_list(self.room_id)
            mute_list = await RoomRepository.get_room_mute_list(self.room_id)
            extra_data = {
                "ban_list": ban_list,
                "mute_list": mute_list,
            }
            await self._send_extra_info(self.user.username, extra_data)

    @update_room_expiration_time
    async def handle_change_track(self, response):
        """
        Handles change track event. Sends chosen track data and playlist to other listeners.
        """
        # Get new track data and send to clients
        track_data = response.get("track", None)
        playlist_tracks = await RoomPlaylistRepository.get_playlist_tracks(self.room_id)
        message = f"Track changed by {self.user.username}."
        data = self._build_context_data(consts.CHANGE_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "track": track_data,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    @update_room_expiration_time
    async def handle_add_track(self, response):
        """
        Handles add track event. Sends updated playlist and flag whether new Soundtrack instance
        has been created.
        """
        url = response.get("url", None)
        name = response.get("name", None)
        new_track, _ = await SoundtrackRepository.get_or_create(url, name)
        # We need to know whether new RoomPlaylistTrack instance has been created
        _, created = await RoomPlaylistTrackRepository.get_or_create(new_track.id, self.room_id)
        # Send message
        playlist_tracks = await RoomPlaylistRepository.get_playlist_tracks(self.room_id)
        message = f"New track added by {self.user.username}."
        data = self._build_context_data(consts.ADD_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "created": created,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    @update_room_expiration_time
    async def handle_delete_track(self, response):
        """
        Handles delete track event. Sends deleted track info along with updated playlist.
        """
        track_data = response.get("track", None)
        chosen_track_url = response.get("chosenTrackUrl", None)
        # Delete playlist track
        soundtrack = await SoundtrackRepository.get_by_url_and_name(track_data["url"], track_data["name"])
        playlist_track = await RoomPlaylistTrackRepository.get_by_track_and_playlist(soundtrack.id, self.room_id)
        await RoomPlaylistTrackRepository.delete(playlist_track)
        # Get updated playlist
        playlist_tracks = await RoomPlaylistRepository.get_playlist_tracks(self.room_id)
        message = f"Track removed by {self.user.username}."
        data = self._build_context_data(consts.DELETE_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "chosenTrackUrl": chosen_track_url,
            "deletedTrackInfo": track_data,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_send_track_to_new_user(self, response):
        """
        Used when new listener enters the room.
        Retrieves track data from existing listener and sends it only to new one by specifying user group.
        """
        new_user_username = response.get("user", None)
        track_data = response.get("track", None)
        loop = response.get("loop", None)
        playlist_tracks = await RoomPlaylistRepository.get_playlist_tracks(self.room_id)
        message = f"Set current track data. {self.user.username}"
        data = self._build_context_data(consts.SET_CURRENT_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "track": track_data,
            "loop": loop,
        })
        new_user_group = self._get_user_group(new_user_username)
        await self.channel_layer.group_send(new_user_group, data)

    @update_room_expiration_time
    async def handle_change_time(self, response):
        """
        Handles player time change. Sends new time to all listeners.
        """
        time = response.get("time", None)
        message = "Set current time."
        data = self._build_context_data(consts.CHANGE_TIME_EVENT, message, {"time": time})
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_set_next_track(self, response):
        """
        Finds next track in the list and sends change track event.
        """
        # Get current playlist and current track
        playlist_tracks = await RoomPlaylistRepository.get_playlist_tracks(self.room_id)
        current_track_data = response.get("track", None)
        previous = response.get("previous", False)
        next_track = await self._find_next_track(playlist_tracks, current_track_data, previous=previous)
        # Send change track event with next track
        message = "New current track set."
        data = self._build_context_data(consts.CHANGE_TRACK_EVENT, message, {
            "playlist": playlist_tracks,
            "track": {
                'url': next_track['url'],
                'name': next_track['name'],
            },
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_chat_message(self, response):
        """
        Handles chat messages. Retrieves user message, creates new ChatMessage instance
        and sends it to others.
        """
        text = response.get("chat_message", None)
        new_chat_message = await ChatMessageRepository.create(self.room_id, self.user.id, text)
        # Formatting model dict
        dict_chat_msg = model_to_dict(new_chat_message)
        dict_chat_msg["username"] = self.user.username
        dict_chat_msg["timestamp"] = str(new_chat_message.timestamp)
        del dict_chat_msg["sender"]
        del dict_chat_msg["room"]

        message = "New message incoming"
        data = self._build_context_data(consts.SEND_CHAT_MESSAGE_EVENT, message, {
            "chat_message": dict_chat_msg,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_change_host(self, response):
        """
        Changes host to new one by it's username.
        """
        new_host_username = response.get("new_host", None)
        new_host = await CustomUserRepository.get_by_username_or_none(new_host_username)
        await RoomRepository.change_host(self.room_id, new_host.id)
        # Unmute new host automatically
        await RoomRepository.unmute_user(self.room_id, new_host.id)
        # Technically new host cannot be banned user
        # await RoomRepository.unban_user(self.room_id, new_host.id)
        data = self._build_context_data(consts.HOST_CHANGED_EVENT, consts.HOST_CHANGED, {
            "new_host": new_host_username,
        })
        await self.channel_layer.group_send(self.room_group_name, data)
        # Send lists to new host
        ban_list = await RoomRepository.get_room_ban_list(self.room_id)
        mute_list = await RoomRepository.get_room_mute_list(self.room_id)
        extra_data = {
            "ban_list": ban_list,
            "mute_list": mute_list,
        }
        await self._send_extra_info(new_host_username, extra_data)

    async def handle_change_permissions(self, response):
        """
        Updates permissions and sends them to all listeners.
        """
        room = await RoomRepository.get_room_by_id_or_none(self.room_id)
        new_permissions = response.get("permissions", None)
        # new_max_connections = response.get("max_connections", None)
        room.permissions = new_permissions
        # room.max_connections = new_max_connections
        await RoomRepository.save_room(room)
        data = self._build_context_data(consts.CHANGE_PERMISSIONS_EVENT, consts.PERMISSIONS_CHANGED_MSG, {
            "permissions": room.permissions,
            # "max_connections": room.max_connections,
        })
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_default(self, response):
        """
        Default handler which sends given event and message to all listeners.
        """
        event = response.get("event", None)
        message = response.get("message", None)
        data = self._build_context_data(event, message)
        await self.channel_layer.group_send(self.room_group_name, data)

    async def handle_not_allowed(self):
        """
        If user has no permissions to perform some action this handler is used.
        Sends related message.
        """
        data = self._build_context_data(consts.ROOM_NOT_ALLOWED_EVENT, consts.ROOM_NOT_ALLOWED_MSG)
        await self.channel_layer.group_send(self.user_group_name, data)

    async def handle_mute(self, response):
        """
        Mutes user by updating room's mute list.
        """
        username = response.get("username")
        chosen_user = await CustomUserRepository.get_by_username_or_none(username)
        await RoomRepository.mute_user(self.room_id, chosen_user.id)
        # Send message to affected user
        message = "You are currently muted."
        data = self._build_context_data(consts.MUTE_LISTENER_EVENT, message)
        chosen_user_group = self._get_user_group(chosen_user.username)
        # Notify muted user
        await self.channel_layer.group_send(chosen_user_group, data)
        # Send updated mute list to host
        # self.user is host because only host can send mute events
        mute_list = await RoomRepository.get_room_mute_list(self.room_id)
        extra_data = {'mute_list': mute_list}
        await self._send_extra_info(self.user.username, extra_data=extra_data)

    async def handle_unmute(self, response):
        """
        Unmutes user by updating room's mute list.
        """
        username = response.get("username")
        chosen_user = await CustomUserRepository.get_by_username_or_none(username)
        await RoomRepository.unmute_user(self.room_id, chosen_user.id)
        # Send message to affected user
        message = "You are no longer muted!"
        data = self._build_context_data(consts.UNMUTE_LISTENER_EVENT, message)
        chosen_user_group = self._get_user_group(chosen_user.username)
        await self.channel_layer.group_send(chosen_user_group, data)
        mute_list = await RoomRepository.get_room_mute_list(self.room_id)
        extra_data = {'mute_list': mute_list}
        await self._send_extra_info(self.user.username, extra_data=extra_data)

    async def handle_listener_muted(self):
        """
        Sends message to muted listener.
        """
        message = "You are currently muted."
        data = self._build_context_data(consts.LISTENER_MUTED_EVENT, message)
        await self.channel_layer.group_send(self.user_group_name, data)

    async def handle_ban(self, response, close_func):
        """
        Bans user by updating room's ban list and sending related event to close connection.
        """
        username = response.get("username")
        chosen_user = await CustomUserRepository.get_by_username_or_none(username)
        await RoomRepository.ban_user(self.room_id, chosen_user.id)
        # Send message to affected user
        message = "You have been banned."
        data = self._build_context_data(consts.BAN_USER_EVENT, message)
        chosen_user_group = self._get_user_group(chosen_user.username)
        await self.channel_layer.group_send(chosen_user_group, data)
        ban_list = await RoomRepository.get_room_ban_list(self.room_id)
        extra_data = {'ban_list': ban_list}
        await self._send_extra_info(self.user.username, extra_data=extra_data)

    async def handle_unban(self, response):
        """
        Unbans user by updating room's ban list.
        """
        username = response.get("username")
        message = f"User {username} has been unbanned."
        chosen_user = await CustomUserRepository.get_by_username_or_none(username)
        await RoomRepository.unban_user(self.room_id, chosen_user.id)
        data = self._build_context_data(consts.UNBAN_USER_EVENT, message)
        await self.channel_layer.group_send(self.room_group_name, data)
        ban_list = await RoomRepository.get_room_ban_list(self.room_id)
        extra_data = {'ban_list': ban_list}
        await self._send_extra_info(self.user.username, extra_data=extra_data)
