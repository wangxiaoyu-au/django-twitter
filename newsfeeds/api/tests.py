from rest_framework.test import APIClient
from testing.testcases import TestCase


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.pluto = self.create_user('pluto')
        self.pluto_client = APIClient()
        self.pluto_client.force_authenticate(self.pluto)

        self.brunch = self.create_user('brunch')
        self.brunch_client = APIClient()
        self.brunch_client.force_authenticate(self.brunch)

    def test_list(self):
        # logged in is mandated
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)
        # action should not be POST
        response = self.pluto_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)
        # at the first place no newsfeeds
        response = self.pluto_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # one can view the tweets that posted by him/herself in the newsfeeds
        self.pluto_client.post(
            POST_TWEETS_URL,
            {'content': 'Meow World'},
        )
        response = self.pluto_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        # one can view the tweets that posted by who one is following in the newsfeeds
        self.pluto_client.post(FOLLOW_URL.format(self.brunch.id))
        response = self.brunch_client.post(
            POST_TWEETS_URL,
            {'content': 'Meow Friends'},
        )
        posted_tweet_id = response.data['id']
        response = self.pluto_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)