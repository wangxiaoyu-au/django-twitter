from testing.testcases import TestCase
from rest_framework.test import APIClient


COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.pluto = self.create_user('pluto')
        self.pluto_client = APIClient()
        self.pluto_client.force_authenticate(self.pluto)
        self.brunch = self.create_user('brunch')
        self.brunch_client = APIClient()
        self.brunch_client.force_authenticate(self.brunch)

        self.tweet = self.create_tweet(self.pluto)

    def test_create(self):
        # logged in is mandated
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)
        # must post with attributes: tweet_id, content
        response = self.pluto_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)
        # cannot post only with tweet_id
        response = self.pluto_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)
        # cannot post only with content
        response = self.pluto_client.post(COMMENT_URL, {'content': 'Meow!'})
        self.assertEqual(response.status_code, 400)
        # cannot post too long content
        response = self.pluto_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'M' * 141,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)
        # post comment successfully
        response = self.pluto_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'Meow!',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.pluto.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], 'Meow!')


