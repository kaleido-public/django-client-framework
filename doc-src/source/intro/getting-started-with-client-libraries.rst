Getting Starting with Client Libraries
======================================

.. seealso::

    This tutorial follows the previous tutorial "`Getting Started with the
    Backend`_". In this section, we assume the `Product` and `Brand` models are
    correctly set up.

Instead of sending HTTP requests manually to query the backend RESTful API,
Django Client Framework's client libraries support quering the backend in
frontend's native programming language, with a set of APIs that are similar to
Django's `QuerySet`.


Install client libraries
------------------------

TypeScript
~~~~~~~~~~

The TypeScript client can be installed with the npm or yarn package
managers.

.. tabs::

    .. code-tab:: bash NPM

        npm install django-client-framework

    .. code-tab:: bash Yarn

        yarn add django-client-framework


Swift
~~~~~


Kotlin
~~~~~~

Define a model class
--------------------

Since a `Product` model is defined at the Django backend, we need to define a
`Product` model that mirrors the backend in the frontend language.

.. warning::

    A more accurate statement is that the `Product` model in the frontend
    mirrors the `ProductSerializer` in the backend. This is because a serializer
    can support fields that doesn't exist on the model, for instance, through
    the `SerializerMethodField`.

Similar to the Django models, the `Product` model in the frontend should also
extend the :ref:`Model` base class.

.. tabs::

    .. code-tab:: ts

        import { Model, CollectionManager } from "django-client-framework"

        class Product extends Model {
            static readonly objects = new CollectionManager(Product)
            id: number = 0
            barcode: string = ""
            brand_id?: number
        }




Retrieve a model object
-----------------------

To retrieve a `Product` instance, we use the `CollectionManager` class. To
retrieve an instance of the `CollectionManager`, you can either create it
yourself, or access it through tbe `.objects` static member on the `Product`
class.

.. tabs::

    .. code-tab:: ts

        import { Ajax } from "django-client-framework"

        Ajax.url_prefix = "http://localhost:8000"

        let page = await Product.objects.page({})
        console.log(page)

        /*
            PageResult {
                page: 1,
                limit: 50,
                total: 1,
                previous: null,
                next: null,
                objects: [ Product { id: 1, barcode: 'xxyy', brand_id: 1 } ]
            }
        */


.. seealso::

    Besides retrieving object, the client libraries also support methods that
    modify and delete objects. See the full set of APIs here. [todo]


Retrieve a relational object
----------------------------

First, we first add a `Brand` model:

.. tabs::

    .. code-tab:: ts

        import { Model, CollectionManager } from "django-client-framework"

        class Product extends Model {
            static readonly objects = new CollectionManager(Product)
            id: number = 0
            barcode: string = ""
            brand_id?: number
        }

        class Brand extends Model {
            static readonly objects = new CollectionManager(Brand)
            id: number = 0
            name: string = ""
        }


To access the `Brand` object on the product, we add a brand field of the
`RelatedObjectManager` type to `Product`, and a products field of the
`RelatedCollectionManager` type to `Brand`.

.. tabs::

    .. code-tab:: ts

        import { Model, CollectionManager, RelatedObjectManager } from "django-client-framework"

        class Product extends Model {
            static readonly objects = new CollectionManager(Product)
            get brand() { return new RelatedObjectManager(Brand, this, "brand") }
            id: number = 0
            barcode: string = ""
            brand_id?: number
        }

        class Brand extends Model {
            static readonly objects = new CollectionManager(Brand)
            get products() { return new RelatedCollectionManager(Product, this, "products") }
            id: number = 0
            name: string = ""
        }

We get the product that has `id=1`, then get the brand object off the product:

.. tabs::

    .. code-tab:: ts

        import { Ajax } from "django-client-framework"
        import { Product } from "./models"

        Ajax.url_prefix = "http://localhost:8000"

        let product = await Product.objects.get({ id: 1 })

        console.log(product)
        // Product { id: 1, barcode: 'xxyy', brand_id: 1 }

        let nike = product.brand.get()
        console.log(nike)
        // Brand { id: 1, name: 'nike' }
