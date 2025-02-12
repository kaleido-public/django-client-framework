.. _RelatedCollectionManager:

`class` RelatedCollectionManager `<T:Model, P:Model>`
============================================================================================

A generic class where ``T`` and ``P`` are constrained by `Model`_. This class
provides the ability access and modify many-to-one or many-to-many object
relations.

**Constructor**

Implementation varies. Most commonly, three values are passed into the constructor:

    1. The constructor of ``T``, the model to be retrieved via the manager.
    2. The manager's parent object of type ``P``. Usually, this is the ``this`` keyword.
    3. The property's name on the model.

For instance, for the `Product` and `Brand` relation, a brand has many products. In
this case:

    1. The constructor of ``T`` is ``Product``.
    2. The `parent` is the brand object.
    3. Finally, the property's name on ``Brand`` is ``products``.


.. tabs::

    .. code-tab:: ts

        class Product extends Model {
            // ...
        }

        class Brand extends Model {
            // ...
            get products() { return new RelatedCollectionManager(Product, this, "products") }
        }


.. _RelatedCollectionManager.page1:

`method` .page `(query, pagination)` ``disamb-RelatedCollectionManager``
-----------------------------------------------------------------------------

    This method is agnostic to `CollectionManager.page(...)`_, but to retrieve a
    collection of related model objects. It sends a ``GET`` request to the
    server.

    .. tabs::

        .. code-tab:: ts

            let brand: ObjectManager<Brand> = ... // assumes id is 1
            let products = await brand.products.page({
                query: {
                    name__contains: "xy"
                }
            })
            // GET /brand/<id>/products?name__contains=xy



.. _RelatedCollectionManager.get(...):

`method` .get `(query, pagination)`
----------------------------------------

    This method is agnostic to `CollectionManager.get(...)`_, but to retrieve a
    collection of related model objects. It sends a ``GET`` request to the
    server.



.. _RelatedCollectionManager.addIDs(...):

`method` .addIDs `(ids)`
----------------------------

    Creates object relations using object ids. It sends a ``POST`` request to
    the server.

    ids
        The ids of the objects to be added to the collection.

    .. tabs::

        .. code-tab:: ts

            let brand: ObjectManager<Brand> = ... // assumes id is 1
            let product: ObjectManager<Product> = ... // assumes id is 1
            await brand.products.addIDs([product.id])
            // POST /brand/<id>/products [1]


.. _RelatedCollectionManager.setIDs(...):

`method` .setIDs `(ids)`
-------------------------------

    Clear the object relations first, before adding new ones using the object
    ids. It sends a ``PUT`` request to the server.

    ids
        The ids of the objects to be used as the collection.


    .. tabs::

        .. code-tab:: ts

            let brand: ObjectManager<Brand> = ... // assumes id is 1
            let product: ObjectManager<Product> = ... // assumes id is 1
            await brand.products.setIDs([product.id])
            // PUT /brand/<id>/product [1]


.. _RelatedCollectionManager.removeIDs(...):

`method` .removeIDs `(ids)`
-------------------------------

    Removes object relations using object ids. The method only removes the
    relation. It does not delete the objects. It sends a ``DELETE`` request to
    the server.

    ids
        The ids of the objects to be removed from the collection.


    .. tabs::

        .. code-tab:: ts

            let brand: ObjectManager<Brand> = ... // assumes id is 1
            let product: ObjectManager<Product> = ... // assumes id is 1
            await brand.products.removeIDs([product.id])
            // DELETE /brand/<id>/product [1]


`method` .add `(objs)`
--------------------------

    Same as `RelatedCollectionManager.addIDs(...)`_ but takes a set of
    `ObjectManager`_ objects instead.

    objs
        A set of `ObjectManager`_ objects whose ids are added to the collection.


`method` .set `(objs)`
--------------------------

    Same as `RelatedCollectionManager.setIDs(...)`_ but takes a set of
    `ObjectManager`_ objects instead.

    objs
        A set of `ObjectManager`_ objects whose ids are set as the collection.


`method` .remove `(objs)`
---------------------------------

    Same as `RelatedCollectionManager.removeIDs(...)`_ but takes a set of
    `ObjectManager`_ objects instead.

    objs
        A set of `ObjectManager`_ objects whose ids are removed from the
        collection.

