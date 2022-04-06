from friendships.models import Friendship
from friendships.services import FriendshipService
from testing.testcases import TestCase


class FriendshipServiceTests(TestCase):

    def setUp(self):
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
