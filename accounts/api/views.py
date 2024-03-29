from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import (
    authenticate as django_authenticate,
    login as django_login,
    logout as django_logout,
)
from accounts.models import UserProfile
from accounts.api.serializers import (
    SignupSerializer,
    LoginSerializer,
    UserProfileSerializerForUpdate,
    UserSerializer,
    UserSerializerWithProfile,
)

from utils.permissions import IsObjectOwner
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit



class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializerWithProfile
    permission_classes = (permissions.IsAdminUser,)


class AccountViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def signup(self, request):
        """
        Using username, email, password to SIGN IN
        """
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)

        user = serializer.save()
        django_login(request, user)
        return Response({
            'success': True,
            'user': UserSerializer(user).data,
        }, status=201)

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def login(self, request):
        """
        Get username and password from request,
        By default, username is 'admin', password is 'admin'
        """
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)

        # validation has no issues, log in
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # For code style consistence, the login validation could be implemented in serializers.py,
        # like signup validation part
        # if not User.objects.filter(username=username).exists():
        #     return Response({
        #         'success': False,
        #         'message': "User does not exist.",
        #     }, status=400)

        user = django_authenticate(username=username, password=password)
        if not user or user.is_anonymous:
            return Response({
                'success': False,
                'message': "username and password does not match",
            }, status=400)

        django_login(request, user)
        return Response({
            'success': True,
            'user': UserSerializer(instance=user).data,
        })

    @action(methods=['GET'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='GET', block=True))
    def login_status(self, request):
        """
        check the current status and details of the user
        """
        data = {
            'has_logged_in': request.user.is_authenticated,
            'ip': request.META['REMOTE_ADDR'],
        }
        if request.user.is_authenticated:
            data['user'] = UserSerializer(request.user).data
        return Response(data)

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def logout(self, request):
        django_logout(request)
        return Response({'success': True})


class UserProfileViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.UpdateModelMixin,
):
    queryset = UserProfile
    permission_classes = (IsAuthenticated, IsObjectOwner)
    serializer_class = UserProfileSerializerForUpdate
