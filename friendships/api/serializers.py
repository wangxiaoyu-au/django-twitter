from django.contrib.auth.models import User
from accounts.api.serializers import UserSerializerForFriendship
from friendships.models import Friendship
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from friendships.services import FriendshipService

class FollowerSerializer(serializers.ModelSerializer):
    # To get this account's all followers, it belongs to following friendship,
    # other users 'following' me
    user = UserSerializerForFriendship(source='following_user')
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return FriendshipService.has_followed(self.context['request'].user, obj.following_user)


class FollowingSerializer(serializers.ModelSerializer):
    # To get all user by which this account followed, it belongs to followed friendship,
    # other users are 'followed' by me
    user = UserSerializerForFriendship(source='followed_user')
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return FriendshipService.has_followed(self.context['request'].user, obj.followed_user)


class FriendshipSerializerForCreate(serializers.ModelSerializer):
    following_user_id = serializers.IntegerField()
    followed_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ('following_user_id', 'followed_user_id')

    def validate(self, attrs):
        if not User.objects.filter(id=attrs['followed_user_id']).exists():
            raise ValidationError({
                'message': 'You cannot follow a non-existent user.',
            })
        if attrs['following_user_id'] == attrs['followed_user_id']:
            raise ValidationError({
                'message': 'You cannot follow yourself.',
            })
        if Friendship.objects.filter(
            following_user_id=attrs['following_user_id'],
            followed_user_id=attrs['followed_user_id'],
        ).exists():
            raise ValidationError({
                'message': 'You have already followed this user.',
            })
        return attrs

    def create(self, validated_data):
        return Friendship.objects.create(
            following_user_id=validated_data['following_user_id'],
            followed_user_id=validated_data['followed_user_id'],
        )

