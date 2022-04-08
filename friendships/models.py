from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, post_save
from friendships.listeners import invalidate_following_cache
from utils.memcached_helper import MemcachedHelper


class Friendship(models.Model):
    following_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        # related_name is for reverse query in mysql,
        # for example
        # user.following_friendship_set
        # equals to
        # Following_friendship.objects.filter(user=user)
        related_name='following_friendship_set',
    )
    followed_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='follower_friendship_set',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            # get all users that this account are following
            ('following_user_id', 'created_at'),
            # get all users that being followed this account
            ('followed_user_id', 'created_at'),
        )
        unique_together = (('following_user_id', 'followed_user_id'),)

    def __str__(self):
        return '{} is following {}.'.format(self.following_user, self.followed_user)

    @property
    def cached_following_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.following_user_id)

    @property
    def cached_followed_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.followed_user_id)


# hook up with listeners to invalidate cache
pre_delete.connect(invalidate_following_cache, sender=Friendship)
post_save.connect(invalidate_following_cache, sender=Friendship)
