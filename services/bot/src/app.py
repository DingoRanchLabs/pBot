"""
    Bot runner.
"""

import os
from datetime import datetime
# import random
from logger import logger
from redis import Redis
import discord
# from openai import OpenAI
from discord.ext import commands
from dotenv import load_dotenv
from bot import (
    active_channels,
    channel_message_ids,
    get_messages,
    # num_tokens_from_string,
    # trim_message_history,
    # response_chance,
    mark_as_read,
    # generate_response,
    # was_refused,
    is_image
)

from bot.middleware import (
	SimpleOpenAiResponseMiddleware,
    TrimMessagesByTokens
)

# Params -----------------------------------------------------------------------


REDIS_CHANNEL_KEY_PREFIX = "channel"
REDIS_MESSAGE_KEY_PREFIX = "message"
REDIS_RESPONSES_KEY = "responses"
REDIS_RESPONSE_KEY_PREFIX = "response"


# MAX_INPUT_TOKENS = 2000
ACTIVE_CHANNEL_CUTOFF_HOURS = 48
MESSAGE_HISTORY_CUTOFF_HOURS = 48

# --------------------------------------------------------------------- / Params

load_dotenv()

# Set up intents for bot.
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot("", intents=intents)

# Clients
redis_client = Redis(host="redis", port=6379, decode_responses=True)

def message_filter_for_non_parse_users(message):
    """

    """

    user_id = message["user"]

    user = redis_client.hgetall(f"user:{user_id}")

    if user["_parse_messages"] == "1":
        return True
    return False

def message_filter_for_non_parse_servers(message):
    """

    """

    server_id = message["server_id"]
    server = redis_client.hgetall(f"server:{server_id}")
    if server["_parse_messages"] == "1":
        return True
    return False


class PBot:
    middlewares = []

    def __init__(self):
        pass

    def add_middleware(self, middleware):
        self.middlewares.append(middleware)

    def handle_messages(self, messages):
        for middleware in self.middlewares:
            messages = middleware.handle_messages(messages)

    def run(self):
        for channel_id in active_channels(redis_client,
            hours=ACTIVE_CHANNEL_CUTOFF_HOURS):

            # Ignore channel?
            channel = redis_client.hgetall(f"{REDIS_CHANNEL_KEY_PREFIX}:{channel_id}")
            if int(channel["_parse_messages"]) != 1:
                print(f"Ignoring {channel_id}")
                continue

            message_ids = channel_message_ids(
                redis_client,
                channel_id,
                hours=MESSAGE_HISTORY_CUTOFF_HOURS)

            messages = get_messages(redis_client, message_ids)

            # Are all messages already read?
            if len(list(filter(lambda x:x["read"] == None, messages))) < 1:
                continue

            print(f"Handling {len(messages)} messages.")

            self.handle_messages(messages)

            print(f"Cleaning up {len(messages)} messages.")

            mark_as_read(redis_client, messages)


pbot = PBot()

pbot.add_middleware(TrimMessagesByTokens(redis_client))
pbot.add_middleware(SimpleOpenAiResponseMiddleware(redis_client, os.environ.get("OPENAI_KEY")))

while True:
    pbot.run()
