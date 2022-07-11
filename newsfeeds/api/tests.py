from rest_framework.test import APIClient
from testing.testcases import TestCase
from utils.paginations import EndlessPagination
from django.conf import settings
from friendships.models import Friendship
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        super(NewsFeedApiTests, self).setUp()
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
        self.assertEqual(len(response.data['results']), 0)
        # one can view the tweets that posted by him/herself in the newsfeeds
        self.pluto_client.post(
            POST_TWEETS_URL,
            {'content': 'Meow World'},
        )
        response = self.pluto_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 1)
        # one can view the tweets that posted by who one is following in the newsfeeds
        self.pluto_client.post(FOLLOW_URL.format(self.brunch.id))
        response = self.brunch_client.post(
            POST_TWEETS_URL,
            {'content': 'Meow Friends'},
        )
        posted_tweet_id = response.data['id']
        response = self.pluto_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        newsfeeds = []
        for i in range(page_size * 2):
            tweet = self.create_tweet(followed_user)
            newsfeed = self.create_newsfeed(user=self.pluto, tweet=tweet)
            newsfeeds.append(newsfeed)

        newsfeeds = newsfeeds[::-1]

        # pull the first page
        response = self.pluto_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            newsfeeds[page_size - 1].id,
        )

        # pull the second page
        response = self.pluto_client.get(
            NEWSFEEDS_URL,
            {'created_at__lt': newsfeeds[page_size - 1].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[page_size + 1].id)
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            newsfeeds[2 * page_size - 1].id,
        )

        # pull the latest newsfeed
        response = self.pluto_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        new_tweet = self.create_tweet(followed_user)
        new_newsfeed = self.create_newsfeed(user=self.pluto, tweet=new_tweet)

        response = self.pluto_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_newsfeed.id)

    def test_user_cache(self):
        profile = self.brunch.profile
        profile.nickname = 'Chubby'
        profile.save()

        self.assertEqual(self.pluto.username, 'pluto')
        self.create_newsfeed(self.brunch, self.create_tweet(self.pluto))
        self.create_newsfeed(self.brunch, self.create_tweet(self.brunch))

        response = self.brunch_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'brunch')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'Chubby')
        self.assertEqual(results[1]['tweet']['user']['username'], 'pluto')

        self.pluto.username = 'plutokitty'
        self.pluto.save()
        profile.nickname = 'PangPang'
        profile.save()

        response = self.brunch_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'brunch')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'PangPang')
        self.assertEqual(results[1]['tweet']['user']['username'], 'plutokitty')


    def test_tweet_cache(self):
        tweet = self.create_tweet(self.pluto, 'Meow')
        self.create_newsfeed(self.brunch, tweet)
        response = self.brunch_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'pluto')
        self.assertEqual(results[0]['tweet']['content'], 'Meow')

        # update username
        self.pluto.username = 'Fluffy'
        self.pluto.save()
        response = self.brunch_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'Fluffy')

        # update content
        tweet.content = 'Eat'
        tweet.save()
        response = self.brunch_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['content'], 'Eat')

    def _paginate_to_get_newsfeeds(self,client):
        # paginate until the end
        response = client.get(NEWSFEEDS_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEEDS_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = EndlessPagination.page_size
        users = [self.create_user('user{}'.format(i)) for i in range(5)]
        newsfeeds = []

        # create the newsfeeds under the user pluto,
        # the previous list_limit data records would be cached,
        # the remaining page_size data records need go to database to query
        for i in range(list_limit + page_size):
            tweet = self.create_tweet(user=users[i % 5], content='feed{}'.format(i))
            feed = self.create_newsfeed(self.pluto, tweet)
            newsfeeds.append(feed)
        newsfeeds = newsfeeds[::-1]

        # only cached list_limit objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.pluto.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        queryset = NewsFeed.objects.filter(user=self.pluto)
        self.assertEqual(queryset.count(), list_limit + page_size)

        results = self._paginate_to_get_newsfeeds(self.pluto_client)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].id, results[i]['id'])

        # a followed user create a new tweet
        self.create_friendship(self.pluto, self.brunch)
        new_tweet = self.create_tweet(self.brunch, 'a new tweet')
        NewsFeedService.fanout_to_followers(new_tweet)

        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_newsfeeds(self.pluto_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            self.assertEqual(results[0]['tweet']['id'], new_tweet.id)
            for i in range(list_limit + page_size):
                self.assertEqual(newsfeeds[i].id, results[i + 1]['id'])

        _test_newsfeeds_after_new_feed_pushed()

        # cache expired
        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()























