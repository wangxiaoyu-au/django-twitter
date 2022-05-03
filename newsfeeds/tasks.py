from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from tweets.models import Tweet
from celery import shared_task
from utils.time_constants import ONE_HOUR


@shared_task(time_limit=ONE_HOUR)
def fanout_newsfeeds_task(tweet_id):
    # to prevent circular dependency, write the import mark below
    from newsfeeds.services import NewsFeedService
    tweet = Tweet.objects.get(id=tweet_id)

    # incorrect implementation:
    # put sql operation in for loop
    # followers = FriendshipService.get_followers(tweet.user)
    # for follower in followers:
    #     NewsFeed.objects.create(user=follower, tweet=tweet)

    # correct implementation:
    # using bulk_create()
    newsfeeds = [
        NewsFeed(user=follower, tweet=tweet) for
        follower in FriendshipService.get_followers(tweet.user)
    ]
    newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
    NewsFeed.objects.bulk_create(newsfeeds)

    # bulk_create() cannot trigger post_save signal,
    # that's why we need push newsfeeds one by one into cache manually
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)