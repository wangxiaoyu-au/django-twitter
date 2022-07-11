from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_client import RedisClient
from newsfeeds.tasks import fanout_newsfeeds_main_task


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        super(NewsFeedServiceTests, self).setUp()
        self.pluto = self.create_user('pluto')
        self.brunch = self.create_user('brunch')

    def test_get_user_newsfeeds(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.brunch)
            newsfeed = self.create_newsfeed(self.pluto, tweet)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        # cache miss
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.pluto.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

        # cache hit
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.pluto.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

        # cache updated
        tweet = self.create_tweet(self.pluto)
        new_newsfeed = self.create_newsfeed(self.pluto, tweet)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.pluto.id)
        newsfeed_ids.insert(0, new_newsfeed.id)
        self.assertEqual([newsfeed.id for newsfeed in newsfeeds], newsfeed_ids)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(self.pluto, self.create_tweet(self.pluto))

        RedisClient.clear()
        conn = RedisClient.get_connection()

        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.pluto.id)
        self.assertEqual(conn.exists(key), False)

        feed2 = self.create_newsfeed(self.pluto, self.create_tweet(self.pluto))
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedService.get_cached_newsfeeds(self.pluto.id)
        self.assertEqual([feed.id for feed in feeds], [feed2.id, feed1.id])


class NewsFeedTaskTests(TestCase):

    def setUp(self):
        super(NewsFeedTaskTests, self).setUp()
        self.pluto = self.create_user('pluto')
        self.brunch = self.create_user('brunch')

    def test_fanout_main_task(self):
        tweet = self.create_tweet(self.pluto, 'pluto meows')
        self.create_friendship(self.brunch, self.pluto)
        msg = fanout_newsfeeds_main_task(tweet.id, self.pluto.id)
        self.assertEqual(msg, '1 newsfeeds are going to fanout, 1 batches are created.')
        self.assertEqual(1 + 1, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.pluto.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('user{}'.format(i))
            self.create_friendship(user, self.pluto)
        tweet = self.create_tweet(self.pluto, 'pluto eats')
        msg = fanout_newsfeeds_main_task(tweet.id, self.pluto.id)
        self.assertEqual(msg, '3 newsfeeds are going to fanout, 1 batches are created.')
        self.assertEqual((1 + 1) + (1 + 3), NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.pluto.id)
        self.assertEqual(len(cached_list), 2)

        user = self.create_user('new user')
        self.create_friendship(user, self.pluto)
        tweet = self.create_tweet(self.pluto, 'pluto sleeps')
        msg = fanout_newsfeeds_main_task(tweet.id, self.pluto.id)
        self.assertEqual(msg, '4 newsfeeds are going to fanout, 2 batches are created.')
        # meows + 1 * meows (brunch)
        # eats + 3 * eats (brunch, user0, user1)
        # sleeps + 4 * sleeps (brunch, user0, user1, user)
        self.assertEqual((1 + 1) + (1 + 3) + (1 + 4), NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.pluto.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.brunch.id)
        self.assertEqual(len(cached_list), 3)