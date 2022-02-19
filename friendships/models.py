from django.db import models
from django.contrib.auth.models import User


# Create your models here.
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
        return '{} is following {}.'.format(self.following_user,self.followed_user)
