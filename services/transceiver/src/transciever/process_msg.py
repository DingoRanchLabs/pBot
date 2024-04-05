"""
    Shared message processing between transciever and history fetching.
"""

from datetime import datetime
from urllib.parse import urlparse
import random
from redis.commands.json.path import Path


# Params -----------------------------------------------------------------------

REDIS_MESSAGE_EXPIRE_SECONDS = 60*60*24*7*5 # 5 weeks?
REDIS_MESSAGE_KEY_PREFIX = "message"
REDIS_MESSAGES_KEY = "messages"
REDIS_USERS_KEY = "users"
REDIS_USER_KEY_PREFIX = "user"
REDIS_SERVERS_KEY = "servers"
REDIS_SERVER_KEY_PREFIX = "server"
REDIS_CHANNELS_KEY = "channels"
REDIS_CHANNEL_KEY_PREFIX = "channel"

# --------------------------------------------------------------------- / Params

# Redis Templates
# FIXME: move these elsewhere.

server_template = {
    "id": None,
    "name": None,
    # FIXME: check for values in settings?
    "_parse_messages":   1, # parse messages?
    "_allow_generation": 1, # generate responses?
    "_send_responses":   1  # send responses?
}

channel_template = {
    "id": None,
    "name": None,
    "server_id": None,
    # FIXME: check for values in settings?
    "_parse_messages":   1, # parse messages?
    "_allow_generation": 1, # generate responses?
    "_send_responses":   1  # send responses?
}

user_template = {
    "id": None,
    "name": None,
    "color": None,
    # Assume users as good.
    "_parse_messages":   1, # parse messages?
    # FIXME: check for values in settings?
    "_allow_generation": 1, # generate responses?
    "_send_responses":   1  # send responses?
}

message_template = {
        "id": None,
        "time": None,
        "content": None,
        "read": None,
        "response": None,
        "origin": {
            "server": {
                "id": None,
                "name": None,
                "channel": {
                    "id": None,
                    "name": None,
                }
            }
        },
        "user": {
            "id": None,
            "bot": 0,
            "name": None,
            "nick": None,
            "avatar": None,
        },
        "objects": {
            "links": [],
            "attachments": []
        }
}

attachment_template = {
    "id": None,
    "url": None,
    "filename": None
}

def random_color():
    """
    Used to assign a color to new Discord users.
    Returns: A random hex color value.
    """

    # FIXME: pick from a color pallette to avoid 5 shades of the same color.
    r = lambda: random.randint(0,255)
    return ('#%02X%02X%02X' % (r(),r(),r()))

def urls_from_string(string):
    """
    Finds all valid URLS in a string.
    Returns: A list of URLs.
    """

    urls = []
    for word in string.split():
        url = urlparse(word)
        if url.scheme and url.netloc:
            urls.append(word)
    return urls

def process_msg(redis_client, message, read=""):
    """
    Captures message objects in Redis.
    """

    message_id = str(message.id)
    msg_created_timestamp = message.created_at.timestamp()

    # Don't process existing messages. This can occur when pulling historic messages.
    if redis_client.exists(f"{REDIS_MESSAGE_KEY_PREFIX}:{message_id}"):
        return

    # Handle author. -----------------------------------------------------------
    author_id = str(message.author.id)

    if not redis_client.exists(f"{REDIS_USER_KEY_PREFIX}:{author_id}"):
        redis_client.sadd(REDIS_USERS_KEY, author_id)

        # Copy & mod user template
        user_temp = user_template.copy()

        user_temp["id"] = author_id
        user_temp["name"] = message.author.name
        user_temp["color"] = random_color()

        redis_client.hset(f"{REDIS_USER_KEY_PREFIX}:{author_id}", mapping=user_temp)

    # Handle server. -----------------------------------------------------------
    server_id = str(message.guild.id)

    if not redis_client.exists(f"{REDIS_SERVER_KEY_PREFIX}:{server_id}"):
        redis_client.sadd(REDIS_SERVERS_KEY, server_id)

        # Copy & mod server template
        server_temp = server_template.copy()
        server_temp["id"] = server_id
        server_temp["name"] = message.guild.name

        redis_client.hset(f"{REDIS_SERVER_KEY_PREFIX}:{server_id}", mapping=server_temp)

    # Relations
    redis_client.sadd(f"{REDIS_SERVER_KEY_PREFIX}:{server_id}:{REDIS_USERS_KEY}", author_id)
    redis_client.sadd(f"{REDIS_USER_KEY_PREFIX}:{author_id}:{REDIS_SERVERS_KEY}", server_id)

    # Handle channel. ----------------------------------------------------------
    channel_id = str(message.channel.id)

    if not redis_client.exists(f"{REDIS_CHANNEL_KEY_PREFIX}:{channel_id}"):
        redis_client.sadd(f"{REDIS_SERVER_KEY_PREFIX}:{server_id}:{REDIS_CHANNELS_KEY}", channel_id)
        redis_client.sadd(REDIS_CHANNELS_KEY, channel_id)

        # Copy & mod channel template
        channel_temp = channel_template.copy()
        channel_temp["id"] = channel_id
        channel_temp["name"] = message.channel.name
        channel_temp["server_id"] = server_id

        redis_client.hset(f"{REDIS_CHANNEL_KEY_PREFIX}:{channel_id}", mapping=channel_temp)

    # Relations
    redis_client.sadd(f"{REDIS_CHANNEL_KEY_PREFIX}:{channel_id}:{REDIS_USERS_KEY}", author_id)
    redis_client.sadd(f"{REDIS_USERS_KEY}:{author_id}:{REDIS_CHANNELS_KEY}", channel_id)

    # Handle message. ----------------------------------------------------------

    redis_client.zadd(REDIS_MESSAGES_KEY, {f"{server_id}.{channel_id}-{message_id}": msg_created_timestamp})

    # Handle occasional/changing server-based nick
    nick_name = ""
    if hasattr(message.author, "nick") and message.author.nick:
        nick_name = message.author.nick

    # Handle changing avatar
    avatar = ""
    if hasattr(message.author, "display_avatar") and message.author.display_avatar:
        avatar = message.author.display_avatar

    # Relations
    redis_client.zadd(f"{REDIS_USER_KEY_PREFIX}:{author_id}:{REDIS_MESSAGES_KEY}", {message_id: msg_created_timestamp})
    redis_client.zadd(f"{REDIS_CHANNEL_KEY_PREFIX}:{channel_id}:{REDIS_MESSAGES_KEY}", {message_id: msg_created_timestamp})
    redis_client.zadd(f"{REDIS_SERVER_KEY_PREFIX}:{server_id}:{REDIS_MESSAGES_KEY}", {message_id: msg_created_timestamp})

    # Copy & mod message template
    msg_temp = message_template.copy()
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
        attachment_temp = attachment_template.copy()
        attachment_temp["id"] = attachment.id
        attachment_temp["url"] = attachment.url
        attachment_temp["filename"] = attachment.filename

        msg_temp["objects"]["attachments"].append(attachment_temp)

    # Handle any links.
    for url in urls_from_string(message.clean_content):
        msg_temp["objects"]["links"].append(url)

    # Store & expire.
    key = f"{REDIS_MESSAGE_KEY_PREFIX}:{message_id}"
    redis_client.json().set(key, Path.root_path(), msg_temp)
    redis_client.expire(key, REDIS_MESSAGE_EXPIRE_SECONDS)
