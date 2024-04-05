"""
    Transciever runner.

    Stores incoming messages & sends responses.
"""

import os
from datetime import datetime, timedelta
from logger import logger
from redis import Redis
import discord
from dotenv import load_dotenv
from discord.ext import tasks
from transciever.process_msg import process_msg
from transciever import chunk_str


# Params -----------------------------------------------------------------------

REDIS_RESPONSES_KEY = "responses"
REDIS_RESPONSE_KEY_PREFIX = "response"
RESPONSE_DELVE_TIME = timedelta(hours=1)
RESPONSE_DELVE_CUTOFF = (datetime.now() - RESPONSE_DELVE_TIME).timestamp()
DISCORD_CHARACTER_LIMIT = 2000

# --------------------------------------------------------------------- / Params

# Set up intents for bot.
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Set up clients.
discord_client = discord.Client(intents=intents)
redis_client = Redis(host='redis', port=6379, decode_responses=True)

async def send_response(message, string):
    """
    Sends response to Discord message.
    """

    try:
        await message.reply(string)
    except Exception as error: # FIXME: too permissive--don't try forever
        logger.error(error)

@tasks.loop(seconds=2)
async def response_check():
    """
    Checks for and send any waiting responses.
    """

    # Get recent responses.
    responses = redis_client.zrangebyscore(REDIS_RESPONSES_KEY, RESPONSE_DELVE_CUTOFF, '+inf', withscores=True)

    # Handle any unsent.
    for k in responses: # response:server_id.channel_id.user_id-response_id

        # Break apart mixed key
        mixed_key = k[0].replace(f"{REDIS_RESPONSE_KEY_PREFIX}:", "")
        server_channel_user, resp_id = mixed_key.split("-")
        server_id, channel_id, user_id = server_channel_user.split(".")

        # Pull related objects
        response = redis_client.hgetall(f"{REDIS_RESPONSE_KEY_PREFIX}:{resp_id}")
        server = redis_client.hgetall(f"server:{server_id}")
        channel = redis_client.hgetall(f"channel:{channel_id}")
        user = redis_client.hgetall(f"user:{user_id}")

        # Ensure Server, Channel, and User are allowed responses.
        # FIXME: handle ignored responses clogging queue.
        if response and response["sent"] == "":
            if all([
                int(server["_send_responses"]) == 1,
                int(channel["_send_responses"]) == 1,
                int(user["_send_responses"]) == 1
            ]):

                channel = discord_client.get_channel(int(channel_id))
                message = channel.get_partial_message(int(response["message"]))

                # Check if response will exceed Discord character limit.
                if len(response["content"]) > DISCORD_CHARACTER_LIMIT:
                    chunks = chunk_str(response["content"], DISCORD_CHARACTER_LIMIT)
                    for chunk in chunks:
                        await send_response(message, chunk)
                else:
                    await send_response(message, response["content"])

                redis_client.hset(f"{REDIS_RESPONSE_KEY_PREFIX}:{resp_id}", "sent", datetime.now().timestamp())

# Events -----------------------------------------------------------------------

@discord_client.event
async def on_ready():
    """
    Start the response checking.
    """

    logger.debug("Logged in")
    response_check.start()

@discord_client.event
async def on_message(message):
    """
    Handle incoming message.
    """

    # Log message.
    log_str = f"{message.created_at}|{message.id}|"
    log_str += f"{message.guild.name}.{message.channel.name}|"
    log_str += f"{message.author.name}({message.author.nick}):"
    log_str += f"{message.content}"
    logger.debug(log_str)

    process_msg(redis_client, message)

# Exec -------------------------------------------------------------------------

load_dotenv()
discord_client.run(os.getenv('DISCORD_TOKEN'))
