from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from newsfeeds.models import NewsFeed
from newsfeeds.api.serializers import NewsFeedSerializer
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        # self-defined queryset, because only the current logged in user
        # can check newsfeed, it can be
        # self.request.user.newsfeed_set.all() either
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        newsfeed_page = self.paginate_queryset(self.get_queryset())
        serializer = NewsFeedSerializer(
            newsfeed_page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)


