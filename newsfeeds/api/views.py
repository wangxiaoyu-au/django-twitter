from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.api.serializers import NewsFeedSerializer
from utils.paginations import EndlessPagination
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    @method_decorator(ratelimit(key='user', rate='5/s', method='GET', block=True))
    def list(self, request):
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(request.user.id)
        newsfeed_page = self.paginator.paginate_cached_list(cached_newsfeeds, request)
        if newsfeed_page is None:
            queryset = NewsFeed.objects.filter(user=request.user)
            newsfeed_page = self.paginate_queryset(queryset)

        serializer = NewsFeedSerializer(
            newsfeed_page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)


