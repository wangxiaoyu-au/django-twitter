from testing.testcases import TestCase
from rest_framework.test import APIClient
from comments.models import Comment
from django.utils import timezone


COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.pluto = self.create_user('pluto')
        self.pluto_client = APIClient()
        self.pluto_client.force_authenticate(self.pluto)
        self.brunch = self.create_user('brunch')
        self.brunch_client = APIClient()
        self.brunch_client.force_authenticate(self.brunch)

        self.tweet = self.create_tweet(self.pluto)

    def test_list(self):
        # tweet_id must be claimed
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)
        # no comment in the first place
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)
        # created comments in time order
        self.create_comment(self.pluto, self.tweet, '1')
        self.create_comment(self.brunch, self.tweet, '2')
        self.create_comment(self.brunch, self.create_tweet(self.brunch), '3')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')
        # if both tweet_id and user_id are provided, only tweet_id works in filter
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.pluto.id,
        })
        self.assertEqual(len(response.data['comments']), 2)

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

    def test_destroy(self):
        comment = self.create_comment(self.pluto, self.tweet)
        url = COMMENT_DETAIL_URL.format(comment.id)

        # logged_in is mandated to delete a comment
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)
        # cannot delete the comments posted by other users
        response = self.brunch_client.delete(url)
        self.assertEqual(response.status_code, 403)
        # delete successfully
        count = Comment.objects.count()
        response = self.pluto_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.create_comment(self.pluto, self.tweet, 'original')
        another_tweet = self.create_tweet(self.brunch, content='brunch posted this tweet.')
        url = COMMENT_DETAIL_URL.format(comment.id)

        response = self.anonymous_client.put(url, {'comment': 'new'})
        self.assertEqual(response.status_code, 403)
        response = self.brunch_client.put(url, {'comment': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')

        # can only update comment's content
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.pluto_client.put(url, {
            'content': 'new',
            'user_id': self.brunch.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.pluto)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)






