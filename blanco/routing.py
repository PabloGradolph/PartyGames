from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/partida/(?P<codigo>[A-Z0-9\-]+)/$', consumers.PartidaConsumer.as_asgi()),
]