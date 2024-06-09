PBot APIs
#########

PBot's APIs are broken up by service. These services rely on shared models in
Redis.


.. note:: **Regarding the recent Redis license rug-pull:** While the Redis license change doesn't directly impact PBot's use of Redis the project will be investigating true open source forks of Redis going forward. Any changes that would break backwards compatibility would be pushed to a major version update.

--------------------------------------------------------------------------------

====================
Bot Service
====================

.. toctree::
   :maxdepth: 2

   api_bot

===========================
Transceiver Service
===========================

.. toctree::
   :maxdepth: 2

   api_transceiver

====================
Shared Configuration
====================

.. toctree::
   :maxdepth: 2

   shared_conf

=================
Development Tasks
=================

.. toctree::
   :maxdepth: 2

   api_devtasks
