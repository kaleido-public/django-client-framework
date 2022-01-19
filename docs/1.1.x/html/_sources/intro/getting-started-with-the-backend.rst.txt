Getting Started with the Backend
================================

.. warning::

    This guide assumes that you are familiar with Django. Before starting, you
    may want to go through Django's tutorial first:
    https://docs.djangoproject.com/en/3.2/


Installation with pip3+git
--------------------------

Django Client Framework (Django) requires ``python3.8+`` and ``Django 3.0+``. To
install Django Client Framework from the GitHub repository:

With ``pip``:
    .. code-block:: bash

        pip3 install git+https://github.com/kaleido-public/django-client-framework.git@staging

With ``poetry``:
    .. code-block:: bash

        poetry add git+https://github.com/kaleido-public/django-client-framework.git@staging


Configure Django's settings.py file
-----------------------------------

In ``settings.py`` for your Django app, simply add *at the end of the file*:

.. code-block:: py

    import django_client_framework.settings
    django_client_framework.settings.install(
        INSTALLED_APPS,
        REST_FRAMEWORK,
        MIDDLEWARE,
        AUTHENTICATION_BACKENDS
    )


.. warning::

    The line must be added after where the ``INSTALLED_APPS``, ``REST_FRAMEWORK``,
    ``MIDDLEWARE`` and ``AUTHENTICATION_BACKENDS`` global variables are defined,
    because the ``.install()`` function modifies these variables by reference.

An example of the ``settings.py`` file is as follows:

.. code-block:: py

    import django_client_framework.settings

    # ... other configs

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
    ]

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    REST_FRAMEWORK = {
        # .. your settings
    }

    AUTHENTICATION_BACKENDS = [
        # .. your settings
    ]

    # Add this line
    django_client_framework.settings.install(
        INSTALLED_APPS,
        REST_FRAMEWORK,
        MIDDLEWARE,
        AUTHENTICATION_BACKENDS
    )


Add routing handlers to ``urls.py``
-----------------------------------

Next, append Django Client Framework's API route handlers to your app's
``urls.py`` file:

.. code-block:: py

    from django.urls import path, include
    import django_client_framework.api.urls

    app_name = "myapp"

    urlpatterns = [
        ... # other routes
        path("<str:locale>/api/<str:version>", include(django_client_framework.api.urls))
    ]


.. note::

    The ``.urlpatterns`` variable provided by the Django Client Framework is just
    a list of routes and handlers. You can append this variable to your
    urlpatterns list flexiably. Internally, the ``.urlpatterns`` is defined as
    follows:

    .. code-block:: py

        # django_client_framework.api.urls.urlpatterns
        urlpatterns = [
            path("<str:model>", ModelCollectionAPI.as_view(), name="model_collection"),
            path("<str:model>/<int:pk>", ModelObjectAPI.as_view(), name="model_object"),
            path(
                "<str:model>/<int:pk>/<str:target_field>",
                ModelFieldAPI.as_view(),
                name="model_field",
            ),
        ]


Add a Serializable model
-------------------------

To add a model, create a model that extends from
``django_client_framework.models.Serializable``. For instance:

.. code-block:: py

    from django_client_framework.models import DCFModel, Serializable
    from django.db.models import CharField

    class Product(DCFModel, Serializable):
        barcode = CharField(max_length=32)


The ``Serializable`` class requires ``Product`` to implement a class method
named ``.get_serializer_class()``, which should return a ``DCFModelSerializer``
class. This class is responsible for converting back and forth betwen a JSON
object and a class object, ie, serialization and deserialization.


To define a ``DCFModelSerializer`` for ``Product``, create another class that
inherits from ``DCFModelSerializer``:


.. code-block:: py

    from django_client_framework.serializers import DCFModelSerializer

    class ProductSerializer(DCFModelSerializer):
        class Meta:
            model = Product
            fields = ["id", "type", "created_at", "barcode"]


