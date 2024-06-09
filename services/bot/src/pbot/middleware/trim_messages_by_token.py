from redis import Redis

from pbot.middleware.base import Middleware
from pbot.utils import count_tokens
from pbot.constants import OPENAI_MAX_TOKENS
from pbot.constants import REDIS_PROMPT_KEY, BOT_NAME

class TrimMessagesByTokens(Middleware):
    """Taking into account prompt, removes message history that would exceed
    token limit.
    """

    def __init__(self, redis: Redis, prompt_key: str=REDIS_PROMPT_KEY, max_tokens: int=int(OPENAI_MAX_TOKENS/2)) -> None:
        """Constructor

        Args:
            redis (Redis): Redis connection.
            prompt_key (str): Redis prompt key.
            max_tokens (int): Token limit to cull message history by.
        """
        self.prompt_key = prompt_key
        self.max_tokens = max_tokens
        self.redis = redis

    def __trim_message_history(self, messages: list[dict], token_limit: int) -> list[dict]:
        """Removes older messages that would exceed token length.

        Args:
            messages (list): A list of messages.
            token_limit (int): Limit to curtail history by.

        Returns:
            list: A list of messages.
        """
        messages.sort(key=lambda x: float(x["time"]), reverse=True) # descending
        token_count = 0
        cutoff_index = None

        # FIXME: this will explode if the newest message exceeds max_tokens!
        for i, msg in enumerate(messages):
            # Handle exceeding length limit.
            if token_count + count_tokens(msg["content"]) > token_limit:
                cutoff_index = i
                break
            else:
                # Handle acceptable message length.
                token_count += count_tokens(msg["content"])

        # Trim history as needed.
        if cutoff_index:
            return messages[0:cutoff_index]

        return messages

    def handle_messages(self, messages: list[dict]) -> list[dict]:
        """Trims message history that would exceed token limit.

        Args:
            messages (list): A list of messages.

        Returns:
            list: A list of messages.
        """
        prompt = self.redis.get(self.prompt_key)
        if not prompt:
            raise Exception(f"Prompt not found by key: {self.prompt_key}")

        prompt = prompt.replace("{bot_name}", BOT_NAME)

        token_length = self.max_tokens - count_tokens(prompt)
        curtailed_history = self.__trim_message_history(messages, token_length)

        return curtailed_history
