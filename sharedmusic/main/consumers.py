import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from main import consts
from main.services import MusicRoomConsumerService
from django.core.serializers.json import DjangoJSONEncoder
from sharedmusic.settings.settings import CHANNEL_LAYERS
# from asgiref.sync import sync_to_async


class MusicRoomConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.service = MusicRoomConsumerService(self.scope, self.channel_layer, self.channel_name)

        # If user is banned or room is full then close connection immediately
        is_banned = await self.service._is_user_banned()
        is_room_full = await self.service._is_room_full()
        if is_banned or is_room_full:
            return

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

        # Check permission before handling event
        allowed = await self.service._check_permission(event)
        if not allowed:
            await self.service.handle_not_allowed()
            return

        # Event handlers
        if event == consts.CONNECT_EVENT:
            await self.service.handle_connect(response)
        elif event == consts.ADD_TRACK_EVENT:
            await self.service.handle_add_track(response)
        elif event == consts.CHANGE_TRACK_EVENT:
            await self.service.handle_change_track(response)
        elif event == consts.SEND_TRACK_TO_NEW_USER_EVENT:
            await self.service.handle_send_track_to_new_user(response)
        elif event == consts.CHANGE_TIME_EVENT:
            await self.service.handle_change_time(response)
        elif event == consts.DELETE_TRACK_EVENT:
            await self.service.handle_delete_track(response)
        elif event == consts.TRACK_ENDED_EVENT:
            await self.service.handle_set_next_track(response)
        elif event == consts.CHANGE_HOST_EVENT:
            await self.service.handle_change_host(response)
        elif event == consts.CHANGE_PERMISSIONS_EVENT:
            await self.service.handle_change_permissions(response)
        elif event == consts.SEND_CHAT_MESSAGE_EVENT:
            is_muted = await self.service._is_user_muted()
            if not is_muted:
                await self.service.handle_chat_message(response)
            else:
                await self.service.handle_listener_muted()
        elif event == consts.MUTE_LISTENER_EVENT:
            await self.service.handle_mute(response)
        elif event == consts.UNMUTE_LISTENER_EVENT:
            await self.service.handle_unmute(response)
        elif event == consts.BAN_USER_EVENT:
            await self.service.handle_ban(response, self.close)
        elif event == consts.UNBAN_USER_EVENT:
            await self.service.handle_unban(response)
        else:
            await self.service.handle_default(response)

    async def send_message(self, res):
        # Send message to WebSocket
        # If django json encoder will be used with redis pubsub channel layer it may cause error
        # autobahn.exception.Disconnected: Attempt to send on a closed protocol
        # Actually nothing bad happens, but I add chack to suppress this exception (in most cases).
        # 1 case of error is when user opens 2 tabs and 1 gets disconnected
        if CHANNEL_LAYERS["default"]["BACKEND"] == 'channels.layers.InMemoryChannelLayer':
            await self.send(text_data=json.dumps({"payload": res}, default=DjangoJSONEncoder().default))
        else:
            await self.send(text_data=json.dumps({"payload": res}))
