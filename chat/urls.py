from django.urls import path
from .views import ConversationListCreateView, QAPairListCreateView

urlpatterns = [
    path('', ConversationListCreateView.as_view(), name='conversations'),
    path('<int:conversation_id>/qapairs/', QAPairListCreateView.as_view(), name='conversation-qapairs'),
]
