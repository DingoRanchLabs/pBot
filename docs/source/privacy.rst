A Note on Privacy
#################

--------------------------------------------------------------------------------

This project is based on Discord, a private 3rd party service.
You should have no expectation of true privacy.

Do not transmit sensitive information over Discord.

==========
Middleware
==========

Middleware you load into the bot *may* also have privacy concerns attached.
The AI chatbot middleware SimpleOpenAiResponseMiddleware for example,
is a direct integration with OpenAI's Chat GPT that sends channel chat snippets
to another private 3rd party.

=============================
Data Collection and Retention
=============================

Your instance of Pbot *can* store messages from any server it's invited to.
These messages are temporarily stored within a local Redis database.
By default, each stored chat message is automatically deleted shortly thereafter
based on an `expiration variable <api_transceiver.constants.html#transceiver.constants.REDIS_MESSAGE_EXPIRE_SECONDS>`_.

The PBot project has zero code for telemetry and no interest in your data.

============
Dependencies
============

Be advised, the project relies on Discord the service as well as the following open source software:

Bot service ``requirements.txt``

.. include:: ../../services/bot/src/requirements.txt
   :literal:

Transceiver service ``requirements.txt``

.. include:: ../../services/transceiver/src/requirements.txt
   :literal:
