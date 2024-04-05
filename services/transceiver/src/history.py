"""
    Fetches Discord message history.
"""

import os
from datetime import datetime
from logger import logger
from redis import Redis
import discord
from dotenv import load_dotenv
from transciever.process_msg import process_msg


# Params -----------------------------------------------------------------------

HISTORY_MESSAGES_PER_PAGE = 100
HISTORY_MAX_PAGES = 5

# --------------------------------------------------------------------- / Params

# Set up Discord "intents" for bot.
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Set up clients.
discord_client = discord.Client(intents=intents)
redis_client = Redis(host='redis', port=6379)

# Events -----------------------------------------------------------------------

# FIXME: this shouldn't be based on an event.
@discord_client.event
async def on_ready():
    for guild in discord_client.guilds:
        for c in guild.channels:
            channel = discord_client.get_channel(c.id)

            # Ignore non text channels.
            if not channel.__class__.__name__ == "TextChannel":
                continue

            print(f"Handling {guild.name}.{channel.name}")

            valid_results = True
            last_msg_id = channel.last_message_id
            pages = 0

            while valid_results:
                pages += 1

                if pages > HISTORY_MAX_PAGES:
                    break

                last_msg = await channel.fetch_message(last_msg_id)

                messages = [message async for message in channel.history(
                    limit=HISTORY_MESSAGES_PER_PAGE, before=last_msg)]

                if len(messages) == 0:
                    valid_results = False
                    break

                last_msg_id = messages[-1].id
                for message in messages:
                    process_msg(redis_client, message, message.created_at.timestamp())

    raise Exception("halt") # FIXME: this isn't the way to stop..


load_dotenv()
discord_client.run(os.getenv('DISCORD_TOKEN'))
