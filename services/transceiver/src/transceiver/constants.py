import os
from datetime import datetime
from datetime import timedelta


"""
messages = []
servers
channels
users
responses = [{server_id}.{channel_id}.{user_id}-{resp_id}, timestamp]


response:{resp_id} = {
	"id": {resp_id}
	"user": None,
	"content": None,
	"message": None,
	"channel": None,
	"server": None,
	"sent": "",
	"time": None
}
"""

# Bot.
# ------------------------------------------------------------------------------

TRANSCEIVER_RESPONSE_DELAY = 2
""" Delay between polling for new responses. """

RESPONSE_DELVE_TIME = timedelta(hours=1)
""" How long ago to look for unsent responses. """

# Redis.
# ------------------------------------------------------------------------------

REDIS_MESSAGE_EXPIRE_SECONDS = 60*60*24*3
""" How long to persist Discord messages. """

# Keys.

REDIS_KEY_MESSAGES = "messages"
""" Key for messages by timestamp """

REDIS_KEY_SERVERS = "servers"
""" Key for server ids. """

REDIS_KEY_CHANNELS = "channels"
""" Key for channel ids. """

REDIS_KEY_USERS = "users"
""" Key for user ids. """

REDIS_KEY_RESPONSES = "responses"
""" Key for responses by timestamp. """

#-

REDIS_KEY_MESSAGE_PREFIX = "message"
""" Key prefix for a message. """

REDIS_KEY_SERVER_PREFIX = "server"
""" Key prefix for a server. """

REDIS_KEY_CHANNEL_PREFIX = "channel"
""" Key prefix for a channel. """

REDIS_KEY_USER_PREFIX = "user"
""" Key prefix for a user. """

REDIS_KEY_RESPONSE_PREFIX = "response"
""" Key prefix for a response. """












# Other.
# ------------------------------------------------------------------------------

DISCORD_CHARACTER_LIMIT = 2000
""" Discord message length limit. """
