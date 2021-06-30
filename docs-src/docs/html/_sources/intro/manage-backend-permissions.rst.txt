.. _Permission-Concepts-and-Management:

Permission Concepts and Management
==================================

Django Client Framework supports four levels of permissions: `model`, `object`,
`model field`, and `object field`. There are four types of permissions: `read`,
`write`, `create`, `delete`. The framework also supports `user` and `group`. A
user can be added to multiple groups. A permission can be given to a `user` or a
`group`. All users in a group obtain the permissions that are assigned to the
group. By default, all users and groups have no permissions assigned.

The framework uses a deterministic permission model. This means instead of
assigning user permissions dynamically as your web service runs, the permissions
are determined during django data migrations. You must design the permission
structure depending on the user and object relations.


Types of permissions
--------------------

There are four types of permissions: `read`, `write`, `create`, `delete`. These
permissions are checked when users access the RESTful API. In particular, when
accessing the model collection, the model object, and the related object APIs,
the permissions allow for the following HTTP methods:

    :read: ``GET``
    :write: ``PATCH``
    :create: ``POST`` and ``PUT``
    :delete: ``DELETE``


Levels of permissions
-----------------------

There are four levels of permissions: `model`, `object`, `model field`, and
`object field`. In terms of inclusion, ``model > object > model field > object
field``.

    Model permission
        When assigning permissions to a model, the permissions apply to all
        objects of the model class. For instance, you can assign the read
        permission for the ``Product`` class to the ``anyone`` group so that all
        products are readable to any user.

    Object permission
        When assigning permissions to an object, the permissions only affects
        the object but not the others. For instance, you can assign the write
        permission for a `User` object to itself, so that any user can modify
        their own personal data.

    Model field permission
        Instead of assigning permissions to a model, in which case the
        permissions apply to all fields on the model, you can also allow the
        permission on a particular field of the model. For instance, you may
        want to give user the read-only permission on a model, except for a
        particular field, which can be both read and written.

    Object field permission
        Similar to model field permission except the permission is assgined to
        one object instead of all.


Default users
-------------

The framework comes with a default user named `AnonymousUser`. This is a dummy
user object that's used to assign permissions to any anonymous user. The user
can be accessed by ``django_client_framework.permissions.default_users.anonymous``.

.. note::
    Since in most applications, the permissions for the anonymous user are most
    likely a subset of any other user, you should consider assigning the
    permissions to the ``default_groups.anyone`` group instead.

You can add custom default users that are required by your application using the
``@register_default_user`` decorator.


Default groups
--------------

The framework comes with a default group named `anyone`. This is a dummy group
object that includes all users, including the `anonymous` user. The user can be
accessed by ``django_client_framework.permissions.default_groups.anyone``.

You can also add custom default groups that are required by your application
using the ``@register_default_group`` decorator.


Example
    .. code-block:: py

        from .models import Product, User
        from django_client_framework.permissions import default_groups

        add_perms_shortcut(default_groups.anyone, Product, "r")

        user = m.User.objects.create(username="example_user")
        add_perms_shortcut(user, user, "r")
        add_perms_shortcut(user, user, "rw", "first_name")



Permissions for RESTful requests
-------------------------------------------

