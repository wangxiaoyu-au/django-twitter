from testing.testcases import TestCase
from friendships.models import Friendship
from rest_framework.test import APIClient
from friendships.api.paginations import CustomizedPagination
from friendships.services import FriendshipService
from utils.paginations import EndlessPagination


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        super(FriendshipApiTests, self).setUp()

        self.pluto = self.create_user('pluto')
        self.pluto_client = APIClient()
        self.pluto_client.force_authenticate(self.pluto)

        self.brunch = self.create_user('brunch')
        self.brunch_client = APIClient()
        self.brunch_client.force_authenticate(self.brunch)

        # create followings and followers for brunch
        for i in range(2):
            follower = self.create_user('brunch_follower{}'.format(i))
            self.create_friendship(following_user=follower, followed_user=self.brunch)
        for i in range(3):
            following = self.create_user('brunch_following{}'.format(i))
            self.create_friendship(following_user=self.brunch, followed_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.pluto.id)

        # login is mandated for action 'follow', or return HTTP_403_FORBIDDEN
        # response = self.anonymous_client.post(url)
        # self.assertEqual(response.status_code, 403)
        # # follow should be a 'POST' action, or return HTTP_405_METHOD_NOT_ALLOWED
        # response = self.brunch_client.get(url)
        # self.assertEqual(response.status_code, 405)
        # cannot follow yourself
        response = self.brunch_client.post(url)
        self.assertEqual(response.status_code, 201)

        # follow successfully
        # response = self.brunch_client.post(url)
        # self.assertEqual(response.status_code, 201)
        # # multiple follows would be silenced
        # response = self.brunch_client.post(url)
        # self.assertEqual(response.status_code, 201)
        # self.assertEqual(response.data['duplicated'], True)
        #
        # # reversed follow would create new instance
        # before_count = FriendshipService.get_following_count(self.pluto.id)
        # response = self.pluto_client.post(FOLLOW_URL.format(self.brunch.id))
        # self.assertEqual(response.status_code, 201)
        # after_count = FriendshipService.get_following_count(self.pluto.id)
        # self.assertEqual(after_count, before_count + 1)

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
        self.create_friendship(following_user=self.brunch, followed_user=self.pluto)
        before_count = FriendshipService.get_following_count(self.brunch.id)
        response = self.brunch_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        after_count = FriendshipService.get_following_count(self.brunch.id)
        self.assertEqual(after_count, before_count - 1)

        # if the following relationship did not exist, unfollow would be silenced
        before_count = FriendshipService.get_following_count(self.brunch.id)
        response = self.brunch_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        after_count = FriendshipService.get_following_count(self.brunch.id)
        self.assertEqual(after_count, before_count)

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
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            followed_user = self.create_user('pluto_following{}'.format(i))
            friendship = self.create_friendship(
                following_user=self.pluto,
                followed_user=followed_user,
            )
            friendships.append(friendship)
            if followed_user.id % 2 == 0:
                self.create_friendship(
                    following_user=self.brunch,
                    followed_user=followed_user,
                )
        url = FOLLOWINGS_URL.format(self.pluto.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous user hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # brunch has followed users with even id
        response = self.brunch_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # pluto has followed all following users
        response = self.pluto_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

        # test pull new friendships
        last_created_at = friendships[-1].created_at
        response = self.pluto_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(len(response.data['results']), 0)

        new_friends = [self.create_user('new_friend{}'.format(i)) for i in range(3)]
        new_friendships = []
        for friend in new_friends:
            new_friendships.append(
                self.create_friendship(following_user=self.pluto, followed_user=friend)
            )
        response = self.pluto_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(len(response.data['results']), 3)
        for result, friendship in zip(response.data['results'], reversed(new_friends)):
            self.assertEqual(result['created_at'], friendship.created_at)

    def test_followers_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            following_user = self.create_user('pluto_follower{}'.format(i))
            friendship = self.create_friendship(
                following_user=following_user,
                followed_user=self.pluto,
            )
            friendships.append(friendship)
            if following_user.id % 2 == 0:
                self.create_friendship(
                    following_user=self.brunch,
                    followed_user=following_user,
                )
        url = FOLLOWERS_URL.format(self.pluto.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous user hasn't been followed by any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # brunch has been followed by users with even id
        response = self.brunch_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def _paginate_until_the_end(self, url, expect_pages, friendships):
        results, pages = [], 0
        response = self.anonymous_client.get(url)
        results.extend(response.data['results'])
        pages += 1
        while response.data['has_next_page']:
            self.assertEqual(response.status_code, 200)
            last_item = response.data['results'][-1]
            response = self.anonymous_client.get(url, {
                'created_at__lt': last_item['created_at']
            })
            results.extend(response.data['results'])
            pages += 1

        self.assertEqual(len(results), len(friendships))
        self.assertEqual(pages, expect_pages)
        # results in descending order while friendships in ascending order
        for result, friendship in zip(results, friendships[::-1]):
            self.assertEqual(result['created_at'], friendship.created_at)


