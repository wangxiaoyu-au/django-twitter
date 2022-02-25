from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    """
    This Permission is to check whether obj.user == request.user
    Only has_permission would be detected for action whose argument detail=False,
    both has_permission and has_object_permission detected when detail=True.
    When detected failed, IsObjectOwner.message would give message content
    by default.
    """
    message = 'You do not have permission to access this object.'

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user