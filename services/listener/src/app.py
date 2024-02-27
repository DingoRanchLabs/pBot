"""
Listener runner.
"""
import os
from datetime import datetime, timedelta
#
from redis import Redis
import discord
from dotenv import load_dotenv
from discord.ext import tasks
import pysnooper
#
from logger import logger
from listen.process_msg import process_msg
from pprint import pprint

# Set up intents for bot.
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Set up clients.
discord_client = discord.Client(intents=intents)
redis_client = Redis(host='redis', port=6379, decode_responses=True)

def chunk_str(blurb, size):
    """Breaks string up (on whitespace) by chunk size."""
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

@tasks.loop(seconds=2)
async def response_check():
    """
    tbd
    """
    # Get recent responses.
    response_delve_time = timedelta(hours=1)
    timestamp = (datetime.now() - response_delve_time).timestamp()
    responses = redis_client.zrangebyscore("responses", timestamp, '+inf', withscores=True)

    # Handle any unsent.
    for k in responses:
        mixed_key = k[0].replace("resp:","")
        server_channel_ids, resp_id = mixed_key.split("-")
        _, channle_id = server_channel_ids.split(".")

        response = redis_client.hgetall("response:"+resp_id)

        if response and response["sent_at"] == "":
            channel = discord_client.get_channel(int(channle_id))
            msg = channel.get_partial_message(int(response["message_id"]))

            if len(response["message"]) > 2000:
                chunks = chunk_str(response["message"], 2000)
                try:
                    for chunk in chunks:
                        await msg.reply(chunk)
                    redis_client.hset("response:"+resp_id, "sent_at", datetime.now().timestamp())
                except Exception as error: # FIXME: too permissive.
                    print(error)
                    logger.error(error)
            else:
                try:
                    m = response["message"]

                    await msg.reply(m)

                    redis_client.hset("response:"+resp_id, "sent_at", datetime.now().timestamp())
                except Exception as error: # FIXME: too permissive.
                    print(error)
                    logger.error(error)

# Events -----------------------------------------------------------------------

@discord_client.event
async def on_ready():
    """
    tbd
    """
    login_msg = "Logged in"
    logger.debug(login_msg)
    response_check.start()

@discord_client.event
async def on_message(message):
    """
    tbd
    """

    log_str = f"{message.created_at}|{message.id}|"
    log_str += f"{message.guild.name}.{message.channel.name}|"
    log_str += f"{message.author.name}({message.author.nick}):"
    log_str += f"{message.content}"
    logger.debug(log_str)

    process_msg(redis_client, message)

# Exec -------------------------------------------------------------------------

load_dotenv()
discord_client.run(os.getenv('DISCORD_TOKEN'))
