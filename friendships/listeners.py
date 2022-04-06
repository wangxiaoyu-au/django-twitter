def invalidate_following_cache(sender, instance, **kwargs):
    # to prevent circular reference,
    # this import sentence should be in def function
    from friendships.services import FriendshipService
    FriendshipService.invalidate_following_cache(instance.following_user_id)