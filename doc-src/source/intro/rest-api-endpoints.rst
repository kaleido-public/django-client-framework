.. _Supported_REST_API:

REST API Endpoints
=====================================

There are four types of routes:

    1. :ref:`Collection API <collection-api>`, `eg. /product`
    2. :ref:`Object API <object-api>`, `eg. /product/<id>`
    3. :ref:`Related Collection API <related-collection-api>`, `eg. /brand/<id>/products`
    4. :ref:`Related Object API <related-object-api>`, `eg. /product/<id>/brand`

The following HTTP methods are supported for each type of routes:


.. _collection-api:

Collection API
------------------------

``GET``: lists objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted query parameters:
        ``_page``
            An integer indicating which page to display

        ``_limit``
            An integer indicating how many results per page to include

        ``_order_by``
            This is handled by Django's :django:`.order_by() <models/querysets/#order-by>` QuerySet API. Adding ``-`` before the key name sorts the property in the reverse order. Use ``,`` to join multiple keys.

        ``<property>[__<transformer>...][__<lookup>]``
            Any key names are handled by :django:`Django's QuerySet API
            <models/querysets>`. Keys such as ``id__in[]`` are passed to
            :django:`.filter() <models/querysets/#filter>`. See
            :django:`Django's Field lookups <models/querysets/#field-lookups>`.
            Any value of the list/array type must have ``[]`` appended after the
            key name.

    .. seealso::

        For more examples of the Collection API query parameters, see
        :ref:`Pagination <collection-api-pagination>` and :ref:`Filtering
        <collection-api-filtering>`.

    Example:
        .. code-block:: bash

            GET /product
                ?id__in[]=id1,id2
                &_page=1
                &_order_by=-id

            # Alternatively, separate id__in[] for each array element
            GET /product
                ?id__in[]=id1
                &id__in[]=id2
                &_page=1
                &_order_by=-id


``POST``: creates an object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted JSON body:
        A dictionary accepted by the model's serializer.

    Example:
        .. code-block::

            POST /product

            {
                barcode: "xxyy"
            }



.. _object-api:

Object API
-----------------------

``GET``: retrieves an object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted query parameters:
        Same as the :ref:`Collection API <collection-api>`. The response is `404
        Not Found` if the filtered result is empty.

    Example:
        .. code-block::

            GET /product/1370f589-6a45-4a25-8b77-c28c98b8b98b

            {
                id: "...",
                type: "product",
                barcode: "xxyy"
            }

``PATCH``: updates an object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted JSON body:
        A dictionary accepted by the model's serializer.

    Example:
        .. code-block::

            PATCH /product/1370f589-6a45-4a25-8b77-c28c98b8b98b

            {
                barcode: "xxyy"
            }


.. _related-collection-api:

Related Collection API
-----------------------------

``GET``: lists related objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted query parameters:
        Same as the :ref:`Collection API <collection-api>`.

    Example:
        .. code-block::

            GET /brand/1370f589-6a45-4a25-8b77-c28c98b8b98b/products

            {
                "limit" : 1,
                "objects_count" : 15,
                "page" : 1,
                "pages_count" : 15
                "objects" : [
                    {
                        "id": "...",
                        "type": "product",
                    }
                ],
            }

``POST``: creates a relation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted JSON body:
        A list of object ids.

    Example:
        .. code-block::

            POST /brand/<brand_id>/products

            ["32453b61-6718-45bf-bccb-d866cdd3ddad", "662c99ee-5a65-4e39-ac3a-2836aa52b3ed"]

``DELETE``: removes a relation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted JSON body:
        A list of object ids.

``PATCH``: sets a set of relations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted JSON body:
        A list of object ids.

    Example:
        .. code-block:: js

            PATCH /brand/662c99ee-5a65-4e39-ac3a-2836aa52b3ed/products

            [] // unlink all relations

.. _related-object-api:

Related Object API
--------------------------

``GET``: retrieves a related object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted query parameters:
        Same as the :ref:`Object API <object-api>`.

    Example:
        .. code-block::

            GET /product/1370f589-6a45-4a25-8b77-c28c98b8b98b/brand

            {
                "id": "...",
                "type": "brand",
                "name": "xxyy",
            }

``PATCH``: sets a related object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Accepted JSON body:
        A object id, or ``null``.

    Example:
        .. code-block::

            PATCH /products/662c99ee-5a65-4e39-ac3a-2836aa52b3ed/brand

            "32453b61-6718-45bf-bccb-d866cdd3ddad"



.. _collection-api-pagination:

Pagination (Collection APIs)
---------------------------------

Both collection APIs (regular and related) support pagination by these query parameters:

    ``_limit``
        An integer to specify how many objects to return per page.

    ``_page``
        An integer to specify the page number. The first page is ``1``.

    ``_order``
        A pattern that matches ``[-]<property>, [-]<property>, ...``. For
        example, ``id, -username``. The collection is sorted by the first
        property in an increasing order, then the other properties are tie
        breakers in that order. When ``-`` is before a property name, it means
        to sort by that property in the decreasing order.

