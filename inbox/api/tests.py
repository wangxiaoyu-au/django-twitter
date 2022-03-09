from testing.testcases import TestCase
from notifications.models import Notification


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'


class NotificationTests(TestCase):

    def setUp(self):
        self.pluto, self.pluto_client = self.create_user_and_client('pluto')
        self.brunch, self.brunch_client = self.create_user_and_client('brunch')
        self.brunch_tweet = self.create_tweet(self.brunch)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.pluto_client.post(COMMENT_URL, {
            'tweet_id': self.brunch_tweet.id,
            'content': 'Salut!'
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.pluto_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.brunch_tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)