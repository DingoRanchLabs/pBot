Models
######

.. automodule:: pbot.models
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

--------------------------------------------------------------------------------

==========
The prompt
==========

The prompt is little more than a text file that is read into a single Redis key.

This file is completely free-form but serves as a template that can be
decorated with ad hoc symbols to support logic or formatting in your
middleware. For example, the SimpleOpenAiResponseMiddleware uses the
symbols ``{chat_history}`` and ``{target_message}`` to conduct substring
replacement.

prompt.txt
----------

.. include:: ../../services/bot/src/prompt.txt
   :literal:
