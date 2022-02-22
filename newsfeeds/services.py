from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed


class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
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