.. _add_perms_shortcut:

`func` add_perms_shortcut `(user_or_group, model_or_instance_or_queryset, perms, field_name=None)`
========================================================================================================

    .. code-block:: py

        from django_client_framework.permissions import add_perms_shortcut

    Gives user/group permission for a model/object, or a particular property on the
    model/object.

    Paramenters
        user_or_group
            A ``User`` or a ``Group`` object to give permissions to.

        model_or_instance_or_queryset
            Accepts a model class, or an instance or a queryset of the model.

        perms
            A string representing the permissions, eg, ``"rwcd"``
                :``r``: read - allows ``GET``
                :``w``: write - allows ``PATCH``
                :``c``: create - allows ``POST``, ``PUT``
                :``d``: delete - allows ``DELETE``

        field_name `=None`
            Accepts a property named that's defined on the model. If this argument
            is present, then the permission is for the model/object field. Otherwise
            the permission is applied to the model/object.

    .. seealso::
        See defails about :ref:`permission-concepts-and-management`.


.. _has_perms_shortcut:

`func` has_perms_shortcut `(user_or_group, model_or_instance, perms, field_name=None ) -> bool`
===========================================================================================================================

    .. code-block:: py

        from django_client_framework.permissions import has_perms_shortcut

    Checks if the user/group has a particular model/object/field permission.
    Agnostic to `add_perms_shortcut(...)`_. This function respects the inclusion of
    permissions, ie `model > object > model field > object field`. Also take into
    account the permissions assigned on the ``default_groups.anyone`` group.

    Paramenters
        user_or_group
            A ``User`` or a ``Group`` object to check permissions for.

        model_or_instance
            Accepts a model class, or an instance or a queryset of the model.

        perms
            A string representing the permissions, eg, ``"rwcd"``

        field_name `=None`
            If supplied, checks for the field permission.

    Returns
        True if the user has the permission, otherwise False.

    .. seealso::
        See defails about :ref:`permission-concepts-and-management`.


.. _reset_permissions:

`func` reset_permissions `()`
===================================

    .. code-block:: py

        from django_client_framework.permissions import reset_permissions

    Clears all permissions assigned in the application, and for each model that is a
    subclass of `AccessControlled`_, set up the permissions by calling
    ``PermissionManager.reset_perms()``.

    When ever the permission structure changes in your application, you need to call
    this function manually, or automatically in a django data migration.
