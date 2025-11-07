from django.contrib import admin
from .models import Conversation, QAPair


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'summary', 'user', 'series', 'created_at')
    search_fields = ('summary',)


@admin.register(QAPair)
class QAPairAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'question_text', 'created_at')
    search_fields = ('question_text', 'answer_text')
