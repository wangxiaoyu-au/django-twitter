from testing.testcases import TestCase
from notifications.models import Notification


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'


class NotificationTests(TestCase):

    def setUp(self):
        self.clear_cache()
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


class NotificationApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.pluto, self.pluto_client = self.create_user_and_client('pluto')
        self.brunch, self.brunch_client = self.create_user_and_client('brunch')
        self.pluto_tweet = self.create_tweet(self.pluto)

    def test_unread_count(self):
        self.brunch_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.pluto_tweet.id,
        })

        url = '/api/notifications/unread-count/'
        response = self.pluto_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        comment = self.create_comment(self.pluto, self.pluto_tweet)
        self.brunch_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.pluto_client.get(url)
        self.assertEqual(response.data['unread_count'], 2)
        response = self.brunch_client.get(url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_mark_all_as_read(self):
        self.brunch_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.pluto_tweet.id,
        })
        comment = self.create_comment(self.pluto, self.pluto_tweet)
        self.brunch_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        unread_url = '/api/notifications/unread-count/'
        response = self.pluto_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        mark_url = '/api/notifications/mark-all-as-read/'
        # brunch cannot mark pluto's notifications as read
        response = self.brunch_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 0)

        response = self.pluto_client.get(mark_url)
        self.assertEqual(response.status_code, 405)
        response = self.pluto_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.pluto_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        self.brunch_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.pluto_tweet.id,
        })
        comment = self.create_comment(self.pluto, self.pluto_tweet)
        self.brunch_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)
        # brunch views no notifications
        response = self.brunch_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        # pluto views 2 notifications
        response = self.pluto_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        notification = self.pluto.notifications.first()
        notification.unread = False
        notification.save()
        response = self.pluto_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.pluto_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.pluto_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)

    def test_update(self):
        self.brunch_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.pluto_tweet.id,
        })
        comment = self.create_comment(self.pluto, self.pluto_tweet)
        self.brunch_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        notification = self.pluto.notifications.first()

        url = '/api/notifications/{}/'.format(notification.id)

        # action method should be PUT not POST
        response = self.pluto_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)
        # updated by anonymous is forbidden
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)
        # updated by other users would fail in filtering step,
        # get_object() would return 404
        response = self.brunch_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)

        # updated successfully
        response = self.pluto_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        unread_url = '/api/notifications/unread-count/'
        response = self.pluto_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 1)
        # reversely verification
        response = self.pluto_client.put(url, {'unread': True})
        response = self.pluto_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        # unread field must be included
        response = self.pluto_client.put(url, {'verb': 'new verb'})
        self.assertEqual(response.status_code, 400)
        # only unread field can be updated
        response = self.pluto_client.put(url, {'verb': 'new verb', 'unread': False})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'new verb')















