from friendships.models import Friendship
from django.conf import settings
from django.core.cache import caches
from twitter.cache import FOLLOWINGS_PATTERN
from friendships.hbase_models import HBaseFollower, HBaseFollowing
from gatekeeper.models import GateKeeper

import time

cache = caches['testing'] if settings.TESTING else caches['default']


class FriendshipService(object):

    @classmethod
    def get_follower_ids(cls, followed_user_id):
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            friendships = Friendship.objects.filter(followed_user_id=followed_user_id)
        else:
            friendships = HBaseFollower.filter(prefix=(followed_user_id, None))
        return [friendship.following_user_id for friendship in friendships]

    @classmethod
    def get_following_user_id_set(cls, following_user_id):
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            friendships = Friendship.objects.filter(following_user_id=following_user_id)
        else:
            friendships = HBaseFollower.filter(prefix=(following_user_id, None))
        user_id_set = set([
            fs.followed_user_id for fs in friendships
        ])
        return user_id_set

    # To alleviate data inconsistency, deleting the old data instead of updating
    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        cache.delete(key)

    @classmethod
    def get_follow_instance(cls, following_user_id, followed_user_id):
        followings = HBaseFollowing.filter(prefix=(following_user_id, None))
        for follow in followings:
            if follow.followed_user_id == followed_user_id:
                return follow
        return None

    @classmethod
    def has_followed(cls, following_user_id, followed_user_id):
        if following_user_id == followed_user_id:
            return False

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            return Friendship.objects.filter(
                following_user_id=following_user_id,
                followed_user_id=followed_user_id,
            ).exists()

        instance = cls.get_follow_instance(following_user_id, followed_user_id)
        return instance is not None

    @classmethod
    def follow(cls, following_user_id, followed_user_id):
        if following_user_id == followed_user_id:
            return None

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # create data in mysql
            return Friendship.objects.create(
                following_user_id=following_user_id,
                followed_user_id=followed_user_id,
            )

        # create data in hbase
        now = int(time.time() * 1000000)
        HBaseFollower.create(
            following_user_id=following_user_id,
            followed_user_id=followed_user_id,
            created_at=now,
        )
        return HBaseFollowing.create(
            following_user_id=following_user_id,
            followed_user_id=followed_user_id,
            created_at=now,
        )

    @classmethod
    def unfollow(cls, following_user_id, followed_user_id):
        if following_user_id == followed_user_id:
            return 0

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            deleted, _ = Friendship.objects.filter(
                following_user_id=following_user_id,
                followed_user_id=followed_user_id,
            ).delete()
            return deleted

        instance = cls.get_follow_instance(following_user_id, followed_user_id)
        if instance is None:
            return 0

        HBaseFollowing.delete(following_user_id=following_user_id, created_at=instance.create_at)
        HBaseFollower.delete(followed_user_id=followed_user_id, created_at=instance.create_at)
        return 1

    @classmethod
    def get_following_count(cls, following_user_id):
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            return Friendship.objects.filter(following_user_id=following_user_id).count()
        followings = HBaseFollowing.filter(prefix=(following_user_id, None))
        return len(followings)