from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import (
    TweetSerializer,
    TweetSerializerForCreate,
    TweetSerializerForDetail,
)
from tweets.models import Tweet
from newsfeeds.services import NewsFeedService
from utils.decorators import required_params
from utils.paginations import EndlessPagination
from tweets.services import TweetService
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit


class TweetViewSet(viewsets.GenericViewSet):
    serializer_class = TweetSerializerForCreate
    queryset = Tweet.objects.all()
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_params(params=['user_id'])
    @method_decorator(ratelimit(key='user_or_ip', rate='5/s', method='GET', block=True))
    def list(self, request):
        user_id = request.query_params['user_id']
        cached_tweets = TweetService.get_cached_tweets(user_id=user_id)
        tweets_page = self.paginator.paginate_cached_list(cached_tweets, request)
        if tweets_page is None:
            queryset = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
            tweets_page = self.paginate_queryset(queryset)

        serializer = TweetSerializer(
            tweets_page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)

    @method_decorator(ratelimit(key='user_or_ip', rate='5/s', method='GET', block=True))
    def retrieve(self, request, *args, **kwargs):
        serializer = TweetSerializerForDetail(
            self.get_object(),
            context={'request': request},
        )
        return Response(serializer.data)

    # For sensitive action, rate limiter combination might be applied
    @method_decorator(ratelimit(key='user', rate='1/s', method='POST', block=True))
    @method_decorator(ratelimit(key='user', rate='5/m', method='POST', block=True))
    def create(self, request):
        serializer = TweetSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input.',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        # save() will call create() in TweetSerializerForCreate
        tweet = serializer.save()
        # fanning out the new posted tweet to all followers
        NewsFeedService.fanout_to_followers(tweet)
        return Response(
            TweetSerializer(tweet, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )