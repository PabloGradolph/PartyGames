from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/partida/(?P<codigo>\w+)/$', consumers.PartidaConsumer.as_asgi()),
] 