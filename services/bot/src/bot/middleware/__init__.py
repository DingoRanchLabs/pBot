import random
from abc import ABC, abstractmethod
from openai import OpenAI
from bot import (
	num_tokens_from_string,
    trim_message_history,
    response_chance,
    get_messages,
    mark_as_read,
    generate_response,
    create_response,
    was_refused)

from pprint import pprint

class Middleware(ABC):
    @abstractmethod
    def handle_messages(self, messages=[]):
        """
        This function should always accept and return a list.
        """
        return messages

class TrimMessagesByTokens(Middleware):

    OPENAI_MAX_TOKENS = 4000
    max_tokens = None
    prompt_key = None
    redis_client = None


    def __init__(self, redis_client, prompt_key="prompt", max_tokens=OPENAI_MAX_TOKENS/2):
        self.prompt_key = prompt_key
        self.max_tokens = max_tokens
        self.redis_client = redis_client

    def handle_messages(self, messages):
        prompt = self.redis_client.get(self.prompt_key)

        if not prompt: raise Exception("Prompt not found by key.")

        token_length = self.max_tokens - (num_tokens_from_string(prompt))

        history = trim_message_history(messages, max_tokens = token_length)

        return history

class SimpleOpenAiResponseMiddleware(Middleware):

    openai_client = None
    redis_client = None
    prompt_key = None


    def __init__(self, redis_client, api_key, prompt_key="prompt"):
        self.openai_client = OpenAI(api_key=api_key)
        self.redis_client = redis_client
        self.prompt_key = prompt_key

    def handle_messages(self, messages):
        prompt = self.redis_client.get(self.prompt_key)

        if not prompt: raise Exception("Prompt not found by key.")

        chance, target_message_id, img_url = response_chance(self.redis_client, messages)

        # FIXME: just pull it out of messages instead of repolling redis.
        key_message = get_messages(self.redis_client, [target_message_id])[0]

        roll = random.randrange(100)

        if chance < roll:
            return messages

        completetion= None

        try:
            completetion = generate_response(
                self.openai_client,
                messages,
                target_message_id,
                prompt)
            # FIXME: log


            # logger.debug(completetion)

        except Exception as error:  # FIXME: too permissive.
            print(error)
            # FIXME: log

        if completetion:
            content = completetion.choices[0].message.content.strip()

            if was_refused(content):
                content = random.choice(["¯\\_(ツ)_/¯", "(╯°□°)╯︵ ┻━┻", "(ง'̀-'́)ง", "ಠ_ಠ"])

            completion_id = completetion.id.replace("chatcmpl-", "")

            create_response(self.redis_client, completion_id, content, target_message_id)

        return messages
