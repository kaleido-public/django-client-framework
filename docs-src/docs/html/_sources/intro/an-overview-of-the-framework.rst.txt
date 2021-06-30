An Overview of the Framework
============================

Django Client Framework is meant to work with the famous python server framework
`Django <https://www.djangoproject.com>`_, and its popular REST API library,
`Django Rest Framework <https://www.django-rest-framework.org>`_.

The Django Client Framework includes client libraries in multiple languages,
which enables frontend developers to query the database using native programming
languages, without having to worry about the communication details at the REST
API level.

For instance, when a `Product` model is defined in Django:

.. code-block:: py

   class Product(Model):
      barcode = CharField()

With the Django Client Framework, a corresponding model in the frontend language
is defined.


.. tabs::

   .. code-tab:: ts

         class Product extends Model {
            barcode: str;
         }

   .. code-tab:: kotlin

         class Product(
            val barcode: String
         ): Model

   .. code-tab:: swift

         struct Product: Model {
            var barcode: String
         }

Then to query get a Product object in the frontend, you can use the API provided
by the Django Client Framework, which is extremely similar to the Django's:

.. tabs::

   .. code-tab:: ts

         let results: PageResult<Product> = await Product.objects.page()
         let product: Product = results[0]
         product.barcode = "xxyy"
         await product.save()

   .. code-tab:: kotlin

         val result: PageResult<Product> = Product.objects.page()
         val product: Product = results[0]
         product.barcode = "xxyy"
         product.save()

   .. code-tab:: swift

         let results: PageResult<Product> = try Product.objects.page().await()
         let product: Product = results[0]
         product.barcode = "xxyy"
         product.save().await()


.. note::

   The Django Client Framework has two components, the frontend libraries,
   and the backend API server based on Django. You need to install both components
   into your project.

Internally, a communication protocol based on RESTful API is used between the
frontend and the backend. The protocol is considered an internal detail of the
Django Client Framework, and you should not need to worry about it.

.. image:: /images/overview1.jpg

