from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url

from .consumers import ContainerConsumer
from .consumers import StationConsumer
from .consumers import ConnectionConsumer


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(
            [
                url("ws/genius/[^/]+/[^/]+$", ConnectionConsumer),
                url("ws/genius/[^/]+$", ContainerConsumer),
                url("ws/genius$", StationConsumer),
            ]
        )
    ),

})