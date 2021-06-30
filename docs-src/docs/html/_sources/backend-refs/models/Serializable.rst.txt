.. _Serializable:

`class` Serializable
==========================

.. code-block:: py

    from django_client_framework.models import Serializable

This abstract model class provides caches for serialization.

.. note::

    Any :ref:`Model` to be registered as an API must inherit this class.


**Inheritance**

Subclasses of `Serializable`_ must override `Serializable.serializer_class()`_ which
returns a `Serializer`_ class.


.. _Serializable.serializer_class():

`classmethod` .serializer_class `(cls)`
-----------------------------------------------------------

    `required`

    Override this method to return the `Serializer`_ class for the model.


.. _Serializable.serializer:

`property` .serializer
------------------------------
    An instance of the `Serializer`_ class returned by
    `Serializable.serializer_class()`_.


.. _Serializable.get_serialization_cache_timeout():

`classmethod` .get_serialization_cache_timeout `(cls)`
---------------------------------------------------------------
    Override this method to change how long to cache the serialized
    data in seconds.
