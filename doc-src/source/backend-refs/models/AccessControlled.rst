.. _AccessControlled:

`class` AccessControlled
============================

.. code-block:: py

    from django_client_framework.models import AccessControlled

This abstract model class provides the permission structure for its subclasses.

**Inheritance**

Subclasses of `AccessControlled`_ can optionally override the
`.get_permissionmanager_class(cls)` which returns a `AccessControlled.PermissionManager`_ class.


.. _AccessControlled.get_permissionmanager_class():

`classmethod` .get_permissionmanager_class `(cls)`
--------------------------------------------------------------
    :Returns: A subclass of `AccessControlled.PermissionManager` which
                defines the object permission.



.. _AccessControlled.PermissionManager:

`class` .PermissionManager
-------------------------------------

This is a nested class in `AccessControlled`_ whose subclasses should be
returned from `AccessControlled.get_permissionmanager_class()`_.

