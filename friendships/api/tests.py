from testing.testcases import TestCase
from friendships.models import Friendship
from rest_framework.test import APIClient


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        # self.anonymous_client = APIClient()

        self.pluto = self.create_user('pluto')
        self.pluto_client = APIClient()
        self.pluto_client.force_authenticate(self.pluto)

        self.brunch = self.create_user('brunch')
        self.brunch_client = APIClient()
        self.brunch_client.force_authenticate(self.brunch)

        # create followings and followers for brunch
        for i in range(2):
            follower = self.create_user('brunch_follower{}'.format(i))
            Friendship.objects.create(following_user=follower, followed_user=self.brunch)
        for i in range(3):
            following = self.create_user('brunch_following{}'.format(i))
            Friendship.objects.create(following_user=self.brunch, followed_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.pluto.id)

        # login is mandated for action 'follow', or return HTTP_403_FORBIDDEN
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # follow should be a 'POST' action, or return HTTP_405_METHOD_NOT_ALLOWED
        response = self.brunch_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot follow yourself
        response = self.pluto_client.post(url)
        self.assertEqual(response.status_code, 400)

        # follow successfully
        response = self.brunch_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual('created_at' in response.data, True)
        self.assertEqual('user' in response.data, True)
        self.assertEqual(response.data['user']['id'], self.pluto.id)
        self.assertEqual(response.data['user']['username'], self.pluto.username)

        # multiple follows would be silenced
        response = self.brunch_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicated'], True)

        # reversed follow would create new instance
        count = Friendship.objects.count()
        response = self.pluto_client.post(FOLLOW_URL.format(self.brunch.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.pluto.id)

        # login is mandated for action 'unfollow', or return HTTP_403_FORBIDDEN
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # unfollow should be a 'POST' action, or return HTTP_405_METHOD_NOT_ALLOWED
        response = self.brunch_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot unfollow yourself
        response = self.pluto_client.post(url)
        self.assertEqual(response.status_code, 400)

        # unfollow successfully
        # create a friendship in the first place
        Friendship.objects.create(following_user=self.brunch, followed_user=self.pluto)
        count = Friendship.objects.count()
        response = self.brunch_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)

        # if the following relationship did not exist, unfollow would be silenced
        count = Friendship.objects.count()
        response = self.brunch_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.brunch.id)

        # post is forbidden
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)

        # make sure the following in time descending orders
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'brunch_following2',
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'brunch_following1',
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'brunch_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.brunch.id)

        # post is forbidden
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)

        # make sure the followers in time descending orders
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'brunch_follower1',
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'brunch_follower0',
        )









