from logging import Logger
from typing import NoReturn

from redis import Redis

from pbot.middleware.base import Middleware
from pbot.utils import active_channels
from pbot.utils import get_messages
from pbot.utils import channel_message_ids
from pbot.utils import mark_as_read
from pbot.constants import REDIS_CHANNEL_KEY_PREFIX


class PBot:
    """Persona Bot.

    PBot is a lightweight handler that is merely meant to pass message history
    to a stack of middleware layers, where the real work is done.


    """

    middlewares = []
    """A list of middleware to pass message history through."""

    active_channel_cutoff_hours = 2
    """How far back to look for channel activity."""

    message_history_cutoff_hours = 8
    """ How far back to include message history from. """

    def __init__(self, redis: Redis, logger: Logger) -> None:
        """Constructor

        Args:
            redis (Redis): Redis connection.
            logger (Logger): Logger.
        """
        self.redis = redis
        self.logger = logger

    def add_middleware(self, middleware: Middleware) -> None:
        """Add middleware to bot.

        Load a single middleware layer into the bot. The load order of
        middleware likely matters!

        Args:
            middleware (Middleware): Middleware to load.
        """
        self.middlewares.append(middleware)

    def handle_messages(self, messages: list[dict]) -> None:
        """Pushes a message history through middleware.

        In turn, hands message history to each layer of middleware loaded.
        Keep in mind, middleware is allowed to mutate the message history!

        Args:
            messages (list): a list of messages.
        """
        message_buffer = messages
        for middleware in self.middlewares:
            message_buffer = middleware.handle_messages(message_buffer)

    def run(self) -> NoReturn:
        """Execute the bot.

        Endlessly loops, looking for recently active channels. Pulls message
        history for each and sends history through middleware layers.
        """
        while True:
            for channel_id in active_channels(self.redis, hours=self.active_channel_cutoff_hours):

                # Skip ignored channels.
                channel = self.redis.hgetall(f"{REDIS_CHANNEL_KEY_PREFIX}:{channel_id}")
                if int(channel["parse"]) != 1:
                    continue

                # Fetch message history.
                message_ids = channel_message_ids(self.redis, channel_id, hours=self.message_history_cutoff_hours)
                messages = get_messages(self.redis, message_ids)

                # Skip channel if all the messages are already read.
                if len(list(filter(lambda x:x["read"] == None, messages))) < 1:
                    continue

                # Push messages through middleware.
                self.handle_messages(messages)

                # Clean up and mark processed messages as read.
                self.logger.debug(f"Cleaning up {len(messages)} messages.")
                mark_as_read(self.redis, messages)
