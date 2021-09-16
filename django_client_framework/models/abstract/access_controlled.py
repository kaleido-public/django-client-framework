from __future__ import annotations

from logging import getLogger
from typing import Any, Generic, Type, TypeVar, cast

from django.contrib.contenttypes.fields import GenericRelation
from guardian.models import UserObjectPermission

from .model import Model as DCFModel

LOG = getLogger(__name__)


T = TypeVar("T", bound="AccessControlled")
_T = TypeVar("_T", bound="DCFModel")


class AccessControlled(DCFModel):
    class Meta:
        abstract = True

    userobjectpermissions = GenericRelation(
        UserObjectPermission, object_id_field="object_pk"
    )

    class PermissionManager(Generic[_T]):
        def add_perms(self, instance: _T):
            raise NotImplementedError()

        def reset_perms(self, instance: _T):
            LOG.debug(f"resetting permission for {instance}")
            cast(Any, instance).userobjectpermissions.all().delete()
            self.add_perms(instance)

    @classmethod
    def get_permissionmanager_class(cls) -> Type[PermissionManager[T]]:
        """
        Returns an PermissionManager class. The default implementation looks for a class
        named PermissionManager in the current class.
        """
        manager = getattr(cls, "PermissionManager", None)
        if manager is None:
            raise NotImplementedError(
                f"{cls.__name__} does not define a nested class named PermissionManager."
            )
        if not issubclass(manager, AccessControlled.PermissionManager):
            raise NotImplementedError(
                f"{manager} should extend {AccessControlled.PermissionManager}"
            )
        if not hasattr(manager, "add_perms"):
            raise NotImplementedError(
                f"{manager} must implement add_perms(self, instance)"
            )

        return manager

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        self.get_permissionmanager_class()().reset_perms(self)
        return ret

    # def __init_subclass__(cls) -> None:
    #     post_save.connect(
    #         update_permission_on_change,
    #         sender=cls,
    #         dispatch_uid=f"{cls.__name__}.update_permission_on_change",
    #     )
    #     return super().__init_subclass__()

    @classmethod
    def register_signals(cls):
        pass

    #     for child in cls.__subclasses__():
    #         post_save.connect(
    #             update_permission_on_change,
    #             sender=child,
    #             dispatch_uid=f"{cls.__name__}.update_permission_on_change",
    #         )


def update_permission_on_change(sender, instance, **kwargs):
    instance.get_permissionmanager_class()().reset_perms(instance=instance)


def check_integrity():
    for model in AccessControlled.__subclasses__():
        model.get_permissionmanager_class()
