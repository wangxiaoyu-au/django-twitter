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

    def test_filter(self):
        HBaseFollowing.create(following_user_id=1, followed_user_id=2, created_at=self.ts_now)
        HBaseFollowing.create(following_user_id=1, followed_user_id=3, created_at=self.ts_now)
        HBaseFollowing.create(following_user_id=1, followed_user_id=4, created_at=self.ts_now)

        followings = HBaseFollowing.filter(prefix=(1, None, None))
        self.assertEqual(3, len(followings))
        self.assertEqual(followings[0].following_user_id, 1)
        self.assertEqual(followings[0].followed_user_id, 2)
        self.assertEqual(followings[1].following_user_id, 1)
        self.assertEqual(followings[1].followed_user_id, 3)
        self.assertEqual(followings[2].following_user_id, 1)
        self.assertEqual(followings[2].followed_user_id, 4)

        # test limit
        results = HBaseFollowing.filter(prefix=(1, None, None), limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].followed_user_id, 2)

        results = HBaseFollowing.filter(prefix=(1, None, None), limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].followed_user_id, 2)
        self.assertEqual(results[1].followed_user_id, 3)

        results = HBaseFollowing.filter(prefix=(1, None, None), limit=4)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].followed_user_id, 2)
        self.assertEqual(results[1].followed_user_id, 3)
        self.assertEqual(results[2].followed_user_id, 4)

        results = HBaseFollowing.filter(start=(1, results[1].created_at, None), limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].followed_user_id, 3)
        self.assertEqual(results[1].followed_user_id, 4)

        # test reverse
        results = HBaseFollowing.filter(prefix=(1, None, None), limit=2, reverse=True)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].followed_user_id, 4)
        self.assertEqual(results[1].followed_user_id, 3)

        results = HBaseFollowing.filter(start=(1, results[1].created_at, None), limit=2, reverse=True)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].followed_user_id, 3)
        self.assertEqual(results[1].followed_user_id, 2 )
















