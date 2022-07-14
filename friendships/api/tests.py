from testing.testcases import TestCase
from friendships.models import Friendship
from rest_framework.test import APIClient
from friendships.api.paginations import CustomizedPagination


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
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
            self.create_friendship(follower, self.brunch)
        for i in range(3):
            following = self.create_user('brunch_following{}'.format(i))
            self.create_friendship(self.brunch, following)

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
        self.assertEqual(len(response.data['results'  ]), 3)

        # make sure the following in time descending orders
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'brunch_following2',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'brunch_following1',
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
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
        self.assertEqual(len(response.data['results']), 2)

        # make sure the followers in time descending orders
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'brunch_follower1',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'brunch_follower0',
        )

    def test_followings_pagination(self):
        max_page_size = CustomizedPagination.max_page_size
        page_size = CustomizedPagination.page_size
        for i in range(page_size * 2):
            followed_user = self.create_user('pluto_following{}'.format(i))
            Friendship.objects.create(
                following_user=self.pluto,
                followed_user=followed_user,
            )
            if followed_user.id % 2 == 0:
                Friendship.objects.create(
                    following_user=self.brunch,
                    followed_user=followed_user,
                )
        url = FOLLOWINGS_URL.format(self.pluto.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous user hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # brunch has followed users with even id
        response = self.brunch_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # pluto has followed all following users
        response = self.pluto_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

    def test_followers_pagination(self):
        max_page_size = CustomizedPagination.max_page_size
        page_size = CustomizedPagination.page_size
        for i in range(page_size * 2):
            following_user = self.create_user('pluto_follower{}'.format(i))
            Friendship.objects.create(
                following_user=following_user,
                followed_user=self.pluto,
            )
            if following_user.id % 2 == 0:
                Friendship.objects.create(
                    following_user=self.brunch,
                    followed_user=following_user,
                )
        url = FOLLOWERS_URL.format(self.pluto.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous user hasn't been followed by any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # brunch has been followed by users with even id
        response = self.brunch_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def _test_friendship_pagination(self, url, page_size, max_page_size):
        response = self.anonymous_client.get(url, {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        response = self.anonymous_client.get(url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['has_next_page'], False)

        response = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(response.status_code, 404)

        # user cannot customize page_size exceeds max_page_size
        response = self.anonymous_client.get(url, {'page': 1, 'size': max_page_size + 1})
        self.assertEqual(len(response.data['results']), max_page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        # user can customize page size by param 'size'
        size = 4
        response = self.anonymous_client.get(url, {'page': 1, 'size': size})
        self.assertEqual(len(response.data['results']), size)
        self.assertEqual(response.data['total_pages'], page_size * 2 / size)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

































