from django.urls import re_path
from main.consumers import MusicRoomConsumer


websocket_urlpatterns = [
    re_path(r'^ws/room/(?P<id>[A-Za-z0-9_-]+)/', MusicRoomConsumer.as_asgi()),
]
