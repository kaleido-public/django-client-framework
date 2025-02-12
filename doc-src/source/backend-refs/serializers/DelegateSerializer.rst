.. _DelegateSerializer:

`class` DelegateSerializer `extends DCFSerializer`
=========================================================

.. code-block:: py

    from django_client_framework.serializers import DelegateSerializer


This class allows for multiple serializers to be used on one model class. The
class conforms to the Serializer interface, therefore, it can be returned from
the `Serializable.get_serializer_class(...)`_ method.  You can dispatch the request to
one of the serializers.

**Inheritance**

You must override all these methods:

* `DelegateSerializer.get_create_delegate_class(...)`_,
* `DelegateSerializer.get_update_delegate_class(...)`_,
* `DelegateSerializer.get_read_delegate_class(...)`_.



.. _DelegateSerializer.get_read_delegate_class(...):

`method` .get_read_delegate_class `(self, instance) -> Serializer`
-----------------------------------------------------------------------------------------------------------

    instance
        The model instance to be serialized. This is the ``instance`` parameter
        passed to the constructor.

    Override this method to return a `DCFSerializer`_ class that's only used for
    model deserialization. This is the case when the `DelegateSerializer`_ is
    initialized with only the ``instance`` parameter.

    .. code-block:: py

        product = Product.objects.first()
        delegated = DelegateSerializer(instance=product)
        delegated.data # deserialization


.. _DelegateSerializer.get_create_delegate_class(...):

`method` .get_create_delegate_class `(self, initial_data, prevalidated_data) -> Serializer`
---------------------------------------------------------------------------------------------------------

    initial_data
        The data to be deserialized. This is the ``data`` parameter passed to
        the constructor.

    Override this method to return a `DCFSerializer`_ class that's only used for
    model instance creation. This is the case when the `DelegateSerializer`_ is
    initialized with only the ``data`` parameter.

    .. code-block:: py

        delegated = DelegateSerializer(data={"barcode": "xxyy"})
        product = delegated.save() # serialization


.. _DelegateSerializer.get_update_delegate_class(...):

`method` .get_update_delegate_class `(self, instance, initial_data, prevalidated_data) -> Serializer, bool`
--------------------------------------------------------------------------------------------------------------

    instance
        The model instance to be serialized. This is the ``instance`` parameter
        passed to the constructor.

    initial_data
        The data to be deserialized. This is the ``data`` parameter passed to
        the constructor.

    Override this method to return a `DCFSerializer`_ class that's only used for
    partial updating an model instance. This is the case when the
    `DelegateSerializer`_ is initialized with both the ``data`` and the
    ``instance`` parameter.

    .. code-block:: py

        product = Product.objects.first()
        delegated = DelegateSerializer(instance=product, data={"barcode": "xxyy"})
        delegated.save() # updates barcode


