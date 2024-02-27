import pytest
import os
from dotenv import load_dotenv
from redis import Redis
from datetime import datetime, timedelta
from bot import (
	active_channels,
	channel_message_ids,
	get_messages,
	was_refused,
	response_chance,
	trim_message_history,
	num_tokens_from_string,
	mark_as_read,
	get_message_objects
)

# SETUP ------------------------------------------------------------------------

load_dotenv()

redis_client = Redis(
	host=os.environ.get("TEST_REDIS_HOST"),
	port=os.environ.get("TEST_REDIS_PORT"),
	decode_responses=True)

redis_client.ping() # Raises an exception if no connection.

attachments = [
	{
		"id": "82704893274892379847",
		"url": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Piwarski_Para_pijak%C3%B3w.jpg",
		"filename": "Para pijakow.jpg",
		"message_id": "82734893274892379847",
		"timestamp": datetime.now().timestamp()+0
	}
]

links = [
	{
	"id": "82539893274892379807.0",
	"url": "https://upload.wikimedia.org/wikipedia/commons/3/38/%C3%89douard_Manet_-_Le_Suicid%C3%A9_%28ca._1877%29.jpg",
	"message_id": "82539893274892379807",
	"timestamp": datetime.now().timestamp()+2
}]

msgs = [
	{
		"id": "82734893274892379847",
		"server_id": "1",
		"channel_id": "34",
		"read_at": "",
		"timestamp": datetime.now().timestamp()+0,
		"content": "I love that someone was just \"What if John Wick did a bunch of weird shit in a Dominos\"",
		"bot": "0",
		"response_id": "",
		"link_count": "0",
		"attachment_count": "1"
	},
	{
		"id": "82739893274892379847",
		"server_id": "2",
		"channel_id": "99",
		"read_at": "",
		"timestamp": datetime.now().timestamp()+1,
		"content": "pbot who is the best space marine?",
		"bot": "0",
		"response_id": "",
		"link_count": "0",
		"attachment_count": "0"
	},
	{
		"id": "82539893274892379807",
		"server_id": "2",
		"channel_id": "99",
		"read_at": "",
		"timestamp": datetime.now().timestamp()+2,
		"content": "country is just farm emo",
		"bot": "0",
		"response_id": "",
		"link_count": "1",
		"attachment_count": "0"
	},
	{
		"id": "82739893274892379847",
		"server_id": "1",
		"channel_id": "34",
		"read_at": "",
		"timestamp": datetime.now().timestamp()+3,
		"content": "i'm old gregg",
		"bot": "0",
		"response_id": "",
		"link_count": "0",
		"attachment_count": "0"
	}
]

@pytest.fixture
def messages_01():
	r_keys = ["messages"]

	messages = msgs.copy()

	# Load in test data
	for a in attachments:
		now = datetime.now().timestamp()
		attachment_key = f"attachment:{a['id']}"
		r_keys.append(attachment_key)
		redis_client.hset(attachment_key, mapping=a)

		redis_client.lpush(f"message:{a['message_id']}:attachments", a["id"])
		r_keys.append(f"message:{a['message_id']}:attachments")

	# Load in test data
	for l in links:
		now = datetime.now().timestamp()
		link_key = f"link:{l['id']}"
		r_keys.append(link_key)
		redis_client.hset(link_key, mapping=l)

		redis_client.lpush(f"message:{l['message_id']}:links", l["id"])
		r_keys.append(f"message:{l['message_id']}:links")

	# Load in test data
	for m in messages:
		now = datetime.now().timestamp()

		# channel:<id>:messages = [1205727867585957948:1707538324.973]
		channel_messages_key = "channel:"+m["channel_id"]+":messages"
		r_keys.append(channel_messages_key)
		redis_client.zadd(channel_messages_key, {m["id"]:now})

		# messages = [649086180922490880.649086180922490884-1205727867585957948:1707538324.973]
		redis_client.zadd(r_keys[0], {"{}.{}-{}".format(m["server_id"], m["channel_id"], m["id"]):now})

		# message:1205727867585957948 = {...}
		redis_client.hset("message:"+m["id"], mapping=m)

	yield

	# Remove test data.
	for k in r_keys:
		redis_client.delete(k)

# TESTS ------------------------------------------------------------------------

def test_active_channels(messages_01):
	messages = msgs.copy()

	channels = active_channels(redis_client) # Redis call
	assert len(channels) == 2
	for message in messages:
		assert message["channel_id"] in channels

def test_channel_message_ids(messages_01):
	channel_ids = active_channels(redis_client) # Redis call
	for channel_id in channel_ids:
		recent_messages = channel_message_ids(redis_client, channel_id) # Redis call
		assert len(recent_messages) == 2

def test_get_messages(messages_01):
	messages = msgs.copy()

	message_ids = list(map(lambda x: x["id"], messages))
	m = get_messages(redis_client, message_ids) # Redis call
	assert len(m) == 4

def test_was_completion_refused():
	for response_string in [
        "Sorry, but I can't",
        "I'm sorry, but",
        "I cannot comply",
        "As an AI developed by OpenAI",
        "As a large language model",
        "as a llm",
        "As an AI language model"
	]:
		assert was_refused(response_string) == True

def test_trim_message_history():
	messages = msgs.copy()

	max_tokens=num_tokens_from_string(messages[3]["content"]+messages[2]["content"]+messages[1]["content"])
	trimmed_messages = trim_message_history(messages.copy(), max_tokens=max_tokens)
	assert len(trimmed_messages) == 3
	assert messages[0]["id"] not in list(map(lambda x:x["id"] ,trimmed_messages))

def test_response_chance():
	messages = msgs.copy()

	chance, key_id, img_url = response_chance(redis_client, [])
	assert chance == 0
	assert key_id == None

	# Ensure direct reference always succeeds a roll and is the key message.
	chance, key_id, img_url = response_chance(redis_client ,list(filter(lambda x:x["channel_id"] == "99", messages)))
	assert chance > 100
	assert key_id == "82739893274892379847"

def test_mark_as_read(messages_01):
	messages = msgs.copy()

	mark_as_read(redis_client, messages)

	for message in messages:
		value = redis_client.hget("message:"+message["id"], "read_at")
		assert value != ""

def test_get_message_objects(messages_01):
	message_data = msgs.copy()
	message_ids = list(map(lambda x: x["id"], message_data))
	messages = get_messages(redis_client, message_ids) # Redis call
	get_message_objects(redis_client, messages) # Redis call. # Modifies argument.

	target_msg = list(filter(lambda x:x["id"] == "82734893274892379847", messages))[0]
	assert len(target_msg["images"]) == 1

	target_msg = list(filter(lambda x:x["id"] == "82539893274892379807", messages))[0]
	assert len(target_msg["images"]) == 1
