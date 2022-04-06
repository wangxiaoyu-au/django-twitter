from django.contrib.auth.models import User
from accounts.api.serializers import UserSerializerForFriendship
from friendships.models import Friendship
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from friendships.services import FriendshipService


class FollowingUserIdSetMixin:

    @property
    def following_user_id_set(self: serializers.ModelSerializer):
        if self.context['request'].user.is_anonymous:
            return {}
        if hasattr(self, '_cached_following_user_id_set'):
            return self._cached_following_user_id_set
        user_id_set = FriendshipService.get_following_user_id_set(
            self.context['request'].user.id,
        )
        setattr(self, '_cached_following_user_id_set', user_id_set)
        return user_id_set


class FollowerSerializer(serializers.ModelSerializer, FollowingUserIdSetMixin):
    # To get this account's all followers, it belongs to following friendship,
    # other users are 'following' me
    user = UserSerializerForFriendship(source='following_user')
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        return obj.following_user_id in self.following_user_id_set


class FollowingSerializer(serializers.ModelSerializer, FollowingUserIdSetMixin):
    # To get all user to which this account is following, it belongs to followed friendship,
    # other users are 'followed' by me
    user = UserSerializerForFriendship(source='followed_user')
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    def get_has_followed(self, obj):
        return obj.followed_user_id in self.following_user_id_set


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

