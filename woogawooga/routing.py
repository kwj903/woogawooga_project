from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/analysis/(?P<task_id>\w+)/$', consumers.AnalysisProgressConsumer.as_asgi()),
]