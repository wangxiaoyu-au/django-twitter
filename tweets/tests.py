from testing.testcases import TestCase
from datetime import timedelta
from utils.time_helpers import utc_now
from tweets.models import TweetPhoto
from tweets.constants import TweetPhotoStatus


# Create your tests here.
class TweetTests(TestCase):

    def setUp(self):
        self.pluto = self.create_user('pluto')
        self.tweet = self.create_tweet(self.pluto, content = 'We want PEACE, NO WAR!')

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)
        
    def test_like_set(self):
        self.create_like(self.pluto, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        # the same user liked the same comment again,
        # this time the like would be ignored
        self.create_like(self.pluto, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        brunch = self.create_user('brunch')
        self.create_like(brunch, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_create_photo(self):
        photo = TweetPhoto.objects.create(
            tweet=self.tweet,
            user=self.pluto,
        )
        self.assertEqual(photo.user, self.pluto)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)
        self.assertEqual(self.tweet.tweetphoto_set.count(), 1)