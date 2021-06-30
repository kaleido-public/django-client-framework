Designing for a type-safe API
=============================

The goal of the client libraries is to provide type safety to gard against typos
that could be made on model properties, at the same type, utilize Django's
flexible QuerySet API. We would also like to keep a consistent API interface
across all supported programming languages, so that the learning curve can be
flat. Finally, we would like the client's model code to be automatically
generated according to the backend code.

There are some difficulties when designing such API. For instance, we can only
use features that are present in all supported programming languages. Advance
features such as the ``Partial<T>`` type in `TypeScript`, or `associated types`
in `Swift` cannot be used, because they don't exist in other languages, and the
API would be inconsistent.

We want to prevent typos made when querying and updating objects. The current
API provides limited guarantees. For instance, when modifying model properties
and call `ObjectManager.save()`_, typos are prevented because the programming
language only allows access on defined properties.

.. code-block:: ts

    let product: ObjectManager<Product> = ...
    product.barcode = "xxyy"
    product.save()


Make `.update(data)` safe
-------------------------

How can we make APIs such as `ObjectManager.update(...)`_ or
`CollectionManager.page(...)`_ type safe? There are two types of difficulties we
must take into consideration. First, you need to realize that the backend modal
API such as ``PATCH /product/1`` does not only accept valid properties that are
defined on the model. In fact, the backend could use :ref:`DelegateSerializer`
to accept a variaty of key-value pairs. For instance, if a `User` model API is
designed to change user password, the backend will expect an request such as:

.. code-block:: JSON

    // PATCH /user/1

    {
        old_password: "1234",
        new_password: "xxyy",
    }

The backend can achieve this with the :ref:`DelegateSerializer` class. However,
neither ``old_password`` and ``new_password`` are keys on the `User` model.

To resolve this issue, we can consider making the `ObjectManager.update(...)`_ a
generic method such as:

.. code-block:: TypeScript

    update<X>(data: X) {
        ...
    }

where X is any type that is serializable. This way we have define a separate interface such as

.. code-block:: TypeScript

    interface UserUpdatePassword {
        old_password: string
        new_password: string
    }

Then when calling the `ObjectManager.update(...)`_ method you can specify the ``X``:


.. code-block:: TypeScript

    .update<UserUpdatePassword>(data)


But there is another issue: when updating the model by sending JSON data to the
backend, a key that's missing in the data is not equivalent to the same key is
present in data but has the null value.

For instance, the following two data has different meanings:

.. code-block:: JSON

    // PATCH /product/1

    {
        brand_id: null,
        barcode: "xxyy"
    }


.. code-block:: JSON

    // PATCH /product/1

    {
        barcode: "xxyy"
    }

The first request sets the ``brand_id`` to null, but the second request is a
partial update that only changes the `barcode`, and leaves the ``brand_id``
unchanged.

When using an interface alone as the parameter ``X``, in most programming
languages, we can't tell the difference between the two cases. Because the best
you can do is to make a property optional on the interface, and you can set the
property as ``null``, and artificialy define that a ``null`` property represents
the second (or the first) request, but the ability to represent the other
request is missing.

We must resolve the issue using the type union. In other word, we must be able
to use two types on each property of the interface: the value's type, and the
null value. In TypeScript, this can be directly done by using the ``|``
operator. In other languages, such as `Swift` and `Kotlin`, we can use an
`enum`.

.. tabs::

    .. code-tab:: ts

        interface ProductUpdate {
            brand_id?: string | null
            barcode: string | null
        }


    .. code-tab:: swift

        enum Property<T> {
            case use(T)
            case null
        }

        interface ProductUpdate {
            brand_id?: Property(String)
            barcode: Property(String)
        }


Finally to use the `.update(data)` method:

.. tabs::

    .. code-tab:: ts

        product.update<ProductUpdate>({
            brand_id: null,
            barcode: "xxyy"
        })

    .. code-tab:: swift

        product.update<ProductUpdate>({
            brand_id: .null,
            barcode: .use("xxyy")
        })



Make `.page(...)` safe
----------------------

This is the most challenging API, because Django has very powerful support for
relational quries, and we want to keep Django's ability in the frontend. For
example, in the `Product` and `Brand` example, a product has a brand, and a
brand has many products. In Django, if we want to find all product of any brand
where the brand's name contains a substring ``abc``, we can use:

.. code-block:: py

    Product.objects.filter(brand__name__contains="abc")

Our API supports this ability. In particular, you can send a ``GET`` request to this url:

.. code-block::

    GET /product?brand__name__contains="abc"

The ability is also supported on regular properties, for example, we can filter
`Product` by ``barcode``:

.. code-block::

    GET /product?barcode__contains="xy"

.. seealso::

    All full explanation is on the Django's official documentation for :django:`Lookup API reference <models/lookups/>`.
        | A lookup expression consists of three parts:
        | 1. Fields part (e.g. ``Book.objects.filter(author__best_friends__first_name...)``;
        | 2. Transforms part (may be omitted) (e.g. ``__lower__first3chars__reversed``);
        | 3. A lookup (e.g. ``__icontains``) that, if omitted, defaults to ``__exact``.

The syntax of the query name is recursive:

{
    brand: {name: contains("xxyy"))
}
.. code-block::

    query name on T -> regular property of T = value of type of T
                     | string property of T __contains = value of string
                     | string property of T __in = value of list of string
                     | number property of T __in = value of list of number
                     | number property of T __gt = value of number
                     | regular property of T __not __ = value of number
                     | relational property R of T = query name on R

