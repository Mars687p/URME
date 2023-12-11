from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/shipments/(?<id>\w+$", consumers.ListenConsumer.as_asgi()),
]