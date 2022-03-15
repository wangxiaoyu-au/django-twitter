from testing.testcases import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from accounts.models import UserProfile


LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'


class AccountApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user(
            username='administer',
            email='administer@twitter.com',
            password='correct password',
        )

    # def createUser(self, username, email, password):
    #     # Notice: don't use User.objects.create()
    #     # create_user() enables password encryption, username and email normalization
    #     # which create() doesn't
    #     return User.objects.create_user(username, email, password)

    def test_login(self):
        # login can only use POST method, GET method is forbidden
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        # login failed, http status code returns 405 = METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, 405)

        # input wrong password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        # has not logged in yet
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # input correct password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'administer@twitter.com')

        # has logged in successfully
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        # firstly login
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })

        # user has logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        # use GET method to log out, failed
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # use POST method to log out successfully
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        # has logged out successfully
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@twitter.com',
            'password': 'any password',
        }

        # use GET method to sign up, failed
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        # use invalid email to sign up
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a valid email',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # password is too short
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@twitter.com',
            'password': 'ab123',
        })
        self.assertEqual(response.status_code, 400)

        # username is too long
        response = self.client.post(SIGNUP_URL, {
            'username': 'username is toooooooooooooooo loooooooooooooooooooooong',
            'email': 'someone@twitter.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # sign up successfully
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')
        self.assertEqual(response.data['user']['email'], 'someone@twitter.com')

        # verify user profile has been created
        created_user_username = response.data['user']['username']
        profile = UserProfile.objects.filter(user__username=created_user_username).first()
        self.assertNotEqual(profile, None)

        # after a successful signup, the user has logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)




