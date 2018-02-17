Instances
~~~~~~~~~

Default instance to be used when no ``steem_instance`` is given to
the Objects!

.. code-block:: python

   from steempy.instance import shared_steem_instance

   account = Account("test")
   # is equivalent with 
   account = Account("test", steem_instance=shared_steem_instance())

.. automethod:: steempy.instance.shared_steem_instance
.. automethod:: steempy.instance.set_shared_steem_instance
