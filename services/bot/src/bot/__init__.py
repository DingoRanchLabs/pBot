"""
Temp home for bot functions.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
#
from openai import OpenAI
import tiktoken



REDIS_MESSAGE_KEY_PREFIX = "message"

REDIS_CHANNEL_KEY_PREFIX = "channel"
REDIS_MESSAGES_KEY = "messages"


####

AFFINITY_WORDS = [] # FIXME:
PHOBIC_WORDS = [] # FIXME:
MAX_INPUT_TOKEN_LENGTH = 2000
MAX_TOTAL_TOKEN_LENGTH = 4097
TOKEN_SLOP = 10

def active_channels(redis_client, msg_key="messages", hours=1, minutes=0):
    """
    Returns a list of channel Ids with recent activity.
    """

    cutoff = (datetime.now() - timedelta(hours=hours, minutes=minutes)).timestamp()
    messages = redis_client.zrangebyscore(msg_key, cutoff, "+inf")
    messages.sort(key=lambda x: x[1], reverse=True) # descending
    channels = set()
    for activity in messages:
        _, channel_id = (activity.split("-")[0]).split(".")
        channels.add(channel_id)
    return list(channels)

def channel_message_ids(redis_client, channel_id, hours=1, minutes=0):
    """
    Returns a list of channel's message ids within time window.
    """

    msg_key = f"{REDIS_CHANNEL_KEY_PREFIX}:{channel_id}:{REDIS_MESSAGES_KEY}"
    cutoff = (datetime.now() - timedelta(hours=hours, minutes=minutes)).timestamp()
    message_ids = redis_client.zrangebyscore(msg_key, cutoff, "+inf")
    return message_ids

def get_messages(redis_client, message_ids):
    """
    Returns a list of messagess from a list of message ids.
    """

    messages = []
    for message_id in message_ids:
        message = redis_client.json().get(f"{REDIS_MESSAGE_KEY_PREFIX}:{message_id}")
        messages.append(message)
    return messages

def was_refused(resp):
    """
    Returns a bool on whether the response content string was a refusal.
    """

    problem_substrings = [
        "Sorry, but I can't",
        "I'm sorry, but",
        "I cannot comply",
        "As an AI developed by OpenAI",
        "As a large language model",
        "as a llm",
        "As an AI language model",
        "I apologize, but"
    ]

    for flag in problem_substrings:
        if flag.lower() in resp.lower():
            return True
    return False

def num_tokens_from_string(string, encoding_name="cl100k_base"):
    """
    Returns the number of tokens in a text string.
    """

    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def trim_message_history(messages, max_tokens=MAX_INPUT_TOKEN_LENGTH):
    """
    Remove messages older that would exceed token length.
    """

    token_count = 0
    messages.sort(key=lambda x: float(x["time"]), reverse=True) # descending
    cutoff_index = None

    # FIXME: this will explode if the newest message exceeds max_tokens!
    for i, msg in enumerate(messages):
        # Handle exceeding length limit.
        if token_count + num_tokens_from_string(msg["content"]) > max_tokens:
            cutoff_index = i
            break
        else:
            # Handle acceptable message length.
            token_count += num_tokens_from_string(msg["content"])

    # Trim history as needed.
    if cutoff_index:
        return messages[0:cutoff_index]

    return messages

def mark_as_read(redis_client, messages):
    """
    Set read_at attr for messages.
    """
    for message in messages:
        redis_client.json().set(f"message:{message['id']}", ".read", datetime.now().timestamp())

def is_image(url_path):
    discord_friendly_image_files = [
        ".jpg", ".jpeg", ".png", ".gif", ".gifv"
    ]

    path = Path(url_path.lower())

    if path.suffix in discord_friendly_image_files:
        return True

    return False

def response_chance(redis_client, messages): # FIXME: refator.
    """
    Determines the chance pbot will generate a response for message history and
    provides the key message ID pbot should address and an image url.

    Thoughts: Unless specifically called out, pbot should "decide" if a
    conversation is worth its time.

    Returns a tuple (%chance, key_message_id, image_url)
    """

    # FIXME: much of this should be refactored out into other fns

    # Bounce on no messages.
    if len(messages) == 0:
        return (0, None, None)

    # Message history totals.
    # TODO: Add in user-affinity and other modifiers.
    message_values = {}
    duration_in_m = 0
    total_affinity_word_count = 0
    total_phobic_word_count = 0
    users = set()
    includes_image = False

    messages.sort(key=lambda x: float(x["time"]), reverse=False)  # ascending

    assessed_messages = []

    for message in messages:
        assessed_messages.append(message)

        # Don't contribute bot comment to values
        if message["user"]["bot"] == "1":
            continue

        affinity_word_count = 0
        phobic_word_count = 0
        word_count = 0

        # image_files = []
        # if hasattr(message, "images"):
        #     image_files = message["images"]

        # file_reference = None
        # if len(image_files) > 0:
        #     file_reference = image_files[0] # FIXME:

        conditions = [
            "pbot" in message["content"].lower(),
            int(message["user"]["bot"]) == 0,
            not message["read"],
            not message["response"]
        ]

        # Always address earliest direct references to bot.
        if all(conditions):
            #mark_as_read(assessed_messages) #??????????
            return (sys.maxsize, message["id"], None) # FIXME: file_reference is none....

        # Initial message interest value.
        message_values[message["id"]] = 0

        word_count = len((message["content"].split(" ")))


        if int(message["user"]["bot"]) == 0:
            users.add(message["user"]["id"])


        # if len(image_files) > 0:
        #     includes_image = True

        for affinity_word in AFFINITY_WORDS:
            if affinity_word.lower() in message["content"].lower():
                affinity_word_count += 1
                total_affinity_word_count += 1

        for phobic_word in PHOBIC_WORDS:
            if phobic_word.lower() in message["content"].lower():
                phobic_word_count += 1
                total_phobic_word_count += 1

        conditions = [
            int(message["user"]["bot"]) == 1, # Don't respond to bots.
            message["content"] == "", # Don't respond to empty messages.
            message["read"] != "" # Don't respond to already reviewed and ignored messages.
        ]

        if any(conditions):
            message_values[message["id"]] = -97 # why -99
        else:
            message_values[message["id"]] += (
                affinity_word_count + (word_count * 0.15) - (phobic_word_count * 0.7)
            )

            # if includes_image:
            #     message_values[message["id"]] += 5 # arb value for img

    print("AAAAAA")

    # If there are no (real) users, bail.
    if (len(users)) == 0:
        return (-99, None, None) # why -99?

    print("BBBBB")


    # Determine conversation duration
    start = datetime.fromtimestamp(float(messages[0]["time"]))
    end = datetime.fromtimestamp(float(messages[-1]["time"]))
    duration_in_m = (end - start).total_seconds() / 60

    modifier = 0  # starting chance

    modifier += len(assessed_messages) * 0.012

    modifier += len(users) * 0.025

    #modifier += duration_in_m * 0.025 # maybe the opposite?

    modifier += total_affinity_word_count * 0.05

    modifier -= total_phobic_word_count * 0.1

    # if includes_image:
    #     modifier += 10 # doing this again?

    key_message_id = max(message_values, key=message_values.get)

    key_message = list(filter(lambda x:x["id"]==key_message_id, messages))[0]

    # get image if one
    image_ref = None
    if hasattr(key_message, "images"):
        if len(key_message["images"]) > 0:
            image_ref = key_message["images"][0]

    return (modifier, key_message_id, image_ref)

def generate_response(openai_client, messages, target_message_id, persona, instruction):
    """
    tbd
    """
    # TODO: add relationship history and user summaries in the mix.

    scene = []

    messages.sort(key=lambda x: float(x["time"]), reverse=False) # ascending

    message_history_as_str = ""

    for message in messages:
        username = message["user"]["name"]
        # Use server nick if present.
        if message["user"]["nick"] != "":
            username = message["user"]["nick"]

        message_history_as_str += f"{username}:{message['content']}\n"

    key_message = list(filter(lambda x: x["id"] == target_message_id, messages))[0]

    if hasattr(key_message, "images"):
        if len(key_message["images"]) > 0:
            raise Exception("dfdfd")

    instruction = instruction.replace("chat_history", message_history_as_str)
    instruction = instruction.replace("target_message", key_message["content"])

    prompt = instruction + persona

    token_count = num_tokens_from_string(prompt)

    scene.append({"role": "system", "content": prompt})

    token_count += num_tokens_from_string('role')
    token_count += num_tokens_from_string('system')
    token_count += num_tokens_from_string('content')

    try:
        chat_completion = openai_client.chat.completions.create(
            messages=scene,
            max_tokens=(MAX_TOTAL_TOKEN_LENGTH - (token_count + TOKEN_SLOP)),
            model="gpt-3.5-turbo",
            temperature=1,  # 0-2 # vary this by if being asked for real info or not
            n=1,
            user=key_message["user"]["name"],
        )

        return chat_completion
    except Exception as error: # FIXME: too permissive.
        print(error)
        return None

def get_message_objects(redis_client, messages):
    """
    returns messages with related objects bolted on.
    """
    for message in messages:

        # Attach image objects.
        message["images"] = []

        # Attachments take priority over any image links found in message.
        if message["attachment_count"] != "0":
            for attachment_id in redis_client.lrange(f"message:{message['id']}:attachments", 0, -1):
                attachment = redis_client.hgetall(f"attachment:{attachment_id}")
                if is_image(attachment["url"]):
                    message["images"].append(attachment["url"])

        if message["link_count"] != "0":

            for link_id in redis_client.lrange(f"message:{message['id']}:links", 0, -1):


                link = redis_client.hgetall(f"link:{link_id}")


                if is_image(link["url"]):
                    message["images"].append(link["url"])
