from django.urls import re_path
from main.consumers import MusicRoomConsumer


websocket_urlpatterns = [
    re_path(r'^ws/room/(?P<code>\w+)/$', MusicRoomConsumer.as_asgi()),
]