.. error::

    `DCFModelSerializer` is a subclass of `ModelSerializer` in Django Rest
    Framework. Always use `DCFModelSerializer`, or the APIs don't work!


Finally, we return this class from the ``.get_serializer_class()`` method. The final code
looks like this:


.. code-block:: py

    from django_client_framework.models import DCFModel, Serializable
    from django_client_framework.serializers import DCFModelSerializer
    from django.db.models import CharField

    class Product(DCFModel, Serializable):
        barcode = CharField(max_length=32)

        @classmethod
        def get_serializer_class(cls, version, context):
            return ProductSerializer

    class ProductSerializer(DCFModelSerializer):
        class Meta:
            model = Product
            fields = ["id", "type", "created_at", "barcode"]


Now you can run migration to apply the new model.

.. code-block:: bash

    python3 ./manage.py makemigrations
    python3 ./manage.py migrate



Make an AccessControlled model
------------------------------

Django Client Framework supports both model and object level authorizations. By
default, all objects are only readable and writable only to superusers. Next, we
will give the read permission to the anyone user group, so that the product list
is publically visible to anyone visiting our site.

To manage model permission, ``Product`` needs to extend the ``AccessControlled``
class, and overrides a class method named ``.get_permissionmanager_class()``. The
``.get_permissionmanager_class()`` class method should return a
``PermissionManager`` class that implements a method named ``.add_perms(instance)``.
The default implementation of ``.get_permissionmanager_class()`` looks for a class
named ``PermissionManager`` in the model class.

To give anyone the read permission to the Product model, we import the
``default_groups.anyone`` and :ref:`add_perms_shortcut(...)
<add_perms_shortcut(...)>` from ``django_client_framework.permissions`` and use
them to set the permissions.

.. code-block:: py

    from django_client_framework.models import DCFModel, Serializable, AccessControlled
    from django_client_framework.serializers import DCFModelSerializer
    from django_client_framework.permissions import default_groups, add_perms_shortcut
    from django.db.models import CharField


    class Product(DCFModel, Serializable, AccessControlled):
        barcode = CharField(max_length=32)

        @classmethod
        def get_serializer_class(cls, version, context):
            return ProductSerializer

        class PermissionManager(AccessControlled.PermissionManager):
            def add_perms(self, product):
                add_perms_shortcut(default_groups.anyone, product, "r")


    class ProductSerializer(DCFModelSerializer):
        class Meta:
            model = Product
            fields = ["id", "type", "created_at", "barcode"]


Now to refresh the permission stored in the database, run this in Django shell:

.. code-block:: bash

    python3 ./manage.py shell

.. code-block:: py

    # inside shell

    from django_client_framework.permissions import reset_permissions

    reset_permissions()

.. note::

    Consider running ``reset_permissions()`` after the django migrations.


Query objects via HTTP requests
-------------------------------

We need to expose the ``Product`` model to the REST API by using the
``@register_api_model`` decorator. Add ``@register_api_model`` to the `Product`
class.


.. code-block:: py

    from django_client_framework.models import Serializable, AccessControlled
    from django_client_framework.serializers import DCFModelSerializer
    from django_client_framework.permissions import default_groups, add_perms_shortcut
    from django.db.models import CharField
    from django_client_framework.api import register_api_model

    @register_api_model
    class Product(Serializable, AccessControlled):
        barcode = CharField(max_length=32)

        @classmethod
        def get_serializer_class(cls, version, context):
            return ProductSerializer

        class PermissionManager(AccessControlled.PermissionManager):
            def add_perms(self, product):
                add_perms_shortcut(default_groups.anyone, product, "r")


    class ProductSerializer(DCFModelSerializer):
        class Meta:
            model = Product
            fields = ["id", "type", "created_at", "barcode"]


Now that the ``Product`` model is correctly configured, you can create a
``Product`` object in Django and visit in via the REST API.

.. code-block:: bash

    python3 ./manage.py shell

