.. _ObjectManager:

`class` ObjectManager `<T: Model>: T`
==========================================================

A generic class where ``T`` is constrained by :ref:`Model`. This class provides
the ability to modify an model object. When constructing an `ObjectManager`_
instance, an model object is passed into the `ObjectManager`_ class constructor.
Any field that's available on the model objects becomes available on the
`ObjectManager`_ object. In addition, the `ObjectManager`_ object provides
methods that are used to modify the wrapped model object, and save the changes
to the backend.


**Constructor**

Pass the model object into the `ObjectManager`_ constructor.

.. warning::

    Most of time, you should use the `ObjectManager`_ returned by
    `CollectionManager.page(...)`_ or `CollectionManager.get(...)`_, instead of
    creating one yourself.


**Example**

.. tabs::

    .. code-tab:: ts

        let product_model = new Product()
        let product = new ObjectManagerImpl(product_model)

.. warning::

    Due to a limitation of TypeScript, the constructor is named
    ``ObjectManagerImpl`` instead of `ObjectManager`_, which is a type
    alias.


**Methods**

`method` .refresh `()`
-------------------------

    Pulls data from the server and updates the local data.
    It sends a ``GET`` request to the server.

    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = ...
            product.barcode = 'xxyy'
            // GET /product/1
            await product.refresh() // resets product barcode


.. _ObjectManager.save():

`method` .save `()`
---------------------

    Updates the server with properties that have been changed on the object. It
    sends a ``PATCH`` request to the server.

    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = ...
            product.barcode = "xxyy"
            product.price = null
            product.brand_id = 2
            // PATCH /product/1 {"barcode": "xxyy", "price": null, "brand_id": 2}
            await product.save()


.. _ObjectManager.update(...):

`method` .update `(data)`
------------------------------

    Updates the server with a dictionary, and also saves the changes locally. It
    sends a ``PATCH`` request to the server.


.. only:: internal

    .. seealso::

        `The Design Decision for Type-safety`_.

    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = ...
            // PATCH /product/1 {"barcode": "xxyy", "price": null}
            await product.update({
                barcode: "xxyy",
                price: null
            )}

`method` .delete `()`
----------------------------

    Removes the data from the server. It sends a DELETE request to the server.

    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = ...
            // DELETE /product/1
            await product.delete()
