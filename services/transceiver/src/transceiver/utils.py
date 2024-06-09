"""Utilities for transceiver.

Needs refactoring!
"""
from datetime import datetime
from urllib.parse import urlparse

import redis
import discord

from transceiver.process_msg import process_msg
from transceiver.logger import logger
from transceiver.constants import (
	REDIS_KEY_RESPONSES,
    REDIS_KEY_RESPONSE_PREFIX,
    DISCORD_CHARACTER_LIMIT,
    RESPONSE_DELVE_TIME
)

def intents() -> discord.Intents:
	"""Returns a configured Intents object for a Discord a client.

    By default, a bot does not have access to messages or their contents.
    Instead, permission has to be explicitly given to the bot for access to
    that information.
    See docs: https://discordpy.readthedocs.io/en/stable/intents.html

    Returns:
        discord.Intents: A Discord intents object for client.
	"""
	intents = discord.Intents.default()
	intents.messages = True
	intents.message_content = True

	return intents

async def send_message(message: discord.Message, content: str) -> None:
    """Asynchronously sends response to a specific Discord message.

    Args:
        message (discord.Message): The message to respond to.
        content (str): String to respond with.
    """
    try:
        await message.reply(content)
    except Exception as error: # FIXME: too permissive--don't try forever
        logger.error(error)

async def handle_response(discord_client: discord.Client, response: dict[str, any]) -> None:
    """Asynchronously handles sending single/multi-part messages to Discord
    for a given response.

    Args:
        response (dict[str, id]): A response.
    """
    # Dig up Discord message to respond to via API calls.
    channel = discord_client.get_channel(int(response["channel"]))
    message = channel.get_partial_message(int(response["message"]))

    # Handle multi-part responses due to length.
    if len(response["content"]) > DISCORD_CHARACTER_LIMIT:
        chunks = chunk_str(response["content"], DISCORD_CHARACTER_LIMIT)

        for chunk in chunks:
            # Await each message so the response messages are in order.
            await send_message(message, chunk)

    else:
       send_message(message, response["content"])

    # Mark response as sent.
    redis.hset(f"{REDIS_KEY_RESPONSE_PREFIX}:{response['id']}", "sent", datetime.now().timestamp())

def handle_message(redis_conn: redis.Redis, message: discord.Message) -> None:
    """Handle an incoming Discord message.

    Args:
        redis (redis.Redis): Redis connection.
        message (discord.Message): Discord message to handle.
    """
    logger.debug(format_message_for_log(message))
    process_msg(redis_conn, message)

def get_unsent_responses(redis_conn: redis.Redis) -> list[dict]:
    """Returns a list of unsent responses.

    Args:
		redis_conn (redis.Redis): Redis connection.

	Returns:
		list[dict]: A list of unsent responses.
    """
    cutoff = (datetime.now() - RESPONSE_DELVE_TIME).timestamp()

    # Get recent responses.
    responses = redis_conn.zrangebyscore(REDIS_KEY_RESPONSES, cutoff, '+inf', withscores=False)

    unsent = []

    for mixed_key in responses: # response:<server_id>.<channel_id>.<user_id>-<response_id>

        # Remove prefix
        mixed_key = mixed_key.replace(f"{REDIS_KEY_RESPONSE_PREFIX}:", "") # <server_id>.<channel_id>.<user_id>-<response_id>

        # Unpack ids from mixed key.
        server_channel_user, resp_id = mixed_key.split("-") # "<server_id>.<channel_id>.<user_id>", "<response_id>"
        server_id, channel_id, user_id = server_channel_user.split(".") # ""<server_id>", "<channel_id>", "<user_id>"

        # Pull related objects.
        # TODO: Handle missing...
        response = redis_conn.hgetall(f"{REDIS_KEY_RESPONSE_PREFIX}:{resp_id}")
        server = redis_conn.hgetall(f"server:{server_id}")
        channel = redis_conn.hgetall(f"channel:{channel_id}")
        user = redis_conn.hgetall(f"user:{user_id}")

        # Handle an unsent response.
        if response and response["sent"] == "":

            # Ensure Server, Channel, and User are allowed responses.
            if all([
                int(server["_send_responses"]) == 1,
                int(channel["_send_responses"]) == 1,
                int(user["_send_responses"]) == 1
            ]): # FIXME: handle ignored responses clogging queue.
                unsent.append(response)

    return unsent

def format_message_for_log(message: discord.Message) -> str:
    """Returns a string representation of a Discord message for logging.

    Args:
        message (discord.Message): Message to format.

    Returns:
        str: A messages formatted for log.
    """
    # Log statement template.
    log_str = "{created}|{msg_id}|{server}.{channel}|{author}({nick}):{content}"

    # Populate template.
    log_str = log_str.replace("{created}", message.created_at)
    log_str = log_str.replace("{msg_id}", message.id)
    log_str = log_str.replace("{server}", message.guild.name)
    log_str = log_str.replace("{channel}", message.channel.name)
    log_str = log_str.replace("{author}", message.author.name)
    log_str = log_str.replace("{nick}", message.author.nick)
    log_str = log_str.replace("{content}", message.content)

    return log_str

def chunk_str(blurb: str, size: int) -> list[str]:
    """Breaks string up (on whitespace) by chunk size.

    Args:
		blurb (str): String to chunk.
        size (int): Character length to chunk by.

    Returns:
		list[str]: A list of strings
    """
    if len(blurb) > size:
        all_chunks = []
        current_line = ""
        words = blurb.split(" ")

        for word in words:
            # If str wouldn't exceed chunk size:
            if (len(current_line) + len(word) + 1) < size:
                # If its the initial, empty line.
                if current_line == "":
                    current_line = str(word)
                # Otherwise append + space.
                else:
                    current_line += " "+str(word)
            # Otherwise, start a new chunk
            else:
                all_chunks.append(current_line)
                current_line = str(word)

        # Append last chunk segment.
        all_chunks.append(current_line)

        return all_chunks

    return [blurb]
