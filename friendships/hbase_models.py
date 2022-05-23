from django_hbase import models


class HBaseFollowing(models.HBaseModel):

    """
    This model stores all users followed by following_user_id (like A);
    row_key ordered by following_user_id + created_at;
    support to query:
    - all users followed by A, ordered by created_at time
    - the users followed by A in a certain period
    - the X leading users followed by A before/after a certain time
    """

    # row_key
    following_user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    # column key
    followed_user_id = models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_followings'
        row_key = ('following_user_id', 'created_at')


class HBaseFollower(models.HBaseModel):

    """
    This model stores all users which are following followed_user_id (like A),
    a.k.a A's all followers;
    row_key ordered by followed_user_id + created_at;
    support to query:
    - all A's followers ordered by created_at time
    - in a certain period A is followed by which followers
    - the X leading followers who followed A before/after a certain time
    """

    # row_key
    followed_user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    # column key
    following_user_id = models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_followers'
        row_key = ('followed_user_id', 'created_at')