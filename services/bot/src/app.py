"""
Bot runner.
"""
import os
from datetime import datetime
import random
#
from redis import Redis
import discord
from openai import OpenAI
from discord.ext import commands
from dotenv import load_dotenv
#
from logger import logger
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

# Vars -------------------------------------------------------------------------

MAX_INPUT_TOKENS = 2000
ACTIVE_CHANNEL_CUTOFF_HOURS = 48
MESSAGE_HISTORY_CUTOFF_HOURS = 48

# ------------------------------------------------------------------------ /Vars

load_dotenv()

# Set up intents for bot.
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot("", intents=intents)

# Clients
redis_client = Redis(host="redis", port=6379, decode_responses=True)
openai_client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))


def bot_run(): # FIXME: refactor.
    """
    Main bot process. Refactor later..
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

        # if channel_id != "974065195565609040":
        #     continue

        message_ids = channel_message_ids(
            redis_client,
            channel_id,
            hours=MESSAGE_HISTORY_CUTOFF_HOURS)

        messages = get_messages(redis_client, message_ids)

        if len(list(filter(lambda x:x["read_at"] == "", messages))) < 1:
            continue

        max_tokens = MAX_INPUT_TOKENS - (
            num_tokens_from_string(instruction)+num_tokens_from_string(persona))

        messages = trim_message_history(messages, max_tokens=max_tokens)

        # Tack on image attachments and links
        for message in messages:
            message["images"] = []

            if message["attachment_count"] != "0":
                for attachment_id in redis_client.lrange(f"message:{message['id']}:attachments", 0, -1):
                    attachment = redis_client.hgetall(f"attachment:{attachment_id}")
                    if is_image(attachment["url"]):
                        message["images"].append(attachment["url"])

            if message["link_count"] != "0":
                for link_id in redis_client.lrange(f"message:{message['id']}:links", 0, -1):
                    link = redis_client.hgetall(f"link:{link_id}")
                    if is_image(link["url"]):
                        message["images"].append(link["url"])

        chance, target_message_id, img_url = response_chance(redis_client, messages)

        print(chance, target_message_id)

        key_message = get_messages(redis_client, [target_message_id])[0]

        print(key_message)

        roll = random.randrange(100)

        if chance < roll:
            # Mark rejected messages as read.
            mark_as_read(redis_client, messages)
            continue

        completetion = None

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
            print(error) # log

        if completetion:
            content = completetion.choices[0].message.content.strip()

            if was_refused(content):
                content = random.choice(["¯\\_(ツ)_/¯", "(╯°□°)╯︵ ┻━┻", "(ง'̀-'́)ง", "ಠ_ಠ"])

            completion_id = completetion.id.replace("chatcmpl-", "")

            redis_client.hset("message:"+target_message_id, "response_id", completion_id)

            key_message = get_messages(redis_client, [target_message_id])[0]

            k = f"{key_message['server_id']}.{key_message['channel_id']}-{completion_id}"

            redis_client.zadd("responses",{k: datetime.now().timestamp()})

            redis_client.hset(
                "response:"+completion_id,
                mapping={
                    "message": content,
                    "message_id": target_message_id,
                    "channel_id": key_message["channel_id"],
                    "channel_name": key_message["channel_name"],
                    "server_id": key_message["server_id"],
                    "server_name": key_message["server_name"],
                    "sent_at": "",
                    "timestamp":datetime.now().timestamp()
                },
            )

while True:
    bot_run()
