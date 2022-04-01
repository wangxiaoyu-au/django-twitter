from friendships.models import Friendship
# from django.contrib.auth.models import User


class FriendshipService(object):

    @classmethod
    def get_followers(cls, user):

        # incorrect implementation 1:
        # end up with N + 1 Queries:
        # filter() is one Query, and then the for loop operation produced N-time Queries
        # friendships = Friendship.objects.filter(followed_user=user)
        # return [friendship.following_user for friendship in friendships]

        # incorrect implementation 2:
        # this way would introduce JOIN operation (select_related) in mysql,
        # friendship table and user table would JOIN together on argument following_user,
        # which would highly possibly retard the whole process.
        # friendships = Friendship.objects.filter(
        #     followed_user=user
        # ).select_related('following_user')
        # return [friendship.following_user for friendship in friendships]

        # correct implementation 1:
        # filter user_id instead of user, then using IN Query
        # friendships = Friendship.objects.filter(followed_user=user)
        # follower_ids = [friendship.following_user_id for friendship in friendships]
        # followers = User.objects.filter(id__in=follower_ids)

        # correct implementation 2:
        # using prefetch_related()
        # is equivalent to correct implementation 1
        friendships = Friendship.objects.filter(
            followed_user=user
        ).prefetch_related('following_user')
        return [friendship.following_user for friendship in friendships]

    @classmethod
    def has_followed(cls, following_user, followed_user):
        return Friendship.objects.filter(
            following_user=following_user,
            followed_user=followed_user,
        ).exists()







