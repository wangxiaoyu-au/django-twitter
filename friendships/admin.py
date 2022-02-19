from django.contrib import admin
from friendships.models import Friendship


# Register your models here.
@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('id', 'following_user', 'followed_user', 'created_at')
    date_hierarchy = 'created_at'
