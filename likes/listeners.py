def incr_likes_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    if not created:
        return

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return

    # Way 1: not trigger listeners
    # using F function generate an SQL expression at database level
    # https://docs.djangoproject.com/en/4.0/ref/models/expressions/#f-expressions
    Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)

    # Way 2: can trigger listeners
    # tweet = instance.content_object
    # tweet.likes_count = F('likes_count') + 1
    # tweet.save()


def decr_likes_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return

    Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)