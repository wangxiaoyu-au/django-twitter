from django.contrib.auth.models import User
from accounts.api.serializers import UserSerializerForFriendship
from friendships.models import Friendship
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from friendships.services import FriendshipService
from accounts.services import UserService


class BaseFriendshipSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    has_followed = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def get_user_id(self, obj):
        raise NotImplementedError

    def _get_following_user_id_set(self):
        if self.context['request'].user.is_anonymous:
            return {}
        if hasattr(self, '_cached_following_user_id_set'):
            return self._cached_following_user_id_set
        user_id_set = FriendshipService.get_following_user_id_set(
            self.context['request'].user.id,
        )
        setattr(self, '_cached_following_user_id_set', user_id_set)
        return user_id_set

    def get_user_id(self, obj):
        raise NotImplementedError

    def get_has_followed(self, obj):
        return self.get_user_id(obj) in self._get_following_user_id_set()

    def get_user(self, obj):
        user = UserService.get_user_by_id(self.get_user_id(obj))
        return UserSerializerForFriendship(user).data

    def get_created_at(self, obj):
        return obj.created_at


class FollowerSerializer(BaseFriendshipSerializer):
    def get_user_id(self, obj):
        return obj.following_user_id


class FollowingSerializer(BaseFriendshipSerializer):
    def get_user_id(self, obj):
        return obj.followed_user_id


class FriendshipSerializerForCreate(serializers.Serializer):
    following_user_id = serializers.IntegerField()
    followed_user_id = serializers.IntegerField()

    def validate(self, attrs):
        # if not User.objects.filter(id=attrs['followed_user_id']).exists():
        #     raise ValidationError({
        #         'message': 'You cannot follow a non-existent user.',
        #     })
        if attrs['following_user_id'] == attrs['followed_user_id']:
            raise ValidationError({
                'message': 'You cannot follow yourself.',
            })
        # if Friendship.objects.filter(
        #     following_user_id=attrs['following_user_id'],
        #     followed_user_id=attrs['followed_user_id'],
        # ).exists():
        #     raise ValidationError({
        #         'message': 'You have already followed this user.',
        #     })
        return attrs

    def create(self, validated_data):
        following_user_id = validated_data['following_user_id']
        followed_user_id = validated_data['followed_user_id']
        return FriendshipService.follow(
            following_user_id=following_user_id,
            followed_user_id=followed_user_id,
        )