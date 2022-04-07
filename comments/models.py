from django.db import models
from django.contrib.auth.models import User
from tweets.models import Tweet
from likes.models import Like
from django.contrib.contenttypes.models import ContentType
from accounts.services import UserService


class Comment(models.Model):
    """
    in this version, a relatively simple comment function is implemented,
    it can only comment a tweet, not do the same to this tweet's comments
    """
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    tweet = models.ForeignKey(Tweet, null=True, on_delete=models.SET_NULL)
    # or content = models.TextField(max_length=140)
    content = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # under a certain tweet, all the comments are ordered by created time
        index_together = (('tweet', 'created_at'),)

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.id,
        ).order_by('-created_at')

    def __str__(self):
        return '{} - {} says {} under tweet {}'.format(
            self.created_at,
            self.user,
            self.content,
            self.tweet_id,
        )

    @property
    def cached_user(self):
        return UserService.get_user_through_cache(self.user_id)