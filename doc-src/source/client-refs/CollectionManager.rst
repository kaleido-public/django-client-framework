.. _CollectionManager:

`class` CollectionManager `<T:Model>`
=======================================

A generic class where ``T`` is constrained by `Model`_. This class provides the
access to backend objects. You should use this class to retrieve an
``ObjectManager`` for an model object, instead of creating an ``ObjectManager``
directly.

**Constructor**


Implementation varies. For TypeScript and Kotlin, you need to pass the
constructor of ``T`` in to the constructor, because the type information is
erased during the runtime.

.. warning::

    It is recommended to define a static member named ``objects`` on the model
    class, so that you can retrieve the ``CollectionManager`` instance directly.

    .. tabs::

        .. code-tab:: ts

            class Product extends Model {
                static readonly objects = new CollectionManager(Product)
            }

            let results = await Product.objects.page({})


**Methods**

.. _CollectionManager.page(...):

`method` .page `(query, pagination)`
--------------------------------------

    Returns a filtered collection of the model objects, with the desired
    pagination. It sends a ``GET`` request to the server.

    query
        A dictionary of query parameters that eventually get encoded as the
        query parts of the URL. The key names are agnostic to :django:`Django's
        QuerySet API <models/querysets>`. Keys such as ``id__in`` (with an array
        of ids as the value) are supported. See :django:`Django's Field lookups
        <models/querysets/#field-lookups>`.

        For example, a query dictionary of (in JSON format)

        .. code-block:: JSON

            {
                "id__in": [1,2],
                "barcode": "xxyy",
                "price__gt": 12.00
            }

        will be encoded as
        ``?id__in[]=1&id__in[]=2&barcode=xxyy&price__gt=12.00``.

        Suppoted keys
            Any property name of the model, or any :django:`Django's Field
            lookup keys <models/querysets/#field-lookups>`.

        Suppoted values
            Values of array, list, numbers, strings, empty, null types.

    pagination
        A dictionary indicating the number of pages, current page, and how to
        sort the result. Any value of the list/array type will have ``_``
        prepended before the key name, as a way to differentiate from the model
        property names.

        For example, a query dictionary of (in JSON format)

        .. code-block:: JSON

            {
                "limit": 50,
                "page": 1,
                "order_by": "-id"
            }

        will be encoded as ``?_limit=50&_page=1&_order_by=-id``.

        Suppoted key values
            :limit: number - how many items per page
            :page: number - which page to show
            :order_by: This is agnostic to Django's :django:`.order_by() <models/querysets/#order-by>` QuerySet API.
                Adding ``-`` before the key name sorts the property in the
                reverse order. Use ``,`` to join multiple keys.


    Returns
        A ``PageResult`` that contains the objects.

    .. tabs::

        .. code-tab:: ts

            let page: PageResult<Product> = await Product.objects.page({
                query: {
                    barcode__contains="xy"
                    price: null
                },
                page: {
                    limit: 10
                }
            })
            // GET /product?barcode__contains=xy&price=&_limit=10



.. _CollectionManager.get(...):

`method` .get `(query)`
---------------------------

    This method does the same thing as :ref:`CollectionManager.page(...)` except
    that it expects exactly one object to be returned from the server. If less
    or more than one object is returned, an InvalidObjectCount error is thrown.

    Returns
        An :ref:`ObjectManager` object wrapping the model.



.. _CollectionManager.create(...):

`method` .create `(data)`
-------------------------------

    Saves an object on the server with the provided dictionary of data. It sends
    a ``POST`` request to the server.

    Suppoted key-values
        Any property name and value of type accepted by on the model API.

    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = await Product.objects.create({
                name: "xxyy",
                price: null
            })
            // POST /product {"name": "xxyy", "price": null}

    Returns
        An :ref:`ObjectManager` object wrapping the created model.



.. _CollectionManager.get_or_create(...):

`method` .get_or_create `(query, defaults)`
---------------------------------------------------

    First tries to :ref:`CollectionManager.get(...)` the object with the query
    dictionary. If the object does not exist, then
    :ref:`CollectionManager.create(...)` the object by using the combined values
    on query and defaults. It sends a ``GET`` request, and if the object does
    not exist, then sends a ``POST`` request.

    Returns
        An :ref:`ObjectManager` object wrapping the model.

    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = await Product.objects.get_or_create({
                query: {
                    name: "xxyy",
                },
                defaults:  {
                    price: null
                }
            })
            // GET /product?name="xxyy"
            // POST /product {"name": "xxyy", "price": null}




.. _CollectionManager.update_or_create(...):

`method` .update_or_create `(query, defaults)`
------------------------------------------------------

    First tries to :ref:`CollectionManager.get(...)` the object with the
    ``query`` dictionary. If the object does not exist, then it follows the
    :ref:`CollectionManager.get_or_create(...)` logic. If the object already
    exists, then it updates the object with values in the ``defaults``
    dictionary. When updating, sends a ``PATCH`` request.

    Returns
        An :ref:`ObjectManager` object wrapping the model.

    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = await Product.objects.update_or_create({
                query: {
                    name: "xxyy",
                },
                defaults:  {
                    price: null
                }
            })
            // GET /product?name="xxyy"
            // (assumes id is 1) PATCH /product/1 {"price": null}


