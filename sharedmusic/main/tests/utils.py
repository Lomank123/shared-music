from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import Client
from sharedmusic.asgi import application


async def build_communicator(user, room_id) -> WebsocketCommunicator:
    """
    Constructs WebsocketCommunicator with authenticated user.
    """
    client = Client()
    # Authentication
    # force_login authenticates user (use exactly force_login(), login() method won't help)
    await sync_to_async(client.force_login)(user)
    # Then we need to set headers to communicator
    # With this our user will be logged in inside consumer
    # Thus we can receive events (e.g. connect event)
    # output() returns string representation of cookies
    # encode() encodes using UTF-8 by default
    client_cookies = client.cookies.output(header='', sep='; ').encode()
    headers = [
        (b'origin', b'...'),
        (b'cookie', client_cookies)
    ]
    # Communicator instance represent 1 connected user
    # If you want more than 1 user then create multiple communicators
    communicator = WebsocketCommunicator(application, f"/ws/room/{room_id}/", headers)
    communicator.scope["url_route"] = {"kwargs": {"room_id": room_id}}
    communicator.scope["user"] = user
    # Return communicator with authenticated user
    return communicator
