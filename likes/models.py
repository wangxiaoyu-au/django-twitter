from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from utils.memcached_helper import MemcachedHelper
from django.db.models.signals import pre_delete, post_save
from likes.listeners import incr_likes_count, decr_likes_count


class Like(models.Model):
    # https://docs.djangoproject.com/en/4.0/ref/contrib/contenttypes/#generic-relations
    # comment_id or tweet_id
    object_id = models.PositiveIntegerField()
    # liked instance is a comment or a tweet
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # in database level to guarantee the like retrieve's uniqueness
        unique_together = (('user', 'content_type', 'object_id'),)
        index_together = (
            # ordering all likes under a certain comment or tweet
            ('content_type', 'object_id', 'created_at'),
            # ordering all comments or tweets that a certain user has liked
            ('user', 'content_type', 'created_at'),
        )

    def __str__(self):
        return '{} - {} liked {} {}'.format(
            self.created_at,
            self.user,
            self.content_type,
            self.object_id,
        )

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)


pre_delete.connect(decr_likes_count, sender=Like)
post_save.connect(incr_likes_count, sender=Like)
