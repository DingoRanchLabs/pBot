"""
Bot admin
"""
from datetime import datetime, timedelta
#
from flask import Flask, render_template, request, redirect, url_for
from redis import Redis

app = Flask(
    __name__,
    template_folder="admin/templates",
    static_folder="admin/templates/static")

@app.template_filter()
def format_history_window_querystring(message):
    """
    tbd
    """
    time_padding = timedelta(minutes=20)
    message_datetime = datetime.fromtimestamp(float(message["timestamp"]))

    start = (message_datetime - time_padding)
    stop  = (message_datetime + time_padding)

    return f"?start={start.isoformat().split('.')[0]}&stop={stop.isoformat().split('.')[0]}&highlight={message['id']}#{message['id']}"


@app.template_filter()
def format_num_to_answer(value, as_bools=False):
    """
    tbd
    """

    if as_bools:
        zero = "False"
        one  = "True"
    else:
        zero = "No"
        one  = "Yes"

    try:
        if int(value) == 0:
            return zero
        else:
            return one
    except Exception as err:
        pass

    return

@app.template_filter()
def format_timestamp(value):
    """
    tbd
    """
    return datetime.fromtimestamp(float(value)).strftime("%b %a %-d, %-H:%M")

@app.template_filter()
def format_message_author_name(message):
    """
    tbd
    """
    if message["user_nick"]:
        return message["user_nick"]

    return message["user_name"]

redis_client = Redis(host="redis", port=6379, decode_responses=True)






# ------------------------------------------------------------------------------

def get_messages(key, start="-inf", stop="+inf", highlight=[], users=True, attachments=True, links=True, reverse=True):

    messages = []
    users = {}

    for message_id in redis_client.zrangebyscore(key, start, stop):
        message = redis_client.hgetall("message:"+message_id)

        # Highlights
        message["highlight"] = False
        if message_id in highlight:
             message["highlight"] = True

        # Users
        if users:
            user_id = message["user_id"]
            # Store user for subsequent use.
            if not user_id in users.keys():
                users[user_id] = redis_client.hgetall(f"user:{user_id}")
            message["user"] = users[user_id]

        if attachments:
            if message["attachment_count"] != "0":
                message["attachments"] = []
                for attachment_id in redis_client.smembers(f"message:{message['id']}:attachments"):
                     message["attachments"].append(redis_client.hgetall(f"attachment:{attachment_id}"))

        if links:
            if message["link_count"] != "0":
                message["links"] = []
                for link_id in redis_client.smembers(f"message:{message['id']}:links"):
                    message["links"].append(redis_client.hgetall(f"link:{link_id}"))





        messages.append(message)

    messages.sort(key=lambda x: x["timestamp"], reverse=reverse)

    return messages



# ------------------------------------------------------------------------------



@app.route('/user/<user_id>/messages')
def user_messages(user_id):
    """ User messages. """

    # Handle default date range and any querystring supplied dates.
    args = request.args

    start = (datetime.now() - timedelta(hours=24*7))
    if args.get('start'):
        start = datetime.fromisoformat(args.get('start'))

    stop = datetime.now()
    if args.get('stop'):
        stop = datetime.fromisoformat(args.get('stop'))

    highlight = []
    if args.get('highlight'):
        highlight += args.get('highlight').split(",")

    target_user = redis_client.hgetall("user:"+user_id)




    messages = get_messages(f"user:{user_id}:messages", start=start.timestamp(), stop=stop.timestamp(), users=False, highlight=highlight)

    # messages = []
    # for message_id in redis_client.zrangebyscore(f"user:{user_id}:messages", start.timestamp(), stop.timestamp()):
    #     message = redis_client.hgetall("message:"+message_id)

    #     message["highlight"] = False
    #     if message_id in highlight:
    #          message["highlight"] = True

    #     messages.append(message)

    # messages.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template('user_messages.html', user=target_user, messages=messages, start=start.isoformat().split(".")[0], stop=stop.isoformat().split(".")[0])



