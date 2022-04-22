from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.api.serializers import NewsFeedSerializer
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def list(self, request):
        newsfeeds = NewsFeedService.get_cached_newsfeeds(request.user.id)
        newsfeed_page = self.paginate_queryset(newsfeeds)
        serializer = NewsFeedSerializer(
            newsfeed_page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)


