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
    def get_followers(cls, user):
        # incorrect implementation 1:
        # end up with N + 1 Queries:
        # filter() is one Query, and then the for loop operation produced N-time Queries
        # friendships = Friendship.objects.filter(followed_user=user)
        # return [friendship.following_user for friendship in friendships]

        # incorrect implementation 2:
        # this way would introduce JOIN operation (select_related) in mysql,
        # friendship table and user table would JOIN together on argument following_user,
        # which would highly possibly retard the whole process.
        # friendships = Friendship.objects.filter(
        #     followed_user=user
        # ).select_related('following_user')
        # return [friendship.following_user for friendship in friendships]

        # correct implementation 1:
        # filter user_id instead of user, then using IN Query
        # friendships = Friendship.objects.filter(followed_user=user)
        # follower_ids = [friendship.following_user_id for friendship in friendships]
        # followers = User.objects.filter(id__in=follower_ids)

        # correct implementation 2:
        # using prefetch_related()
        # is equivalent to correct implementation 1
        friendships = Friendship.objects.filter(
            followed_user=user
        ).prefetch_related('following_user')
        return [friendship.following_user for friendship in friendships]

    @classmethod
    def get_follower_ids(cls, followed_user_id):
        friendships = Friendship.objects.filter(followed_user_id=followed_user_id)
        return [friendship.following_user_id for friendship in friendships]

    @classmethod
    def get_following_user_id_set(cls, following_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=following_user_id)
        user_id_set = cache.get(key)
        if user_id_set is not None:
            return user_id_set

        friendships = Friendship.objects.filter(following_user_id=following_user_id)
        user_id_set = set([
            fs.followed_user_id for fs in friendships
        ])
        cache.set(key, user_id_set)
        return user_id_set

    # To alleviate data inconsistency, deleting the old data instead of updating
    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        cache.delete(key)

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














