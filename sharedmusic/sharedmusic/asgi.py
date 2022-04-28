import os
import django
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

django.setup()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sharedmusic.settings.settings')
django_asgi_application = get_asgi_application()

import main.routing

# application = get_asgi_application()
application = ProtocolTypeRouter({
    "http": django_asgi_application,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            main.routing.websocket_urlpatterns
        )
    ),
})
