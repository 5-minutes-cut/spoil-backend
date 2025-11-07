from django.urls import path
from .views import ConversationListCreateView, QAPairListCreateView, channel_bug_report

urlpatterns = [
    path('', ConversationListCreateView.as_view(), name='conversations'),
    path('<int:conversation_id>/qapairs/', QAPairListCreateView.as_view(), name='conversation-qapairs'),
    path("api/channel/bug-report/", channel_bug_report, name="channel-bug-report"),
]