The permission system has the following designs:

    1. A ``PermissionDenied`` exception can be raised from anywhere of the
    application. A ``PermissionDenied`` exception can optionally include four
    attributes: the `model`, the `instance`, the `field`, and the `action`,
    depending on the context of what user is accessing. When ``DEBUG=False`` in
    ``settings.py``, if user's modification action raises ``PermissionDenied``
    and user has no ``read`` permission on the context, the server responds with
    a ``404 Not Found`` instead. This is for hiding the existence of an object
    whenever possible.

    .. code-block::

        handling PermissionDenied(model, instance, field, action):
            if settings.DEBUG is False:
                if instance is not None:
                    if user cannot read instance field:
                        raise NotFound(instance)
            raise original PermissionDenied exception


    2. When modifying a related object relation, (eg. modifying a `product`'s
    `brand`), the user must have the ``write`` permission for all the following
    three kinds of fields:

        * the relation field on the parent object (eg. the `product` instance's ``.brand`` field)
        * the reverse relation field of the old related object if not ``None`` (eg. the old `brand` instance's ``.products`` field, in order to remove the original relation)
        * the reverse relation field of the new related object if not ``None`` (eg. the new `brand` instance's ``.products`` field, in order to add the new relation)

    Similarly, when adding or removing objects in a relation collection, (eg.
    adding to or removing from a `brand`'s `products` set), the user must have
    the ``write`` permission for all the following three kinds of fields:

        * the relation field on the parent object (eg. the `brand` instance's ``.products`` field)
        * the reverse relation field of the old related objects (eg, the ``.brand`` field for every old `product` being removed from the `brand`'s ``.products`` set)
        * the reverse relation field of the new related objects (eg, the ``.brand`` field for every new `proudct` being added to the `brand`'s ``.products`` set)

The permission system affects the RESTful API request handlers. For each type of
requests, the handling algorithm is as the following:

**Collection API**, `eg, /product/`

    ``GET``
        When visiting a model collection, only objects that the authenticated
        user has permission to view are displayed. If the user has no ``read``
        permission on any object of the model, then the result is an empty list.

        .. code-block::

            for each object of the model:
                if user can read object:
                    include object in the page result
                else:
                    exclude object from the page result
                    include a message "some results are hidden"

            respond 200 OK with the filtered list of objects


    ``POST``
        When creating an object, the authenticated user must have the ``create``
        permission on the model class; otherwise, the server responses with a
        ``403 Permission Denied`` error. In addition, if the user has the
        ``read`` permission on the object created, then the server responses
        with the ``code 201`` and the created data; otherwise, the server
        responses with ``code 201`` and a message saying `the object is created
        but you have no permission to view it`.

        .. code-block::

            if user can create object:
                create object
                if user can read the created object:
                    respond 201 OK with the created object
                else:
                    respond 200 OK with message "the object is created but you have no permission to view it"
            else:
                raise PermissionDenied(model, "create")

**Object API**, `eg, /product/1`

    ``GET``
        When visiting a model object, the object is only displayed if the
        authenticated user has the `object-level` ``read`` permission.

        .. code-block::

            if user can read object:
                respond 200 OK with object
            else:
                raise PermissionDenied(object, "read")

    ``PATCH``
        When updating a model object, the authenticated user must have the
        `field-level` ``write`` permissions for each field that is modified.
        When the object is updated, if the user has the ``read`` permission,
        then the server responses with ``200 OK`` and the object data; otherwise
        the server responses with ``200 OK`` and a message saying `the object is
        updated but you have no permission to view it`.

        .. code-block::

            for each field being modified:
                if user can write to field:
                    if field is a relation:
                        raise FieldIsReadOnly(object, field)
                    else:
                        modify field
                else:
                    raise PermissionDenied(object, field, "write")
            if user can read object:
                respond 200 OK with updated object
            else:
                respond 200 OK with message "the object is updated but you have no permission to view it"



**Related Collection API**, `eg, /brand/1/products`

    ``GET``
        The authenticated user must have the `object-field-level` ``read``
        permission for the parent object (eg, being able to read the `brand`
        instance's ``.products`` field). Among the set of related objects, only
        the ones to which the user has the ``read`` permission are displayed.

        .. code-block::

            if user can read the relation field:
                for each related object:
                    if user can read the object:
                        include the object in the result
                    else:
                        exclude the object from the result
                respond 200 OK with the filtered list of result
            else:
                raise PermissionDenied(parent, field, "read")


    ``POST``
        The authenticated user must have the `object-field-level` ``write``
        permissions for the parent object (ie, being able to write to the
        brand's ``.products`` field). In addition, for each related objects
        being posted, the user must have the `object-field-level` ``write``
        permission on the reverse field. (eg, being able to write to each
        product's ``.brand`` field.) When the object relations are created, the
        result is displayed following the ``GET`` algorithm.

        .. code-block::

            if user can write to the relation field:
                for each related object to be posted:
                    if user can write to the reverse relation field:
                        create the relation
                    else:
                        raise PermissionDenied(related object, reverse field, "write")
            else:
                raise PermissionDenied(parent, field, "write")

    ``DELETE``
        This requires the same permissions as ``POST`` except the context is for
        deleting relations instead of creating.

        .. code-block::

            if user can write to the relation field:
                for each related object to be removed:
                    if user write to the reverse relation field:
                        remove the relation
                    else:
                        raise PermissionDenied(related object, reverse field, "write")
            else:
                raise PermissionDenied(parent, field, "write")


    ``PATCH``
        This is equivalent to ``DELETE`` and ``POST`` combined.

        .. code-block::

            if user can write to the relation field:
                for each related object deleted or posted:
                    if user write to the reverse relation field:
                        remove or create the relation
                    else:
                        raise PermissionDenied(related object, reverse field, "write")
            else:
                raise PermissionDenied(parent, field, "write")


**Related Object API**, `eg, /product/1/brand`

    ``GET``
        The authenticated user must have the `object-field-level` ``read``
        permission for the parent object (ie, being able to read the product
        instance's `.brand` field), as well as the `object-level` ``read``
        permission for the related object (ie, being able to read the `brand`
        object).

        .. code-block::

            if user can read the parent field:
                if user can read the related object:
                    respond 200 OK with data
                else:
                    raise PermissionDenied(related object, "read")
            else:
                raise PermissionDenied(parent, "read")


    ``PATCH``
        The authenticated user must have the `object-field` level ``write``
        permission for the parent object (ie, being able to write the
        `product`'s ``.brand`` field). In addition, for both the current and the
        new related object (unless ``None``), the user must have the
        `object-field` level ``write`` permission for the reverse field (ie,
        being able to write the current and the new `brand`'s ``.products``
        field).

        .. code-block::

            if user can write to the parent field:
                for both the current and the new related object:
                    if object object is not None:
                        if user can write to the reverse field:
                            create relation
                            if user can read the related object:
                                respond 200 OK with data
                            else:
                                respond 200 OK with message "the relation is updated but you have no permission to view it"
                        else:
                            raise PermissionDenied(related object, reverse field, "write")
            else:
                raise PermissionDenied(parent, field, "write")

