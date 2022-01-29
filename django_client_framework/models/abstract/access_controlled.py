from __future__ import annotations

from abc import abstractmethod
from logging import getLogger
from typing import Any, Generic, Type, TypeVar, cast

from django.db.models import Model as DjangoModel
from django.db.models.manager import BaseManager
from django.db.models.signals import post_save

from django_client_framework.models.abstract.model import DCFModel, IDCFModel

LOG = getLogger(__name__)


T = TypeVar("T", bound="DCFModel")
_T = TypeVar("_T", bound="DCFModel")


class IAccessControlled(IDCFModel[DCFModel], Generic[T]):
    @abstractmethod
    def update_perms(self) -> None:
        ...

    @classmethod
    def get_permissionmanager_class(cls) -> Type[Any]:
        ...


class AccessControlled(DjangoModel, IAccessControlled[T]):
    class Meta:
        abstract = True

    objects: BaseManager[T]

    class PermissionManager(Generic[_T]):
        def add_perms(self, instance: _T) -> None:
            raise NotImplementedError()

        def reset_perms(self, instance: _T) -> None:
            from ..object_permissions import UserObjectPermission

            UserObjectPermission.objects.filter(
                permission__model_name=instance._meta.model_name,
                permission__app_name=instance._meta.app_label,
                object_pk=instance.pk,
            ).delete()
            self.add_perms(instance)

    @classmethod
    def get_permissionmanager_class(cls) -> Type[PermissionManager]:
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

    def update_perms(self) -> None:
        self.get_permissionmanager_class()().reset_perms(self)

    def __init_subclass__(cls) -> None:
        post_save.connect(
            update_permission_on_change,
            sender=cls,
            dispatch_uid=f"{cls.__name__}.update_permission_on_change",
        )
        return super().__init_subclass__()


def update_permission_on_change(
    sender: Any, instance: IAccessControlled, **kwargs: Any
) -> None:
    instance.get_permissionmanager_class()().reset_perms(instance=instance)


def check_integrity() -> None:
    for model in AccessControlled.__subclasses__():
        model.get_permissionmanager_class()
