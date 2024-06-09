"""Transceiver runner.

Stores incoming messages & sends responses.
"""

import os

from dotenv import load_dotenv
from redis import Redis
import discord
from discord.ext import tasks

from transceiver.logger import logger
from transceiver.constants import TRANSCEIVER_RESPONSE_DELAY
from transceiver.utils import (
	intents,
    handle_message,
    get_unsent_responses,
    handle_response
)


# Configure environment.
# ------------------------------------------------------------------------------

# Load required environment variables.
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')

# Set up clients.
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
discord_client = discord.Client(intents=intents())


# Recurring tasks.
# See: https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html
# ------------------------------------------------------------------------------

@tasks.loop(seconds=float(TRANSCEIVER_RESPONSE_DELAY))
async def send_responses() -> None:
    """Asynchronously send any waiting responses in Redis.
    """
    for unsent_response in get_unsent_responses():
        handle_response(discord_client, unsent_response)


# Handle Discord events.
# See: https://discordpy.readthedocs.io/en/stable/api.html#event-reference
# ------------------------------------------------------------------------------

@discord_client.event
async def on_ready() -> None:
    """Execute code on client ready.
    """
    logger.debug("Discord client logged in.")

    # Start up any recurring tasks.
    send_responses.start()

@discord_client.event
async def on_message(message: discord.Message) -> None:
    """Handle an incoming message from Discord.

    Args:
        message (discord.Message): A Discord message.
    """
    handle_message(redis_client, message)

# Run the client.
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    discord_client.run(DISCORD_TOKEN)
