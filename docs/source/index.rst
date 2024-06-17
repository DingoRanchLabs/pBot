Welcome to PBot's documentation!
################################

=============
What is PBot?
=============

PBot is a minimal, dockerized framework for building chatbots on top of Discord.

It's meant to serve as a base for your own business logic, abstracting away
everything that isn't the fun parts of building a chatbot. Pbot revolves around
the idea of `middleware <overview.html#chatbot-middleware>`_. You can write a
middleware layer to do anything. Just `drop your code in place and run the bot <get_started.html>`_.

==============================
Who is this project meant for?
==============================

Anyone who wants to get a `private <privacy.html>`_ bot up and running quickly.

PBot optimizes for ease of use and experimentation. You can run it anywhere
you can run Docker and only requires a little Python knowledge to modify. Run a
fleet of them on a spare Raspberry Pi?

==========================
Is/Was this related to AI?
==========================

PBot's original intent was to incite automated, amusing chaos in my friend's
Discord servers. Earlier incarnations relied on OpenAI's Chat GPT to provide
scathing insults in response to their conversations.

Today, PBot includes optional middleware for integrating with Chat GPT. Use,
extend, or disregard this middleware. Midjourney image middleware is also
currently being ported over to this updated version of the project.



--------------------------------------------------------------------------------

.. toctree::
   :maxdepth: 2

   overview
   get_started
   api
   privacy
   download

.. |ROBOTFACE|   unicode:: U+1F916 .. ROBOTFACE
.. |CHATBUBBLES|   unicode:: U+1F4AC .. CHATBUBBLES
