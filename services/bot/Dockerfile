FROM python:3.12

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /src

# Install dependencies
COPY services/bot/src/requirements.txt .
RUN pip3 install -r requirements.txt

# Copy persona prompt
# COPY config/persona-prompt.txt .

# Copy project
COPY services/bot/src .

# FIXME: call app instead of just run forever..
CMD tail -f /dev/null
