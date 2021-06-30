.. code-block:: py

    import django_client_framework.api.urls

This module defines a global constant ``urlpatterns``.

.. _urlpatterns:

`const` urlpatterns
=========================

    This global constant contains the routing handlers for models' RESTful APIs. You
    can include ``django_client_framework.api.urls`` to your custom ``urlpatterns``
    in any ``urls.py`` file. Then the handlers will become available with your
    custom prefix.

**Example**

.. code-block:: py

    import django_client_framework.api.urls
    from django.urls import path, include

    app_name = "myapp"

    urlpatterns = [
        path("login", v.PasswordLogin.as_view(), name="passwd_login"),
        path("logout", v.Logout.as_view(), name="logout"),
        path("", include(django_client_framework.api.urls)),
    ]
