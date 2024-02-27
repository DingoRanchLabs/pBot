"""
Shared processing between listener and history fetching.
"""
from datetime import datetime
from urllib.parse import urlparse
import random

def random_color():
    r = lambda: random.randint(0,255)
    return ('#%02X%02X%02X' % (r(),r(),r()))

def urls_from_string(string):
    urls = []

    for word in string.split():
        url = urlparse(word)
        if url.scheme and url.netloc:
            urls.append(word)

    return urls

def process_msg(redis_client, message, read_at=""):
    """
    tbd
    """
    message_id = str(message.id)

    print(message)

    now = datetime.now().timestamp()
    now = message.created_at.timestamp()

    # Don't process existing messages. This can occur when pulling historic messages.
    if redis_client.exists(f"message:{message_id}"):
        return

    # Handle author.
    author_id = str(message.author.id)

    if not redis_client.exists(f"user:{author_id}"):
        redis_client.sadd("users", author_id)
        redis_client.hset(f"user:{author_id}", mapping={
            "id": author_id,
            "name": message.author.name,
            "color": random_color()
        })

    # Handle server.
    server_id = str(message.guild.id)

    if redis_client.exists(f"server:{server_id}") == 0:
        redis_client.sadd("servers", server_id)
        redis_client.hset(f"server:{server_id}", mapping={
            "id": server_id,
            "name": message.guild.name
        })

    redis_client.sadd(f"server:{server_id}:users", author_id)
    redis_client.sadd(f"user:{author_id}:servers", server_id)

    # Handle channel.
    channel_id = str(message.channel.id)

    if not redis_client.exists(f"channel:{channel_id}"):
        redis_client.sadd(f"server:{server_id}:channels", channel_id)
        redis_client.sadd("channels", channel_id)
        redis_client.hset(f"channel:{channel_id}", mapping={
            "id": channel_id,
            "name": message.channel.name,
            "server_id": server_id
        })

    redis_client.sadd(f"channel:{channel_id}:users", author_id)
    redis_client.sadd(f"user:{author_id}:channels", channel_id)

    # Handle attachments.
    for attachment in message.attachments:
        attachment_id = str(attachment.id)

        if redis_client.exists(f"attachment:{attachment_id}"):
            continue

        redis_client.zadd("attachments", {attachment_id:now})
        redis_client.zadd(f"user:{author_id}:attachments", {attachment_id:now})
        redis_client.zadd(f"channel:{channel_id}:attachments", {attachment_id:now})
        redis_client.zadd(f"server:{server_id}:attachments", {attachment_id:now})
        redis_client.sadd(f"message:{message_id}:attachments", attachment_id)
        redis_client.hset(f"attachment:{attachment_id}", mapping={
            "id": attachment_id,
            "url": attachment.url,
            "filename": attachment.filename,
            "message_id": message_id,
            "timestamp": now
        })

    # Handle message
    redis_client.zadd(f"user:{author_id}:messages", {message_id:now})
    redis_client.zadd(f"channel:{channel_id}:messages", {message_id:now})
    redis_client.zadd(f"server:{server_id}:messages", {message_id:now})
    redis_client.zadd("messages", {f"{server_id}.{channel_id}-{message_id}":now}) #TODO: rename to msg_history because of inconsistent use of "messages" style key

    links = 0

    # Handle any links in message.
    for i, url in enumerate(urls_from_string(message.clean_content)):
        link_id = f"{message_id}.{i}"
        links += 1

        redis_client.zadd("links", {link_id:now})
        redis_client.zadd(f"user:{author_id}:links", {link_id:now})
        redis_client.zadd(f"channel:{channel_id}:links", {link_id:now})
        redis_client.zadd(f"server:{server_id}:links", {link_id:now})
        redis_client.sadd(f"message:{message_id}:links", link_id)
        redis_client.hset(f"link:{link_id}", mapping={
            "id": link_id,
            "url": url,
            "message_id": message_id,
            "timestamp": now
        })

    # Handle occasional/changing server-based nick
    nick_name = ""
    if hasattr(message.author, "nick") and message.author.nick:
        nick_name = message.author.nick

    # Handle changing avatar
    avatar = ""
    if hasattr(message.author, "display_avatar") and message.author.display_avatar:
        avatar = message.author.display_avatar

    redis_client.hset(f"message:{message_id}", mapping={
        "id": message_id,
        "bot": int(message.author.bot),
        "server_id": server_id,
        "server_name": message.guild.name,
        "channel_id": channel_id,
        "channel_name": message.channel.name,
        "user_id": author_id,
        "user_name": message.author.name,
        "user_nick": nick_name,
        "content": message.clean_content,
        "timestamp": message.created_at.timestamp(),
        "read_at": read_at,
        "response_id": "",
        "attachment_count": len(message.attachments),
        "link_count": links,
        "avatar": str(avatar)
    })

    # TODO: what about a combined model for development on top of?
