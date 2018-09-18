import unittest
from slackbot import slack_client, list_channels
from settings import SLACK_BOT_TOKEN, BOT_ID


class TestSlackbot(unittest.TestCase):

    def test_auth(self):
        self.assertEqual(slack_client.api_call("auth.test").get("ok"), True)

    def test_env(self):
        self.assertTrue(SLACK_BOT_TOKEN)
        self.assertTrue(BOT_ID)

    def test_list_channels(self):
        self.assertTrue(list_channels())


if __name__ == '__main__':
    unittest.main()
