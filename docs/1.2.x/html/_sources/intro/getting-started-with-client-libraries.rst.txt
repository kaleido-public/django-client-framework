Getting Starting with Client Libraries
======================================

.. seealso::

    This tutorial follows the previous tutorial "`Getting Started with the
    Backend`_". In this section, we assume the `Product` and `Brand` models are
    correctly set up.

Instead of sending HTTP requests manually to query the backend REST API,
Django Client Framework's client libraries support quering the backend in
frontend's native programming language, with a set of APIs that are similar to
Django's `QuerySet`.


Install client libraries
------------------------

.. tabs::

    .. code-tab:: bash TypeScript

        # With npm
        npm install django-client-framework

        # Or with yarn
        yarn add django-client-framework

    .. code-tab:: bash Dart

        # With Dart
        dart pub add django-client-framework --git-url=https://github.com/kaleido-public/django-client-framework-dart.git

        # Or with Flutter
        flutter pub add django-client-framework --git-url=https://github.com/kaleido-public/django-client-framework-dart.git



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
            id!: string
            barcode: string = ""
            brand_id?: number
        }

    .. code-tab:: dart

        import 'package:django_client_framework/django_client_framework.dart';

        class Product extends Model {
            static final objects = CollectionManager(Product);

            @override
            String get id => props["id"];

            String get barcode => props["barcode"];
            set barcode(String val) => props["barcode"] = val;

            String get brandID => props["brand_id"];
            set brandID(String val) => props["brand_id"] = val;
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
                pages_count: 1,
                objects_count: 1,
                objects: [ Product { id: "...", barcode: 'xxyy', brand_id: "..." } ]
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
            id!: string
            barcode: string = ""
            brand_id?: number
        }

        class Brand extends Model {
            static readonly objects = new CollectionManager(Brand)
            id!: string
            name: string = ""
        }

    .. code-tab:: dart

        import 'package:django_client_framework/django_client_framework.dart';

        class Product extends Model {
            static final objects = CollectionManager(Product);

            @override
            String get id => props["id"];

            String get barcode => props["barcode"];
            set barcode(String val) => props["barcode"] = val;

            String get brandID => props["brand_id"];
            set brandID(String val) => props["brand_id"] = val;
        }

        class Brand extends Model {
            static final objects = CollectionManager(Brand);

            @override
            String get id => props["id"];

            String get name => props["name"];
            set name(String val) => props["name"] = val;
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
            id!: string
            barcode: string = ""
            brand_id?: number
        }

        class Brand extends Model {
            static readonly objects = new CollectionManager(Brand)
            get products() { return new RelatedCollectionManager(Product, this, "products") }
            id!: string
            name: string = ""
        }

    .. code-tab:: dart

        import 'package:django_client_framework/django_client_framework.dart';

        class Product extends Model {
            static final objects = CollectionManager(Product);

            @override
            String get id => props["id"];

            String get barcode => props["barcode"];
            set barcode(String val) => props["barcode"] = val;

            String get brandID => props["brand_id"];
            set brandID(String val) => props["brand_id"] = val;

            RelatedObjectManager<Brand, Product> get brand =>
                RelatedObjectManager(Brand, this, 'brand');
        }

        class Brand extends Model {
            static final objects = CollectionManager(Brand);

            @override
            String get id => props["id"];

            String get name => props["name"];
            set name(String val) => props["name"] = val;
        }


We can retrieve the product, then get the brand object off the product:

.. tabs::

    .. code-tab:: ts

        import { Ajax } from "django-client-framework"
        import { Product } from "./models"

        Ajax.url_prefix = "http://localhost:8000"

        let product = await Product.objects.get({ id: "..." })

        console.log(product)
        // Product { id: "...", barcode: 'xxyy', brand_id: "..." }

        let nike = product.brand.get()
        console.log(nike)
        // Brand { id: "...", name: 'nike' }

    .. code-tab:: dart

        import 'package:django_client_framework/django_client_framework.dart';

        ajax.endpoints = [
            APIEndpoint(
                scheme: "http",
                host: "localhost",
                urlPrefix: "en/api/v1/",
                port: 8000,
            )
        ];

        final product = await Product.objects.get(id: "...");
        // Product { id: "...", barcode: 'xxyy', brand_id: "..." }

        final nike = await product.brand.get();
        // Brand { id: "...", name: 'nike' }
