from redis import Redis

from pbot.middleware.base import Middleware
from pbot.constants import REDIS_PROMPT_KEY, BOT_NAME

class ReloadPrompt(Middleware):
    """Reloads prompt into Redis from a text file on message handling.

    Useful for quickly editing and updating prompt template.
    """

    def __init__(self, redis: Redis, file_path: str, prompt_key: str=REDIS_PROMPT_KEY) -> None:
        """Constructor

        Args:
            redis (Redis): Redis connection.
            file_path (str): Path to prompt text file.
            prompt_key (str): Redis prompt key.
        """
        self.redis = redis
        self.path = file_path
        self.prompt_key = prompt_key

    def __reload_prompt_from_file(self) -> None:
        """Simply reads file contents into Redis prompt key."""
        try:
            with open(self.path, "r") as f:
                self.redis.set(self.prompt_key, f.read())
        except Exception as error:
            raise error

    def handle_messages(self, messages: list[dict]) -> list[dict]:
        """Reloads prompt and passes back messages.

        Does not alter message history.

        Args:
            messages (list): A list of messages.

        Returns:
            list: A list of messages.
        """
        self.__reload_prompt_from_file()
        return messages
