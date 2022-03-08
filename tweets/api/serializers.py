from rest_framework import serializers
from tweets.models import Tweet
from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer
from likes.services import LikeService
from likes.api.serializers import LikeSerializer


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments_count',
            'likes_count',
            'has_liked',
        )

    def get_comments_count(self, obj):
        return obj.comment_set.count()

    def get_likes_count(self, obj):
        return obj.like_set.count()

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)


# class TweetSerializerWithComments(TweetSerializer):
#     # To get comments of a certain tweet, there are multiple ways,
#     # except claimed 'source=comments__set' like below,
#     # we can also
#     # 1. add a method in Tweet model like:
#     # @property
#     # def comments(self):
#     #     return self.comment_set.all()
#     # or
#     # 2. use serializers.SerializerMethodField
#     # comments = serializers.SerializerMethodField()
#     # def get_comments(self, obj): # here obj is tweet
#     #     return CommentSerializer(obj.comment_set.all(), many=True).data
#
#     comments = CommentSerializer(source='comment_set', many=True)
#
#     class Meta:
#         model = Tweet
#         fields = ('id', 'user', 'created_at', 'content', 'comments')


class TweetSerializerForDetail(TweetSerializer):
    comments =  CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'likes',
            'comments',
            'likes_count',
            'comments_count',
            'has_liked',
        )


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=1, max_length=140)

    class Meta:
        model = Tweet
        fields = ('content',)

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet
