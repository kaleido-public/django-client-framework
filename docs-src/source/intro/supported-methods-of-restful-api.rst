.. _Supported_RESTful_API:

Supported Methods of the RESTful API
=====================================

Types of routes
----------------

There are four types of routes:

    1. Collection API, `eg. /product/`
    2. Object API, `eg. /product/1`
    3. Related Collection API, `eg. /brand/1/products`
    4. Related Object API, `eg. /product/1/brand`

Supported HTTP methods and meanings
----------------------------------------

The following HTTP methods are supported for each type of routes:

**Collection API**, `eg. /product/`

    ``GET``: Retrieve a list of objects.

        Accepted query parameters:
            * ``_page``: an integer indicating which page to display
            * ``_limit``: an integer indicating how many results per page to include
            * ``_order_by``: This is agnostic to Django's :django:`.order_by() <models/querysets/#order-by>` QuerySet API. Adding ``-`` before the key name sorts the property in the reverse order. Use ``,`` to join multiple keys.
            * Any key names that are agnostic to :django:`Django's QuerySet
              API <models/querysets>`. Keys such as ``id__in[]`` are supported.
              See :django:`Django's Field lookups
              <models/querysets/#field-lookups>`. Any value of the list/array
              type must have ``[]`` appended after the key name.

        Example:
            .. code-block::

                GET /product?id__in[]=1&id__in[]=2&_page=1&_order_by=-id


    ``POST``: Create an object.

        Accepted JSON body:
            A dictionary accepted by the model's serializer.

        Example:
            .. code-block::

                POST /product

                {
                    barcode: "xxyy"
                }

**Object API**, `eg. /product/1`

    ``GET``: Retrieve an object.

        Accepted query parameters:
            Same as the `Collection API`. The response is `404 Not Found` if the
            filtered result is empty.

    ``PATCH``: Update an object.

        Accepted JSON body:
            A dictionary accepted by the model's serializer.

**Related Collection API**, `eg. /brand/1/products`

    ``GET``: Retrieve a list of related objects.

        Accepted query parameters:
            Same as the `Collection API`.

    ``POST``: Link some related objects to the parent object.

        Accepted JSON body:
            A list of object ids.

        Example:
            .. code-block::

                POST /brand/1/products

                [1,2,3]

    ``DELETE``: Unlinks some related objects from the parent object.

        Accepted JSON body:
            A list of object ids.

    ``PATCH``: Set the related objects to the specified set.

        Accepted JSON body:
            A list of object ids.

        Example:
            .. code-block::

                PATCH /brand/1/products

                [] // unlink all relations

**Related Object API**, `eg. /product/1/brand`

    ``GET``: Get the details of the related object.

    ``PATCH``: Link a related object to the parent object.

        Accepted JSON body:
            A object id, or null.

        Example:
            .. code-block::

                PATCH /products/1/brand

                1
