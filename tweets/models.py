from django.db import models
from django.contrib.auth.models import User
from likes.models import Like
from utils.time_helpers import utc_now
from django.contrib.contenttypes.models import ContentType
from tweets.constants import TweetPhotoStatus, TWEET_PHOTO_STATUS_CHOICES
from utils.memcached_helper import MemcachedHelper
from django.db.models.signals import post_save, pre_delete
from tweets.listeners import push_tweet_to_cache
from utils.listeners import invalidate_object_cache


class Tweet(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text='who posts this tweet',
    )
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    # notice that new added fields must set null=True, or
    # default=0 would go through the whole database, giving rise to
    # an extremely slow migration, even the whole database
    # might be deadlocked so that new tweets cannot be created
    likes_count = models.IntegerField(default=0, null=True)
    comments_count = models.IntegerField(default=0, null=True)

    class Meta:
        # create composite index
        index_together = (('user', 'created_at'),)
        ordering = ('user', '-created_at')

    def __str__(self):
        return f'{self.created_at} {self.user}: {self.content}'

    @property
    def hours_to_now(self):
        return (utc_now() - self.created_at).seconds // 3600

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Tweet),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)


class TweetPhoto(models.Model):
    # Image is under which tweet
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)

    # Image is uploaded by who.
    # Though we can get this information from tweet.user either,
    # to prevent from join operation in database, we adopt
    # user as an independent column in this model
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    file = models.FileField()
    order = models.IntegerField(default=0)

    # image status, for use of performing image audit
    status = models.IntegerField(
        default=TweetPhotoStatus.PENDING,
        choices=TWEET_PHOTO_STATUS_CHOICES,
    )

    # soft delete
    has_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            ('user', 'created_at'),
            ('has_deleted', 'created_at'),
            ('status', 'created_at'),
            ('tweet', 'order'),
        )

    def __str__(self):
        return f'{self.tweet_id}: {self.file}'


post_save.connect(invalidate_object_cache, sender=Tweet)
pre_delete.connect(invalidate_object_cache, sender=Tweet)
post_save.connect(push_tweet_to_cache, sender=Tweet)




