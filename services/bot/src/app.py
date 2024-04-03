"""
    Bot runner.
"""

import os
from datetime import datetime
import random
from logger import logger
from redis import Redis
import discord
from openai import OpenAI
from discord.ext import commands
from dotenv import load_dotenv
from bot import (
    active_channels,
    channel_message_ids,
    get_messages,
    num_tokens_from_string,
    trim_message_history,
    response_chance,
    mark_as_read,
    generate_response,
    was_refused,
    is_image
)


# Params -----------------------------------------------------------------------

REDIS_CHANNEL_KEY_PREFIX = "channel"
REDIS_MESSAGE_KEY_PREFIX = "message"
REDIS_RESPONSES_KEY = "responses"
REDIS_RESPONSE_KEY_PREFIX = "response"


MAX_INPUT_TOKENS = 2000
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
openai_client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

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

def bot_run(): # FIXME: refactor.
    """
    Main bot process.
    """

    # Reload Prompts (replace w redis)
    persona = ""
    with open("prompt-persona.txt", encoding="utf-8") as f:
        persona += f.read().strip()
    instruction = ""
    with open("prompt-instruction.txt", encoding="utf-8") as f:
        instruction += f.read().strip()


    for channel_id in active_channels(redis_client,
        hours=ACTIVE_CHANNEL_CUTOFF_HOURS):

        # Ignore channel?
        channel = redis_client.hgetall(f"{REDIS_CHANNEL_KEY_PREFIX}:{channel_id}")
        if int(channel["_parse_messages"]) != 1:
            continue

        message_ids = channel_message_ids(
            redis_client,
            channel_id,
            hours=MESSAGE_HISTORY_CUTOFF_HOURS)

        messages = get_messages(redis_client, message_ids)

        # Ignore a server or user? Filter messages.
        # FIXME: commented out for now.....
        # messages = list(filter(message_filter_for_non_parse_users, messages))
        # messages = list(filter(message_filter_for_non_parse_servers, messages))

        # Are all messages already read?
        if len(list(filter(lambda x:x["read"] == None, messages))) < 1:
            print("NO UNREAD")
            continue

        max_tokens = MAX_INPUT_TOKENS - (
            num_tokens_from_string(instruction)+num_tokens_from_string(persona))

        messages = trim_message_history(messages, max_tokens=max_tokens)

        chance, target_message_id, img_url = response_chance(redis_client, messages)

        print(chance)

        key_message = get_messages(redis_client, [target_message_id])[0]

        roll = random.randrange(100)

        if chance < roll:
            # Mark rejected messages as read.
            mark_as_read(redis_client, messages)
            continue

        completetion = None

        print("------1")

        try:
            completetion = generate_response(
                openai_client,
                messages,
                target_message_id,
                persona,
                instruction)

            logger.debug(completetion)

            # Mark responded to messages as read.
            mark_as_read(redis_client, messages)

        except Exception as error:  # FIXME: too permissive.
            print(error)
            print("an error")
            # FIXME: log

        if completetion:
            content = completetion.choices[0].message.content.strip()

            if was_refused(content):
                content = random.choice(["¯\\_(ツ)_/¯", "(╯°□°)╯︵ ┻━┻", "(ง'̀-'́)ง", "ಠ_ಠ"])

            completion_id = completetion.id.replace("chatcmpl-", "")

            redis_client.json().set(f"{REDIS_MESSAGE_KEY_PREFIX}:{target_message_id}", ".response", completion_id)

            key_message = get_messages(redis_client, [target_message_id])[0]

            k = f"{key_message['origin']['server']['id']}.{key_message['origin']['server']['channel']['id']}.{key_message['user']['id']}-{completion_id}"

            redis_client.zadd(REDIS_RESPONSES_KEY, {k: datetime.now().timestamp()})

            redis_client.hset(
                f"{REDIS_RESPONSE_KEY_PREFIX}:{completion_id}",
                mapping={
                    "user": key_message["user"]["id"],
                    "content": content,
                    "message": target_message_id,
                    "channel_id": key_message["origin"]["server"]["channel"]["id"],
                    "server_id": key_message["origin"]["server"]["id"],
                    "sent": "",
                    "time":datetime.now().timestamp()
                },
            )

while True:
    bot_run()