@app.route('/user/<user_id>/settings')
def user_settings(user_id):
    """ User settings. """

    target_user = redis_client.hgetall("user:"+user_id)

    return render_template('user_settings.html', user=target_user)

@app.route('/user/<user_id>')
def user(user_id):
    """
    tbd
    """
    target_user = redis_client.hgetall("user:"+user_id)

    history_cutoff = (datetime.now() - timedelta(hours=24*7))
    messages = []
    for message_id in redis_client.zrangebyscore(
            "user:"+user_id+":messages",
            history_cutoff.timestamp(), '+inf'):

        message = redis_client.hgetall("message:"+message_id)

        if message["attachment_count"] != "0":
            message["attachments"] = []
            for attachment_id in redis_client.smembers(f"message:{message_id}:attachments"):
                attachment = redis_client.hgetall(f"attachment:{attachment_id}")
                message["attachments"].append(attachment)

        if message["link_count"] != "0":
            message["links"] = []
            for link_id in redis_client.smembers(f"message:{message_id}:links"):
                link = redis_client.hgetall(f"link:{link_id}")
                message["links"].append(link)

        messages.append(message)

    messages.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template('user.html', user=target_user, messages=messages)

# Channel routes ---------------------------------------------------------------

@app.route('/channel/<channel_id>/messages')
def channel_messages(channel_id):
    """ Channel messages. """
    target_channel = redis_client.hgetall("channel:"+channel_id)
    server = redis_client.hgetall(f"server:{target_channel['server_id']}")

    # Handle default date range and any querystring supplied dates.
    args = request.args

    start = (datetime.now() - timedelta(hours=24*7))
    if args.get('start'):
        start = datetime.fromisoformat(args.get('start'))

    stop = datetime.now()
    if args.get('stop'):
        stop = datetime.fromisoformat(args.get('stop'))

    highlight = []
    if args.get('highlight'):
        highlight += args.get('highlight').split(",")

    messages = get_messages(f"channel:{channel_id}:messages", start=start.timestamp(), stop=stop.timestamp(), highlight=highlight)

    start_iso = start.isoformat().split(".")[0]
    stop_iso  = stop.isoformat().split(".")[0]

    return render_template('channel_messages.html', channel=target_channel, messages=messages, server=server, users=users, start=start_iso, stop=stop_iso)

@app.route('/channel/<channel_id>/users')
def channel_users(channel_id):
    """ Channel users. """
    target_channel = redis_client.hgetall("channel:"+channel_id)
    server = redis_client.hgetall(f"server:{target_channel['server_id']}")

    return render_template('channel_users.html', channel=target_channel, server=server)

@app.route('/channel/<channel_id>/settings')
def channel_settings(channel_id):
    """ Channel settings. """
    target_channel = redis_client.hgetall("channel:"+channel_id)

    server = redis_client.hgetall(f"server:{target_channel['server_id']}")

    return render_template('channel_settings.html', channel=target_channel, server=server)

@app.route('/channel/<channel_id>')
def channel(channel_id):
    """ A Discord channel. """
    target_channel = redis_client.hgetall("channel:"+channel_id)
    server = redis_client.hgetall(f"server:{target_channel['server_id']}")
    history_cutoff = (datetime.now() - timedelta(hours=48))
    messages = []
    for message_id in redis_client.zrangebyscore(
            "channel:"+channel_id+":messages",
            history_cutoff.timestamp(), '+inf'):
        messages.append(redis_client.hgetall("message:"+message_id))
    users = []
    for user_id in redis_client.smembers("channel:"+channel_id+":users"):
        users.append(redis_client.hgetall("user:"+user_id))

    return render_template('channel.html', channel=target_channel,messages=messages, users=users, server=server)

# Server routes ----------------------------------------------------------------

