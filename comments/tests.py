from testing.testcases import TestCase


class CommentModelTests(TestCase):

    def setUp(self):
        self.pluto = self.create_user('pluto')
        self.tweet = self.create_tweet(self.pluto)
        self.comment = self.create_comment(self.pluto, self.tweet)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        self.create_like(self.pluto, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        # the same user liked the same comment again,
        # this time the like would be ignored
        self.create_like(self.pluto, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        brunch = self.create_user('brunch')
        self.create_like(brunch, self.comment)
        self.assertEqual(self.comment.like_set.count(), 2)