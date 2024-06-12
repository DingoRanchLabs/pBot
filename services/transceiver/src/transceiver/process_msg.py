"""Converts a Discord message to our internal models and writes them to Redis.

TODO: Refactor into models.
"""

from urllib.parse import urlparse
from datetime import datetime

import redis
from redis.commands.json.path import Path
import discord

from transceiver.models import Server, Channel, User, Message, Attachment
from transceiver.constants import REDIS_MESSAGE_EXPIRE_SECONDS
from transceiver.constants import REDIS_KEY_MESSAGE_PREFIX
from transceiver.constants import REDIS_KEY_MESSAGES
from transceiver.constants import REDIS_KEY_USERS
from transceiver.constants import REDIS_KEY_USER_PREFIX
from transceiver.constants import REDIS_KEY_SERVERS
from transceiver.constants import REDIS_KEY_SERVER_PREFIX
from transceiver.constants import REDIS_KEY_CHANNELS
from transceiver.constants import REDIS_KEY_CHANNEL_PREFIX


def urls_from_string(string: str) -> list[str]:
    """Returns a list of substrings found to be URLs.

    Args:
        string (str): Input string.

    Returns:
        list[str]: A list of found URLs.
    """
    urls = []

    for word in string.split():
        url = urlparse(word)
        if url.scheme and url.netloc:
            urls.append(word)

    return urls

def process_msg(redis_client: redis.Redis, message: discord.Message) -> None:
    """Persists a Discord Message to our own models in Redis.

    Args:
        redis_client (redis.Redis):
        message (discord.Message):
    """

    message_id = str(message.id)
    msg_created_timestamp = message.created_at.timestamp()

    # Don't process existing messages. This can occur when pulling historic messages.
    if redis_client.exists(f"{REDIS_KEY_MESSAGE_PREFIX}:{message_id}"):
        return

    # Handle author. -----------------------------------------------------------
    author_id = str(message.author.id)

    if not redis_client.exists(f"{REDIS_KEY_USER_PREFIX}:{author_id}"):
        user_temp = User().mapping()
        user_temp["id"] = author_id
        user_temp["name"] = message.author.name
        redis_client.hset(f"{REDIS_KEY_USER_PREFIX}:{author_id}", mapping=user_temp)

        redis_client.sadd(REDIS_KEY_USERS, author_id)

    # Handle server. -----------------------------------------------------------
    server_id = str(message.guild.id)

    if not redis_client.exists(f"{REDIS_KEY_SERVER_PREFIX}:{server_id}"):
        server_temp = Server().mapping()
        server_temp["id"] = server_id
        server_temp["name"] = message.guild.name
        redis_client.hset(f"{REDIS_KEY_SERVER_PREFIX}:{server_id}", mapping=server_temp)

        redis_client.sadd(REDIS_KEY_SERVERS, server_id)

    # Relations
    redis_client.sadd(f"{REDIS_KEY_SERVER_PREFIX}:{server_id}:{REDIS_KEY_USERS}", author_id)
    redis_client.sadd(f"{REDIS_KEY_USER_PREFIX}:{author_id}:{REDIS_KEY_SERVERS}", server_id)

    # Handle channel. ----------------------------------------------------------
    channel_id = str(message.channel.id)

    if not redis_client.exists(f"{REDIS_KEY_CHANNEL_PREFIX}:{channel_id}"):
        channel_temp = Channel().mapping()
        channel_temp["id"] = channel_id
        channel_temp["name"] = message.channel.name
        channel_temp["server_id"] = server_id
        redis_client.hset(f"{REDIS_KEY_CHANNEL_PREFIX}:{channel_id}", mapping=channel_temp)

        redis_client.sadd(f"{REDIS_KEY_SERVER_PREFIX}:{server_id}:{REDIS_KEY_CHANNELS}", channel_id)
        redis_client.sadd(REDIS_KEY_CHANNELS, channel_id)

    # Relations
    redis_client.sadd(f"{REDIS_KEY_CHANNEL_PREFIX}:{channel_id}:{REDIS_KEY_USERS}", author_id)
    redis_client.sadd(f"{REDIS_KEY_USERS}:{author_id}:{REDIS_KEY_CHANNELS}", channel_id)

    # Handle message. ----------------------------------------------------------

    redis_client.zadd(REDIS_KEY_MESSAGES, {f"{server_id}.{channel_id}-{message_id}": msg_created_timestamp})

    # Handle occasional/changing server-based nick
    nick_name = ""
    if hasattr(message.author, "nick") and message.author.nick:
        nick_name = message.author.nick

    # Handle changing avatar
    avatar = ""
    if hasattr(message.author, "display_avatar") and message.author.display_avatar:
        avatar = message.author.display_avatar

    # Relations
    redis_client.zadd(f"{REDIS_KEY_USER_PREFIX}:{author_id}:{REDIS_KEY_MESSAGES}", {message_id: msg_created_timestamp})
    redis_client.zadd(f"{REDIS_KEY_CHANNEL_PREFIX}:{channel_id}:{REDIS_KEY_MESSAGES}", {message_id: msg_created_timestamp})
    redis_client.zadd(f"{REDIS_KEY_SERVER_PREFIX}:{server_id}:{REDIS_KEY_MESSAGES}", {message_id: msg_created_timestamp})

    # Copy & mod message template
    msg_temp = Message().mapping()
    msg_temp["id"] = message_id
    msg_temp["time"] = message.created_at.timestamp()
    msg_temp["content"] = message.clean_content
    msg_temp["origin"]["server"]["id"] = server_id
    msg_temp["origin"]["server"]["name"] = message.guild.name
    msg_temp["origin"]["server"]["channel"]["id"] = channel_id
    msg_temp["origin"]["server"]["channel"]["name"] = message.channel.name
    msg_temp["user"]["id"] = author_id
    msg_temp["user"]["bot"] = int(message.author.bot)
    msg_temp["user"]["name"] = message.author.name
    msg_temp["user"]["nick"] = nick_name
    msg_temp["user"]["avatar"] = str(avatar)

    # Handle any attachments.
    for attachment in message.attachments:
        attachment_temp = Attachment().mapping()
        attachment_temp["id"] = attachment.id
        attachment_temp["url"] = attachment.url
        attachment_temp["filename"] = attachment.filename

        msg_temp["objects"]["attachments"].append(attachment_temp)

    # Handle any links.
    for url in urls_from_string(message.clean_content):
        msg_temp["objects"]["links"].append(url)

    # Store & expire.
    key = f"{REDIS_KEY_MESSAGE_PREFIX}:{message_id}"
    redis_client.json().set(key, Path.root_path(), msg_temp)
    redis_client.expire(key, REDIS_MESSAGE_EXPIRE_SECONDS)
