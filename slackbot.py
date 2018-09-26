#!/usr/bin/env python
"""
This is Slackbot. Slackbot is a bot on Slack that enjoys long walks on the
beach and other wholesome human activities. Please treat Slackbot with the
kind of respect that only a bot on slack commands.
"""
import signal
import logging
import logging.handlers
import time
import re
import random
import requests
from settings import SLACK_BOT_TOKEN, BOT_ID
from slackclient import SlackClient

# Sets up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s : %(name)s : %(levelname)s : %(threadName)s : %(message)s')

file_handler = logging.handlers.RotatingFileHandler(
    'slackbot.log', maxBytes=5*1024*1024, backupCount=2)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# instantiate Slack client
slack_client = SlackClient(SLACK_BOT_TOKEN)
# slackbot's user ID in Slack: value is assigned after the bot starts up
slackbot_id = None

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
# commands
PING_COMMAND = "ping"
EXIT_COMMAND = "exit"
QUIT_COMMAND = "quit"
HELP_COMMAND = "help"
# variables
exit_flag = False
start_time = time.time()


def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT.
    With the global flag, and main() will exit its loop
    if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """
    signames = dict((k, v) for v, k in reversed(
        sorted(signal.__dict__.items()))
        if v.startswith('SIG') and not v.startswith('SIG_'))
    logger.warn('Received {}'.format(signames[sig_num]))
    global exit_flag
    exit_flag = True


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot
        commands.
        If a bot command is found, this function returns a tuple of
        command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == BOT_ID:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (at the beginning) in message text and returns
        the user ID which was mentioned.
        If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the userid,
    # the second group contains the remaining message
    if matches:
        logger.debug('userid: {} message: {}'.format(matches.group(1),
                                                     matches.group(2).strip()))
    return ((matches.group(1), matches.group(2).strip())
            if matches else (None, None))


def handle_command(command, channel):
    """
        Executes bot command if the command is known.
        Sends message
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(
        HELP_COMMAND)
    # Finds and executes the given command, filling in response
    response = None
    attachments = None
    # Here are all the commands!
    if command is None:
        raise Exception
    if command.startswith(PING_COMMAND):
        response = "I've been here for these many seconds: {}".format(
            time.time() - start_time)
    if command.startswith(EXIT_COMMAND) or command.startswith(QUIT_COMMAND):
        goodbyes = ["I leave of my own accord.",
                    "Catch ya later, alligator.",
                    "I'll be back.",
                    "No."]
        response = random.choice(goodbyes)
        if response is not "No.":
            global exit_flag
            exit_flag = True
    if command.startswith(HELP_COMMAND):
        response = "Here are some basic commands:"
        attachments = [
            {"title": "Current bitcoin rate in USD",
                "text": "`bitcoin`",
                "color": "#5780CD"},
            {"title": "random pic",
                "text": "`pic`",
                "color": "#5780CD"},
            {"title": "ptr_bot will plagiarize your diction",
                "text": "`echo <text>`",
                "color": "#5780CD"},
            {"title": "how long ptr_bot's been chillin'",
                "text": "`{}`".format(PING_COMMAND),
                "color": "#5780CD"},
            {"title": "how to play with ptr_bot",
                "text": "`{}`".format(HELP_COMMAND),
                "color": "#5780CD"},
            {"title": "ptr_bot will leave if desired",
                "text": "`{}` or `{}`".format(EXIT_COMMAND, QUIT_COMMAND),
                "color": "#5780CD"}
        ]
    if command.startswith("echo"):
        response = command[5:]
    if command.startswith("pic"):
        response = "I'll just leave this here..."
        attachments = [
            {
                "title": "ur_pic_sir_or_madam",
                "image_url": "https://picsum.photos/200/300?image={}".format(
                    random.randint(1, 100))
            }
        ]
    if command.startswith("bitcoin"):
        r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
        r = r.json()['bpi']['USD']['rate']
        response = 'The current Bitcoin price is: $' + r
    # Sends the response back to the channel
    logger.debug('channel: {} response: {} attachments: {}'.format(
        channel, response, attachments))
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response,
        attachments=attachments,
        icon_emoji=':robot_face:'
    )


def list_channels():
    """
    Hits the api for a list of channels, returns channel's info if found.
    Returns None if not found.
    """
    channels_call = slack_client.api_call("channels.list")
    if channels_call.get("ok"):
        return channels_call["channels"]
    return None


if __name__ == "__main__":
    # signal_handler will get called if OS sends
    # SIGINT or SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # if slack_client connects, then do the things
    while not exit_flag:
        try:
            if slack_client.rtm_connect(with_team_state=False):
                logger.info("ptr_bot connected and running!")
                # Runs through available channels and sends message
                for c in list_channels():
                    slack_client.api_call("chat.postMessage",
                                          channel=c["id"], text="Greetings"
                                          "and salutations!")
                    logger.info('channel name: {}, channel id: {},'.format(
                        c["name"], c["id"])
                        + ' msg: Greetings '
                        + 'and salutations!'
                    )
                # Read bot's user ID by calling Web API method `auth.test`
                slackbot_id = slack_client.api_call("auth.test")["user_id"]
                logger.info('slackbot_id: {}'.format(slackbot_id))
                while not exit_flag:
                    slack_client.api_call("apt.test")
                    command, channel = parse_bot_commands(
                        slack_client.rtm_read())
                    if command:
                        logger.debug(
                            'command: {}, channel: {}'.format(
                                command, channel))
                        handle_command(command, channel)
                    time.sleep(RTM_READ_DELAY)
            else:
                logger.info(
                    "Connection failed. Exception traceback printed above.")
                time.sleep(5)
        except Exception as e:
            logger.error(e)
            logger.info("Error connecting...retrying")
            time.sleep(5)
    logger.info("Uptime: {}".format(time.time() - start_time))
