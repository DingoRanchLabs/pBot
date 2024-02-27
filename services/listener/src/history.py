"""
History fetch
"""
import os
from datetime import datetime
#
from redis import Redis
import discord
from dotenv import load_dotenv
#
from logger import logger
from listen.process_msg import process_msg


# Set up intents for bot.
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Set up clients.
discord_client = discord.Client(intents=intents)
redis_client = Redis(host='redis', port=6379)

# Events -----------------------------------------------------------------------

@discord_client.event
async def on_ready():
    """
    tbd
    """
    for guild in discord_client.guilds:
        for c in guild.channels:
            chan = discord_client.get_channel(c.id)
            if chan.__class__.__name__ == "TextChannel":

                print(guild.name+"_"+chan.name)

                valid_results = True
                last_msg_id = chan.last_message_id

                print(last_msg_id)

                pages = 0
                while valid_results:
                    pages += 1

                    if pages > 20: break # FIXME: remove this

                    last_msg = await chan.fetch_message(last_msg_id)

                    messages = [message async for message in chan.history(
                        limit=100, before=last_msg)]

                    if len(messages) == 0:
                        valid_results = False
                        break

                    last_msg_id = messages[-1].id
                    for message in messages:

                        process_msg(redis_client, message, message.created_at.timestamp())

    raise Exception("halt") # FIXME:



load_dotenv()
discord_client.run(os.getenv('DISCORD_TOKEN'))
