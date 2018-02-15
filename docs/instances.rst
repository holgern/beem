Instances
~~~~~~~~~

Default instance to be used when no ``steem_instance`` is given to
the Objects!

.. code-block:: python

   from steem.instance import shared_steem_instance

   account = Account("xeroc")
   # is equivalent with 
   account = Account("xeroc", steem_instance=shared_steem_instance())

.. automethod:: steem.instance.shared_steem_instance
.. automethod:: steem.instance.set_shared_steem_instance
