from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, WatchingStatus

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'nickname', 'email', 'is_staff')
    search_fields = ('username', 'nickname', 'email')

    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('nickname', 'profile_image')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('nickname',)}),
    )

@admin.register(WatchingStatus)
class WatchingStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'series', 'status', 'current_episode', 'last_watched', 'rating')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__nickname', 'series__title')
    raw_id_fields = ('user', 'series')
