"""Bot runner.

In this file: configure dependencies, load middleware, run the bot.
"""

import os

from redis import Redis
from dotenv import load_dotenv

from pbot.bot import PBot
from pbot.constants import BOT_NAME
from pbot.logger import get_logger
from pbot.middleware.reload_prompt import ReloadPrompt
from pbot.middleware.trim_messages_by_token import TrimMessagesByTokens
from pbot.middleware.simple_openai import SimpleOpenAiResponseMiddleware


# Configure environment.
# ------------------------------------------------------------------------------

# Load required environment variables.
load_dotenv()
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
# OpenAI Middleware
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Get bespoke logger for service.
logger = get_logger()

# Set up Redis Client.
redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Create bot.
bot = PBot(redis, logger)


# Load bot middleware. (Order matters!)
# ------------------------------------------------------------------------------

# Reload prompt every time.
bot.add_middleware(ReloadPrompt(redis, "prompt.txt"))

# Remove message history over limit.
bot.add_middleware(TrimMessagesByTokens(redis))



# Example AI middleware.
# bot.add_middleware(SimpleOpenAiResponseMiddleware(redis, OPENAI_KEY, logger))


# Run the bot.
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    logger.debug(f"Starting {BOT_NAME}.")
    bot.run()
