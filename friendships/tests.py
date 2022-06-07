from friendships.models import Friendship
from friendships.services import FriendshipService
from testing.testcases import TestCase
from django_hbase.models.exceptions import EmptyColumnError, BadRowKeyError
from friendships.hbase_models import HBaseFollower, HBaseFollowing

import time


class FriendshipServiceTests(TestCase):

    def setUp(self):
        #  b  super(FriendshipServiceTests, self).setUp()
        self.clear_cache()
        self.pluto = self.create_user('pluto')
        self.brunch = self.create_user('brunch')

    def test_get_following(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        for followed_user in [user1, user2, self.brunch]:
            Friendship.objects.create(following_user=self.pluto, followed_user=followed_user)
        FriendshipService.invalidate_following_cache(self.pluto.id)

        user_id_set = FriendshipService.get_following_user_id_set(self.pluto.id)
        self.assertEqual(user_id_set, {user1.id, user2.id, self.brunch.id})

        Friendship.objects.filter(following_user=self.pluto, followed_user=self.brunch).delete()
        FriendshipService.invalidate_following_cache(self.pluto.id)
        user_id_set = FriendshipService.get_following_user_id_set(self.pluto.id)
        self.assertEqual(user_id_set, {user1.id, user2.id})


class HBaseTests(TestCase):

    @property
    def ts_now(self):
        return int(time.time() * 1000000)

    def test_save_and_get(self):
        timestamp = self.ts_now
        following = HBaseFollowing(following_user_id=123, followed_user_id=34, created_at=timestamp)
        following.save()

        instance = HBaseFollowing.get(following_user_id=123, created_at=timestamp)
        self.assertEqual(instance.following_user_id, 123)
        self.assertEqual(instance.followed_user_id, 34)
        self.assertEqual(instance.created_at, timestamp)

        following.followed_user_id = 456
        following.save()

        instance = HBaseFollowing.get(following_user_id=123, created_at=timestamp)
        self.assertEqual(instance.followed_user_id, 456)

        instance = HBaseFollowing.get(following_user_id=123, created_at=self.ts_now)
        self.assertEqual(instance, None)

    def test_create_and_get(self):
        # missing column data, cannot store in hbase
        try:
            HBaseFollower.create(followed_user_id=1, created_at=self.ts_now)
            exception_raised = False
        except EmptyColumnError:
            exception_raised = True
        self.assertEqual(exception_raised, True)

        # invalid row key
        try:
            HBaseFollower.create(following_user_id=1, followed_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at is missing in row key.')
        self.assertEqual(exception_raised, True)

        ts = self.ts_now
        HBaseFollower.create(following_user_id=1, followed_user_id=2, created_at=ts)
        instance = HBaseFollower.get(followed_user_id=2, created_at=ts)
        self.assertEqual(instance.following_user_id, 1)
        self.assertEqual(instance.followed_user_id, 2)
        self.assertEqual(instance.created_at, ts)

        # cannot get if row key is missing
        try:
            HBaseFollower.get(followed_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at is missing in row key.')
        self.assertEqual(exception_raised, True)




