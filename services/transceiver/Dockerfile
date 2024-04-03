# Transciever Dockerfile

FROM python:3.12

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /src

# Install dependencies
COPY ./src/requirements.txt .
RUN pip3 install -r requirements.txt

# Copy project
COPY ./src .

CMD python3 app.py
