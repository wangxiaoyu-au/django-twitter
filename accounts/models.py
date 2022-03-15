from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    # OneToOneField creates a unique index, to make sure the case that
    # multiple UserProfiles point to one User not happen
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    avatar = models.FileField(null=True)
    # As long as a user created, an object of UserProfile
    # would be created either, but the a few information like nickname
    # has not been set, that's why null=True
    nickname = models.CharField(null=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.user, self.nickname)


def get_profile(user):
    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    setattr(user, '_cached_user_profile', profile)
    return profile


# to instant access the attribute User.profile
User.profile = property(get_profile)
