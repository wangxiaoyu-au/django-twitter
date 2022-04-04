from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from friendships.models import Friendship
from friendships.api.serializers import (
    FollowingSerializer,
    FollowerSerializer,
    FriendshipSerializerForCreate,
)
from django.contrib.auth.models import User
from friendships.api.paginations import CustomizedPagination


class FriendshipViewSet(viewsets.GenericViewSet):
    serializer_class = FriendshipSerializerForCreate
    queryset = User.objects.all()
    pagination_class = CustomizedPagination

    # pk is short for primary key, which is id
    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        # GET /api/friendships/1/followers/
        friendships = Friendship.objects.filter(followed_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        friendships = Friendship.objects.filter(following_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowingSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        if Friendship.objects.filter(following_user=request.user,followed_user=pk).exists():
            # if multiple clicks on 'follow' button happened at the front end,
            # process it silently
            return Response({
                'success': True,
                'duplicated': True,
            }, status=status.HTTP_201_CREATED)
        #  POST /api/friendships/<pk>/follow/
        serializer = FriendshipSerializerForCreate(data={
            'following_user_id': request.user.id,
            'followed_user_id': pk,
        })
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(
            FollowingSerializer(instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        # check the unfollowed user exists or not,
        # if the latter case, return 404 not found
        unfollow_user = self.get_object()
        if request.user.id == unfollow_user.id:
            return Response({
                'success': False,
                'message': 'You cannot unfollow yourself.',
            }, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = Friendship.objects.filter(
            following_user=request.user,
            followed_user=unfollow_user,
        ).delete()
        return Response({'success': True, 'deleted': deleted})

    def list(self, request):
        return Response({'message': 'This is friendships home page.'})