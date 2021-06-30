.. _RelatedObjectManager:

`class` RelatedObjectManager `<T:Model, P:Model>`
===============================================================================================


A generic class where ``T`` and ``P`` are constrained by `Model`_. This class
provides the ability access and modify one-to-one relations between two object.

**Constructor**

Implementation varies. Most commonly, three values are passed into the constructor:

    1. The constructor of ``T``, the model to be retrieved via the manager.
    2. The manager's parent object of type ``P``. Usually, this is the ``this`` keyword.
    3. The property's name on the model.

For instance, for the `Product` and `Brand` relation, a product is owned by one brand. In
this case:

    1. The constructor of ``T`` is ``Brand``.
    2. The `parent` is the product object.
    3. Finally, the property's name on ``Product`` is ``brand``.


.. tabs::

    .. code-tab:: ts

        class Brand extends Model {
            // ...
        }

        class Product extends Model {
            // ...
            get brand() { return new RelatedObjectManager(Brand, this, "brand") }
        }


`method` .get `()`
--------------------

    Returns
        An `ObjectManager`_ wrapping the object that's related to the parent. It
        sends a ``GET`` request to the server.

    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = ... // assumes id is 1
            let brand: ObjectManager<Brand> = await product.brand.get()
            // GET /product/1/brand


`method` .set `(target?)`
--------------------------

    Sets the object related to the parent object. This is an alternative to
    setting the foreign id directly on the parent. It sends a ``PUT`` request to
    the server.

    target
        An `ObjectManager`_ wrapping the object that's set to be related to the
        parent.


    .. tabs::

        .. code-tab:: ts

            let product: ObjectManager<Product> = ... // assumes id is 1
            let brand: ObjectManager<Brand> = ... // assumes id is 1
            product.brand.set(brand)
            // PUT /product/1/brand [1]
