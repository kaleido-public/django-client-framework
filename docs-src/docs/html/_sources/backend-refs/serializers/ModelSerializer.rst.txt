.. _ModelSerializer:

`class` ModelSerializer `extends Serializer`
=====================================================

.. code-block:: py

    from django_client_framework.serializers import ModelSerializer


This class is agnostic to :drf:`Django Rest Framework (DRF)'s ModelSerializer
<serializers/#modelserializer>`. The usage is exactly the same as DRF.

.. warning::

    You should always use this class over the DRF's version, otherwise things
    will not work properly!

**Example**

.. code-block:: py

    from django_client_framework.serializers import ModelSerializer

    class ProductSerializer(ModelSerializer):
        class Meta:
            model = m.Product
            exclude: list = []