@app.route("/servers")
def servers():
    """ All Discord servers. """

    servers = []
    for server_id in redis_client.smembers("servers"):
        servers.append(redis_client.hgetall(f"server:{server_id}"))

    return render_template('servers.html', servers=servers)

@app.route('/server/<server_id>')
def server(server_id):
    """ A Discord server. """

    target_server = redis_client.hgetall("server:"+server_id)

    channels = []
    for channel_id in redis_client.smembers("server:"+server_id+":channels"):
        channels.append(redis_client.hgetall("channel:"+channel_id))
    channels.sort(key=lambda x:x["name"] )

    server_users = []
    for user_id in redis_client.smembers("server:"+server_id+":users"):
        server_users.append(redis_client.hgetall("user:"+user_id))
    server_users.sort(key=lambda x:x["name"] )

    return render_template(
        'server.html',
        channels=channels,
        server=target_server,
        users=server_users)

@app.route("/server/<server_id>/channels")
def server_channels(server_id):
    """ Server channels. """

    server = redis_client.hgetall("server:"+server_id)
    channels = []
    for channel_id in redis_client.smembers(f"server:{server_id}:channels"):
        channels.append(redis_client.hgetall(f"channel:{channel_id}"))

    return render_template('server_channels.html', channels=channels, server=server)

@app.route('/server/<server_id>/users')
def server_users(server_id):
    """ Server users. """

    target_server = redis_client.hgetall("server:"+server_id)
    users = []
    for user_id in redis_client.smembers(f"server:{server_id}:users"):
        users.append(redis_client.hgetall(f"user:{user_id}"))

    return render_template(
        'users.html',
        server=target_server, users=users)









@app.route('/server/<server_id>/settings', methods = ['POST', 'GET'])
def server_settings(server_id):
    """
    Server Settings.
    """

    if request.method == 'POST':

        server_id = request.form['server_id']
        parse_messages = request.form['parse_messages'] == "yes"
        allow_generation = request.form['allow_generation'] == "yes"
        send_responses = request.form['send_responses'] == "yes"

        server = redis_client.hgetall(f"server:{server_id}")

        print(server)

        server["_parse_messages"] = "1" if parse_messages else "0"
        server["_allow_generation"] = "1" if allow_generation else "0"
        server["_send_responses"] = "1" if send_responses else "0"


        redis_client.hset(f"server:{server_id}", mapping=server)
        return redirect(url_for("server_settings",server_id=server_id ))
    else:
        target_server = redis_client.hgetall("server:"+server_id)

        return render_template(
            'server_settings.html',
            server=target_server)

# Basic routes -----------------------------------------------------------------

@app.route("/settings")
def settings():
    """ Bot settings. """
    return render_template('settings.html')

@app.route("/sandbox")
def sandbox():
    """ Bot sandbox. """


    args = request.args
    messages = []

    if args.get('messages'):
        for message_id in args.get('messages').split(","):
            messages.append(redis_client.hgetall("message:"+message_id))

    messages.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template('sandbox.html', messages=messages)

@app.route("/users")
def users():
    """ All Discord users. """

    users = []
    for user_id in redis_client.smembers("users"):
        users.append(redis_client.hgetall(f"user:{user_id}"))

    return render_template('users.html', users=users)

@app.route("/docs")
def docs():
    """ Bot documentation. """

    return render_template('docs.html')

@app.route('/')
def index():
    """ Landing page. """

    # Get some metrics.
    channel_count = len(redis_client.smembers("channels"))
    server_count = len(redis_client.smembers("servers"))
    user_count = len(redis_client.smembers("users"))
    message_count = redis_client.zcount("messages", "-inf", "+inf")
    link_count = redis_client.zcount("links", "-inf", "+inf")
    attachment_count = redis_client.zcount("attachments", "-inf", "+inf")

    return render_template(
        'index.html',
        channel_count=channel_count,
        server_count=server_count,
        user_count=user_count,
        message_count=message_count,
        attachment_count=attachment_count,
        link_count=link_count
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7777, debug=True)
