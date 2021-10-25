.. _Serializable:

`class` Serializable `extends AbstractDCFModel`
======================================================

.. code-block:: py

    from django_client_framework.models import Serializable

This abstract model class provides caches for serialization.

.. note::

    Any :ref:`Model` to be registered as an API must inherit this class.


**Inheritance**

Subclasses of `Serializable`_ must override `Serializable.get_serializer_class(...)`_ which
returns a `DCFSerializer`_ class.


.. _Serializable.get_serializer_class(...):

`classmethod` .get_serializer_class `(cls, version, context)`
-----------------------------------------------------------------

    `required`

    Override this method to return the `DCFSerializer`_ class for the model.


.. _Serializable.serializer:

`method` .get_serializer `(self, version, context)`
------------------------------------------------------
    An instance of the `DCFSerializer`_ class returned by
    `Serializable.get_serializer_class(...)`_.


.. _Serializable.get_serialization_cache_timeout():

`classmethod` .get_serialization_cache_timeout `(cls)`
---------------------------------------------------------------
    Override this method to change how long to cache the serialized data in
    seconds. Setting to ``0`` disables the cache.

    Default: ``0``
