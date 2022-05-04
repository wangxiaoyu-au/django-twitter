from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from tweets.models import Tweet
from celery import shared_task
from utils.time_constants import ONE_HOUR
from newsfeeds.constants import FANOUT_BATCH_SIZE


@shared_task(routing_key='newsfeeds', time_limit=ONE_HOUR)
def fanout_newsfeeds_batch_task(tweet_id, follower_ids):
    # to prevent circular dependency, write the import mark below
    from newsfeeds.services import NewsFeedService
    newsfeeds = [
        NewsFeed(user_id=follower_id, tweet_id=tweet_id)
        for follower_id in follower_ids
    ]
    NewsFeed.objects.bulk_create(newsfeeds)

    # bulk_create() cannot trigger post_save signal,
    # that's why we need push newsfeeds one by one into cache manually
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)

    return '{} newsfeeds have been created.'.format(len(newsfeeds))


@shared_task(routing_key='default', time_limit=ONE_HOUR)
def fanout_newsfeeds_main_task(tweet_id, tweet_user_id):
    # Create a newsfeed to user who posted this tweet in the first place,
    # make sure user believes the newsfeed has been created successfully in no time
    NewsFeed.objects.create(user_id=tweet_user_id, tweet_id=tweet_id)

    # obtain all the followers' ids, then break down into a butch of batch_size sets
    follower_ids = FriendshipService.get_follower_ids(tweet_user_id)
    index = 0
    while index < len(follower_ids):
        batch_ids = follower_ids[index: index + FANOUT_BATCH_SIZE]
        fanout_newsfeeds_batch_task.delay(tweet_id, batch_ids)
        index += FANOUT_BATCH_SIZE

    return '{} newsfeeds are going to fanout, {} batches are created.'.format(
        len(follower_ids),
        (len(follower_ids) - 1) // FANOUT_BATCH_SIZE + 1,
    )