.. code-block:: py

    # inside shell
    from .product import Product

    Product.objects.create(barcode="xxyy")


Start the django development server:

.. code-block:: bash

    python3 ./manage.py runserver # Starting development server at http://127.0.0.1:8000/


To visit the list of products, send a GET request to this url:

.. code-block:: bash

    curl http://localhost:8000/product/

    #   {
    #       pages_count: 1,
    #       objects_count: 1,
    #       limit: 50,
    #       page: 1,
    #       objects: [ {id: "...", barcode: "xxyy"} ],
    #   }

To visit the specific product, send a GET request to this url:

.. code-block:: bash

    curl http://localhost:8000/product/<id>

    # {id: "...", barcode: "xxyy"}


.. seealso::

    Besides retrieving the object, creation, deleting, and modifications are
    also supported through POST, DELETE, PUT REST requests respectively.


Query relational objects via HTTP
---------------------------------

The Django model system allows you to define relational data. For instance, we
can add the ``Brand`` class in Django. A brand can have multiple products.
Conversely, a product is made by one brand.

Therefore, we define the two classes as follows:


.. code-block:: py

    from django_client_framework.models import DCFModel, Serializable, AccessControlled
    from django_client_framework.serializers import DCFModelSerializer
    from django_client_framework.permissions import default_groups, add_perms_shortcut
    from django_client_framework.api import register_api_model
    from django.db.models import CharField, ForeignKey, CASCADE


    @register_api_model
    class Brand(DCFModel, Serializable, AccessControlled):
        name = CharField(max_length=16)

        @classmethod
        def get_serializer_class(cls, version, context):
            return BrandSerializer

        class PermissionManager(AccessControlled.PermissionManager):
            def add_perms(self, brand):
                add_perms_shortcut(default_groups.anyone, brand, "r")


    class BrandSerializer(DCFModelSerializer):
        class Meta:
            model = Brand
            fields = ["id", "type", "created_at", "name"]


    @register_api_model
    class Product(Serializable, AccessControlled):
        barcode = CharField(max_length=32)
        brand = ForeignKey("Brand", related_name="products", on_delete=CASCADE, null=True)

        @classmethod
        def get_serializer_class(cls, version, context):
            return ProductSerializer

        class PermissionManager(AccessControlled.PermissionManager):
            def add_perms(self, product):
                add_perms_shortcut(default_groups.anyone, product, "r")


    class ProductSerializer(DCFModelSerializer):
        class Meta:
            model = Product
            fields = ["id", "type", "created_at", "barcode", "brand_id"]


After applying migrations, add a ``Product`` object, and a ``Brand`` object:

.. code-block:: py

    nike = Brand.objects.create(name="nike")
    Product.objects.create(barcode="xxyy", brand=nike)

Now to retrieve the ``Product`` object, send a GET request:

.. code-block:: bash

    curl http://localhost:8000/product/<id>
    # {id: "...", barcode: "xxyy", brand_id: "..."}


Now to query the product's brand, send a GET request to this url:

.. code-block:: bash

    curl http://localhost:8000/product/<id>/brand
    # {id: "...", name: "nike"}


.. note::

    The above query is the same as the query below, which returns the same brand
    object.

    .. code-block:: bash

        curl http://localhost:8000/brand/<brand-id>
        # {id: "...", name: "nike"}


Conversely, we can retrieve all products of the brand:

.. code-block:: bash

    curl http://localhost:8000/brand/<brand-id>/products

    #   {
    #       pages_count: 1,
    #       objects_count: 1,
    #       limit: 50,
    #       page: 1,
    #       objects: [ {id: "...", barcode: "xxyy"} ],
    #       next:null,
    #       previous:null
    #   }

.. warning::

    The last part of the url, ``/products``, comes from the
    ``related_name="products"`` argument when defining the brand `ForeignKey`
    field on ``Product``. This is the same ``.related_name`` in Django that allows
    you to write

    .. code-block:: py

        Brand.objects.filter(products__in=[...])
