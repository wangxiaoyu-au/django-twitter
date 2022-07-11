from accounts.models import UserProfile
from testing.testcases import TestCase


class UserProfileTests(TestCase):

    def setUp(self):
        super(UserProfileTests, self).setUp()

    def test_profile_property(self):
        pluto = self.create_user('pluto')
        self.assertEqual(UserProfile.objects.count(), 0)
        pf = pluto.profile
        self.assertEqual(isinstance(pf, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)