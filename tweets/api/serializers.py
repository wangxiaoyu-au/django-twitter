from rest_framework import serializers
from tweets.models import Tweet
from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()

    class Meta:
        model = Tweet
        fields = ('id', 'user', 'created_at', 'content')


class TweetSerializerWithComments(TweetSerializer):
    # To get comments of a certain tweet, there are multiple ways,
    # except claimed 'source=comments__set' like below,
    # we can also
    # 1. add a method in Tweet model like:
    # @property
    # def comments(self):
    #     return self.comment_set.all()
    # or
    # 2. use serializers.SerializerMethodField
    # comments = serializers.SerializerMethodField()
    # def get_comments(self, obj): # here obj is tweet
    #     return CommentSerializer(obj.comment_set.all(), many=True).data

    comments = CommentSerializer(source='comment_set', many=True)

    class Meta:
        model = Tweet
        fields = ('id', 'user', 'created_at', 'content', 'comments')


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





