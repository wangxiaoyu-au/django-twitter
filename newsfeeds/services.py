from newsfeeds.models import NewsFeed
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper
from newsfeeds.tasks import fanout_newsfeeds_main_task


class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        # in the message queue created by celery,
        # we build a fanout task whose argument is tweet,
        # any worker that is listening to this message queue
        # has a chance to get this task,
        # it would implement an asynchronous fanout_newsfeeds_task.
        # Notice that .delay() can only accept arguments
        # which can be serialized by celery,
        # i.e., tweet.id is a valid argument, but tweet is not,
        # cause celery doesn't know how to serialize Tweet.
        fanout_newsfeeds_main_task.delay(tweet.id, tweet.user_id)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.download_objects_from_cache(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed, queryset)
