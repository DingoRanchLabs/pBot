import sys
import random
from logging import Logger

from openai import OpenAI
from openai.types import Completion
from redis import Redis

from pbot.middleware.base import Middleware
from pbot.utils import count_tokens
from pbot.utils import create_response
from pbot.utils import is_refusal
from pbot.constants import BOT_NAME
from pbot.constants import OPENAI_MAX_TOKENS
from pbot.constants import OPENAI_MODEL
from pbot.constants import OPENAI_TEMP
from pbot.constants import REDIS_PROMPT_KEY


# TODO: handle rate limit
# TODO: handle usage limit
class SimpleOpenAiResponseMiddleware(Middleware):
    """ """
    TOKEN_SLOP = 10

    def __init__(self, redis: Redis, api_key: str, logger: Logger, prompt_key: str=REDIS_PROMPT_KEY) -> None:
        """Constructor for middleware.

        Args:
            redis (Redis): Redis connection.
            api_key (str): OpenAI API key.
            logger (Logger): logger instance.
            prompt_key (string): Redis key used prompt.
        """
        self.openai_client = OpenAI(api_key=api_key)
        self.prompt_key = prompt_key
        self.redis = redis
        self.logger = logger

    def response_chance(self, messages: list[dict]) -> tuple:
        """Determines the chance bot will generate a response for a given
        message history and provides the key message ID the AI should address.

        Thoughts: Unless specifically called out, bot should "decide" if a
        conversation is worth its time.

        Args:
            messages (list): A list of messages.

        Returns:
            tuple: A tuple (%chance, key_message_id).
        """
        rtn_val = (0, None)

        # Bounce on no messages.
        if len(messages) == 0:
            return rtn_val

        # Sort earliest messages first.
        messages.sort(key=lambda x: float(x["time"]), reverse=False) # Ascending.

        # Evaluate messages.
        for message in messages:

            # Handle earliest, direct callouts to the bot above all else.
            conditions = [
                BOT_NAME.lower() in message["content"].lower(),
                int(message["user"]["bot"]) == 0, # Ignore bots.
                not message["read"], # Ignore already read messages.
                not message["response"] # Ignore already responded to messages.
            ]
            if all(conditions):
                return (sys.maxsize, message["id"])

            # TODO: Conditionally handle messages that aren't direct calls.
            """
            # Handle anything else that might be interesting.
            conditions = [
                int(message["user"]["bot"]) == 1, # Don't respond to bots.
                message["content"] == "", # Don't respond to empty messages.
                message["read"] != "" # Don't respond to already reviewed and ignored messages.
            ]
            if any(conditions):
                continue
            else:
                pass # TODO: decide if a message is worth responding to and return thr tuple.
            """

        return rtn_val

    def generate_completion(self, messages: list[dict], target_message_id: str, prompt: str) -> Completion:
        """Formats message history & prompt and submits it to OpenAI's API.

        Args:
            messages (list): A list of messages.
            target_message_id (str): Id of message to respond to.
            prompt (str): Prompt for AI.

        Returns:
            Completion: An OpenAI text completion object.
            https://platform.openai.com/docs/guides/text-generation/completions-api
        """
        # Get message being responded to.
        key_message = list(filter(lambda x: x["id"] == target_message_id, messages))[0]

        # Sort messages by newest.
        messages.sort(key=lambda x: float(x["time"]), reverse=False) # ascending

        # Combine message history into a single string chat log.
        message_history_as_str = ""
        for message in messages:
            username = message["user"]["name"]
            # Use arbitrary nick name if present.
            if message["user"]["nick"] != "":
                username = message["user"]["nick"]
            message_history_as_str += f"{username}:{message['content']}\n"

        # Build prompt around message history.
        prompt = prompt.replace('{chat_history}', message_history_as_str)
        prompt = prompt.replace('{target_message}', key_message["content"])
        prompt = prompt.replace('{bot_name}', BOT_NAME)

        scene = []
        scene.append({"role": "system", "content": prompt})

        token_count = count_tokens(prompt)
        token_count += count_tokens('role')
        token_count += count_tokens('system')
        token_count += count_tokens('content')

        max_tokens = (OPENAI_MAX_TOKENS - (token_count + self.TOKEN_SLOP))

        try:
            chat_completion = self.openai_client.chat.completions.create(
                messages=scene,
                max_tokens=max_tokens,
                model=OPENAI_MODEL,
                temperature=OPENAI_TEMP,
                n=1,
                user=key_message["user"]["name"],
            )
            self.logger.debug(chat_completion)
            return chat_completion

        except Exception as error:
            self.logger.error(error)

        return None

    def generate_response(self, messages: list[dict], target_id: str, prompt: str) -> None:
        """Generate an AI response for a message history and store it.

        Args:
            messages (list): A list of messages.
            target_id (str): Message ID to be focus of completion.
            prompt (str): A prompt for the AI.
        """
        completetion = None

        try:
            completetion = self.generate_completion(messages, target_id, prompt)
            self.logger.debug(completetion)

        except Exception as error:
            self.logger.error(error)

        if completetion:
            # Extract first (guaranteed) response.
            content = completetion.choices[0].message.content.strip()

            # Replace response w/nonsense if it was a refusal of some kind.
            if is_refusal(content):
                content = random.choice(["¯\\_(ツ)_/¯", "(╯°□°)╯︵ ┻━┻", "(ง'̀-'́)ง", "ಠ_ಠ"])

            completion_id = completetion.id.replace("chatcmpl-", "")

            create_response(self.redis, completion_id, content, target_id)

    def handle_messages(self, messages: list[dict]) -> list[dict]:
        """Process message history. Conditionally generate AI responses.

        Args:
            messages (list): A list of messages.

        Returns:
            A list of messages up to and including target message. Any
            subsequent messages will have been trimmed off the list.
        """
        # Should, and to which message, should the bot respond?
        chance, target_message_id = self.response_chance(messages)

        if target_message_id:

            # Remove any message history *newer* than the message to be responded
            # to. Further messages should be handled in a subsequent pass.
            messages.sort(key=lambda x: float(x["time"]), reverse=False) # Ascending.
            target_index = None
            for idx, message in enumerate(messages):
                if message["id"] == target_message_id:
                    target_index = idx
                    break
            messages = messages[0:target_index+1]

            # Roll to respond (direct calls to bot always exceed 100)...
            if chance > random.randrange(100):

                # Get current prompt.
                prompt = self.redis.get(self.prompt_key)
                if not prompt:
                    raise Exception("Prompt not found by key.")

                self.generate_response(messages, target_message_id, prompt)

        return messages
