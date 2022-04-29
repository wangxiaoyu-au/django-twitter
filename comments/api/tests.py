from testing.testcases import TestCase
from comments.models import Comment
from django.utils import timezone

COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.pluto, self.pluto_client = self.create_user_and_client('pluto')
        self.brunch, self.brunch_client = self.create_user_and_client('brunch')
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

    def test_comments_count(self):
        # test tweet detail api
        tweet = self.create_tweet(self.pluto)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.brunch_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 0)

        # test tweet list api
        self.create_comment(self.pluto, tweet)
        response = self.brunch_client.get(TWEET_LIST_API, {'user_id': self.pluto.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['comments_count'], 1)

        # test newsfeed list api
        self.create_comment(self.brunch, tweet)
        self.create_newsfeed(self.brunch, tweet)
        response = self.brunch_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['comments_count'], 2)

    def test_comments_count_with_cache(self):
        tweet_url = '/api/tweets/{}/'.format(self.tweet.id)
        response = self.pluto_client.get(tweet_url)
        self.assertEqual(self.tweet.comments_count, 0)
        self.assertEqual(response.data['comments_count'], 0)

        data = {'tweet_id': self.tweet.id, 'content': 'Meow meow'}
        for i in range(2):
            _, client = self.create_user_and_client('kitten{}'.format(i))
            client.post(COMMENT_URL, data)
            response = client.get(tweet_url)
            self.assertEqual(response.data['comments_count'], i + 1)
            self.tweet.refresh_from_db()
            self.assertEqual(self.tweet.comments_count, i + 1)

        comment_data = self.brunch_client.post(COMMENT_URL, data).data
        response = self.brunch_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 3)

        # update comment should not update comments_count
        comment_url = '{}{}/'.format(COMMENT_URL, comment_data['id'])
        response = self.brunch_client.put(comment_url, {'content': 'Meeeeeow'})
        self.assertEqual(response.status_code, 200)
        response = self.brunch_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 3)

        # delete a comment
        response = self.brunch_client.delete(comment_url)
        self.assertEqual(response.status_code, 200)
        response = self.pluto_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 2)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 2)