Server responses:

    .. code::

        {
            "objects" : [
                <model_objects>
            ],
            "limit" : int,
            "objects_count" : int,
            "page" : int,
            "pages_count" : int
        }

    ``objects``
        The list of objects.

    ``limit``
        This is just an echo of the ``_limit`` provided in the request.

    ``objects_count``
        Total number of objects found in all pages.

    ``page``
        Current page number. Starts from ``1``.

    ``pages_count``
        Total number of pages.



.. _collection-api-filtering:

Filtering (Collection APIs)
----------------------------------

The collection API (regular and related) support filtering objects by most
properties. There are five types of properties: number, string, datetime,
foreign key and reverse foreign key.

You can use the ``<property>[__<lookup>]`` to filter the objects. The
``__<lookup>`` is optional. For example, for the `CartItem` model,
``quantity__gte=2`` filters the object where the ``quantity`` property is
`greater than or equal to` ``2``. When the lookup part is left out, it is the
same as ``<property>__eq``, which is `exactly equal`.

.. _number-property:

Number property
~~~~~~~~~~~~~~~~~~~~~

    The supported lookup are:

        :``__eq``: `(default)` Equal to. This is the default if ``__<lookup>`` if omitted.
        :``__ne``: Not equal to.
        :``__gte``: Greater than or equal to.
        :``__lte``: Less than or equal to.
        :``__gt``: Greater than.
        :``__lt``: Less than.
        :``__range[]=a,b``: Between ``a`` and ``b``, inclusive.
        :``__in[]``: Equal to any number in the list. Eg. ``__in[]=1,2,3``.
        :``__isnull=true``: Is null.

String property
~~~~~~~~~~~~~~~~~~~

    The supported lookup are:

        :``__exact``: `(default)` Equal to. This is the default if ``__<lookup>`` if omitted.
        :``__iexact``: Equal to, case-insensitive.
        :``__contains``: String contains a substring.
        :``__icontains``: String contains a substring, case-insensitive.
        :``__startswith``: String that starts with a prefix
        :``__endswith``: String that ends with a prefix
        :``__istartswith``: String that starts with a prefix, case-insensitive.
        :``__iendswith``: String that ends with a prefix, case-insensitive.
        :``__regex``: String that matches the regex.
        :``__iregex``: String that matches the regex, case-insensitive.
        :``__in[]``: Equal to any string in the list. Eg. ``__in[]=abc,def,ghi``.
        :``__isnull=true``: Is null.

Datetime property
~~~~~~~~~~~~~~~~~~~~~

    The following lookups are supported, when supplied values in the format of
    ISO 8601, for example, ``2022-01-14T12:03:03.899967-05:00``.

        :``__eq``: `(default)` Equal to. This is the default if ``__<lookup>`` if omitted.
        :``__ne``: Not equal to.
        :``__gte``: Later than or equal to (greater than or equal to).
        :``__lte``: Earlier than or equal to (less than or equal to).
        :``__gt``: Later than (greater than).
        :``__lt``: Earlier than (less than).
        :``__range[]=a,b``: Between ``a`` and ``b``, inclusive.


        :``__in[]``: Equal to any number in the list. Eg. ``__in[]="2022-01-14T12:03:03.899967-05:00","2022-01-14T12:03:03.899967-05:00"``.
        :``__isnull=true``: Is null.

    In addition to straight lookups, you can extract values such as the year,
    the month, the date, using `transformers`. After transforming the value, the
    output is a number that can be further chained by a lookup of the
    :ref:`Number property <number-property>`.

    For example, by using the transformer ``__year``, you can filter objects
    that are created between ``2020`` and ``2021`` by using
    ``__year__range[]=2020,2021``.

    The full syntax is ``<property>[__<transformer>][__<lookup>]``.

    Supported transformers are:

        :``__year``: Year as an integer.
        :``__month``: Month as an integer between ``1`` and ``12``.
        :``__day``: Day of the month as an integer.
        :``__week``: Week of the year as an integer.
        :``__week_day``: Day of the week as an integer, between `1`` and ``7``.
        :``__quarter``: Quarter of the year as an integer, between `1`` and ``4``.
        :``__hour``: Hour of the day as an integer, between `0`` and ``23``.
        :``__minute``: Minute of the hour as an integer, between `0`` and ``59``.
        :``__second``: Minute of the minute as an integer, between `0`` and ``59``.




Foreign key property
~~~~~~~~~~~~~~~~~~~~~~~~~~

    The supported lookup are:

        :``__exact``: `(default)` Equal to. This is the default if ``__<lookup>`` if omitted.
        :``__in[]``: Equal to any id in the list. Eg. ``__in[]=346ed90a-2360-4c44-801d-9623b3a1059a,0332daeb-e4b9-46e3-bf8a-0469ff54d1d0``.
        :``__isnull=true``: Is null.


Look up through related objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    In addition to look up by the current model's properties, if the object has
    a related object, you can also filter the current model by the related
    object's properties. For example, you can filter `Product` by the
    `ProdutGroup`'s name.

    .. code::

        /api/v1/product?productgroup__name__istartswith=abc

    All lookup methods above are also supported. The look up can be arbitrarily
    deep. The supported syntax in general is
    ``<property>[__<property>...][__<lookup>]``.
