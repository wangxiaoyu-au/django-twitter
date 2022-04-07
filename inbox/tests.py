from testing.testcases import TestCase
from inbox.services import NotificationService
from notifications.models import Notification


class NotificationServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.pluto = self.create_user('pluto')
        self.brunch = self.create_user('brunch')
        self.pluto_tweet = self.create_tweet(self.pluto)

    def test_send_comment_notification(self):
        # do not dispatch notification if tweet.user == comment.user
        comment = self.create_comment(self.pluto, self.pluto_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet.user != comment.user
        comment = self.create_comment(self.brunch, self.pluto_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        # do not dispatch notification if tweet.user == like.user
        like = self.create_like(self.pluto, self.pluto_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet.user != comment.user
        like = self.create_like(self.brunch, self.pluto_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)