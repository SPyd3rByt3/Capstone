"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

"""
ASGI config for capstone project.

It exposes the ASGI callable as a module-level variable named `application`.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import collab.routing  # You'll create this file later

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')  # Adjust to your project name

                                                # 'config.settings'
                                                
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,
    
    # WebSocket handler
    "websocket": AuthMiddlewareStack(
        URLRouter(
            collab.routing.websocket_urlpatterns + AIcontent.routing.websocket_urlpatterns
        )
    ),
})
