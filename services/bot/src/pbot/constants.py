"""Shared constants.
"""

BOT_NAME = "PBot"
""" Name the bot should respond to and identify as. """

# Redis keys
# ------------------------------------------------------------------------------
REDIS_PROMPT_KEY = "prompt"
REDIS_CHANNEL_KEY_PREFIX = "channel"
REDIS_MESSAGE_KEY_PREFIX = "message"
REDIS_MESSAGES_KEY = "messages"
REDIS_RESPONSE_KEY_PREFIX = "response"
REDIS_RESPONSES_KEY = "responses"

# OpenAI-Related
# ------------------------------------------------------------------------------
OPENAI_MAX_TOKENS = 4097
""" OpenAI max tokens. This is model dependant. """

OPENAI_MODEL = "gpt-3.5-turbo"
""" OpenAI model to use. """

OPENAI_TEMP = 1 # 0-2
""" Default model 'temperature' to use. """

DEFAULT_TOKEN_ENCODING = "cl100k_base"
""" How to count tokens. """
