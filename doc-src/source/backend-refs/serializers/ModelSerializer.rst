.. _DCFModelSerializer:

`class` DCFModelSerializer `extends DCFSerializer`
=====================================================

.. code-block:: py

    from django_client_framework.serializers import DCFModelSerializer


This class is agnostic to :drf:`Django Rest Framework (DRF)'s ModelSerializer
<serializers/#modelserializer>`. The usage is exactly the same as DRF.

.. warning::

    You should always use this class over the DRF's version, otherwise things
    will not work properly!

**Example**

.. code-block:: py

    from django_client_framework.serializers import DCFModelSerializer

    class ProductSerializer(DCFModelSerializer):
        class Meta:
            model = m.Product
            exclude: list = []


