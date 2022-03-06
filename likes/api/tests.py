from testing.testcases import TestCase


LIKE_BASE_URL = '/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'


class LikeApiTests(TestCase):

    def setUp(self):
        self.pluto, self.pluto_client = self.create_user_and_client('pluto')
        self.brunch, self.brunch_client = self.create_user_and_client('brunch')

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.pluto)
        data = {
            'content_type': 'tweet',
            'object_id': tweet.id,
        }

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)
        # action should be POST not GET
        response = self.pluto_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)
        # wrong content type
        response = self.pluto_client.post(LIKE_BASE_URL, {
            'content_type': 'twitter',
            'object_id': tweet.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)
        # wrong object id
        response = self.pluto_client.post(LIKE_BASE_URL, {
            'content_type': 'tweet',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)
        # post likes successfully
        response = self.pluto_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)
        # duplicated likes are ignored
        self.pluto_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        # likes by other user are granted
        self.brunch_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_comment_likes(self):
        tweet = self.create_tweet(self.pluto)
        comment = self.create_comment(self.brunch, tweet)
        data = {
            'content_type': 'comment',
            'object_id': comment.id,
        }

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)
        # action should be POST not GET
        response = self.pluto_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)
        # wrong content type
        response = self.pluto_client.post(LIKE_BASE_URL, {
            'content_type': 'coment',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)
        # wrong object id
        response = self.pluto_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)
        # post likes successfully
        response = self.pluto_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)
        # duplicated likes are ignored
        self.pluto_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 1)
        # likes by other user are granted
        self.brunch_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)

    def test_cancel(self):
        tweet = self.create_tweet(self.pluto)
        comment = self.create_comment(self.brunch, tweet)
        like_comment_data = {
            'content_type': 'comment',
            'object_id': comment.id,
        }
        like_tweet_data = {
            'content_type': 'tweet',
            'object_id': tweet.id,
        }
        self.pluto_client.post(LIKE_BASE_URL, like_comment_data)
        self.brunch_client.post(LIKE_BASE_URL, like_tweet_data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # logged in is mandated
        response = self.anonymous_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 403)
        # the action cancel() should be POST not GET
        response = self.pluto_client.get(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 405)
        # wrong content type
        response = self.pluto_client.post(LIKE_CANCEL_URL, {
            'content_type': 'coment',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)
        # wrong object id
        response = self.pluto_client.post(LIKE_CANCEL_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)

        # brunch has not liked the comment before, this cancel post
        # has no influence on comment's likes
        response = self.brunch_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # pluto canceled successfully on comment
        response = self.pluto_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # pluto has not liked the tweet before, this cancel post
        # has no influence on tweet's likes
        response = self.pluto_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # brunch canceled successfully on tweet
        response = self.brunch_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 0)
