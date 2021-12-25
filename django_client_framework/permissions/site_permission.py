from __future__ import annotations

from logging import getLogger
from typing import (
    Any,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    cast,
    overload,
)

from deprecation import deprecated
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models as m
from django.db import transaction
from django.db.models.base import Model, ModelBase
from django.db.models.query import QuerySet
from guardian import models as gm
from guardian import shortcuts as gs

from django_client_framework.models import get_user_model
from django_client_framework.models.abstract.model import DCFModel

from ..models.abstract.access_controlled import AccessControlled
from .default_groups import default_groups

LOG = getLogger(__name__)

T = TypeVar("T", bound=Model)


@overload
def get_permission_for_model(
    shortcut: str,
    model: Type[Model],
    *,
    string: Literal[True],
    field_name: str | None,
) -> str:
    ...


@overload
def get_permission_for_model(
    shortcut: str,
    model: Type[Model],
    *,
    string: Literal[False],
    field_name: str | None,
) -> Permission:
    ...


def get_permission_for_model(
    shortcut: str,
    model: Type[Model],
    *,
    string: bool,
    field_name: Optional[str],
) -> str | Permission:
    """
    Returns permission object for model and field.
    If string is True, then returns the Permission object's full codename as string.
    """
    action_shortcuts = {
        "r": "view",
        "w": "change",
        "c": "add",
        "d": "delete",
    }
    action = action_shortcuts[shortcut]
    c = ContentType.objects.get_for_model(model, for_concrete_model=False)
    if field_name:
        if not model._meta.get_field(field_name):
            raise AttributeError(
                f'field named "{field_name}" not found on model {model}'
            )
        p, _created = Permission.objects.get_or_create(
            content_type=c, codename=f"{action}_{model._meta.model_name}__{field_name}"
        )
    else:
        p, _created = Permission.objects.get_or_create(
            content_type=c, codename=f"{action}_{model._meta.model_name}"
        )
    if string:
        return f"{c.app_label}.{p.codename}"
    else:
        return p


def filter_queryset_by_perms_shortcut(
    perms: str,
    user_or_group: AbstractUser | Group,
    queryset: QuerySet[T],
    field_name: str | None = None,
) -> QuerySet[T]:
    r"""
    Filters queryset by keeping objects that user_or_group has all permissions
    specified by perms. If field_name is specified, additionally include objects
    that user_or_group has field permission on.

    Algorithm:
        perms: rwcd \in {0,1}^4
        with/no field: f \in {0,1}
        normal/anyone user: u \in {0,1}
        A0 = filter with rwcd mask, f=0
        A1 = filter with rwcd mask, f=1
        B0 = A0 union A1, g=0
        B1 = A0 union A1, g=1
        B0 union B1
    """
    union = queryset.none()
    for u in set([user_or_group, default_groups.anyone]):  # B
        for f in set([None, field_name]):  # A
            perm_full_strs = [
                get_permission_for_model(s, queryset.model, string=True, field_name=f)
                for s in perms.lower()
            ]
            fn: Any = (
                gs.get_objects_for_group
                if isinstance(u, Group)
                else gs.get_objects_for_user
            )
            union |= fn(
                u,
                perms=perm_full_strs,
                accept_global_perms=True,
                any_perm=False,
                klass=queryset,  # filter
            )
    return union


def add_perms_shortcut(
    user_or_group: AbstractUser | Group,
    model_or_instance_or_queryset: Type[Model] | Model | QuerySet,
    perms: str,
    field_name: Optional[str] = None,
) -> None:
    """
    Adds model or object permission depending on whether model_or_instance_or_queryset
    is a model.
    """
    LOG.debug(f"{user_or_group=} {model_or_instance_or_queryset=} {perms=}")
    instance: Any
    if isinstance(model_or_instance_or_queryset, m.Model):
        instance = model_or_instance_or_queryset
        model = instance.__class__
    elif isinstance(model_or_instance_or_queryset, QuerySet):
        instance = model_or_instance_or_queryset
        model = model_or_instance_or_queryset.model
    elif model_or_instance_or_queryset.__class__ is ModelBase:
        instance = None
        model = model_or_instance_or_queryset
    else:
        raise TypeError(
            f"model_or_instance_or_queryset has wrong type: {type(model_or_instance_or_queryset)}"
        )
    for s in perms.lower():
        permstr = get_permission_for_model(s, model, string=True, field_name=field_name)
        gs.assign_perm(permstr, user_or_group, obj=instance)


@deprecated(details="use add_perms_shortcut(...) instead")
def set_perms_shortcut(
    user_or_group: AbstractUser | Group,
    model_or_instance_or_queryset: Type[Model] | Model | QuerySet,
    perms: str,
    field_name: Optional[str] = None,
) -> None:
    return add_perms_shortcut(
        user_or_group, model_or_instance_or_queryset, perms, field_name
    )


def has_perms_shortcut(
    user_or_group: AbstractUser | Group,
    model_or_instance: Type[Model] | Model,
    perms: str,
    field_name: Optional[str] = None,
) -> bool:
    """
    Check if user has all permissions as indicated by perms. For example, when
    perms="rw", returns True only if the user has both read and write
    permissions. Model permission > object permission > field permission.
    """
    User = cast(Type[AbstractUser], get_user_model())

    instance: Any
    if isinstance(model_or_instance, m.Model):
        instance = model_or_instance
        model = instance._meta.model
    elif model_or_instance.__class__ is ModelBase:
        instance = None
        model = model_or_instance
    else:
        raise TypeError(f"model_or_instance has wrong type: {type(model_or_instance)}")

    if isinstance(user_or_group, User) and user_or_group.is_superuser:
        return True

    def disjunction(s: str) -> Iterator[bool]:
        for u in set([default_groups.anyone, user_or_group]):
            for f in set([None, field_name]):
                perm = get_permission_for_model(s, model, string=False, field_name=f)
                if isinstance(u, Group):
                    # check group model permission
                    if u.permissions.filter(pk=perm.pk).exists():
                        yield True
                    # check group object permission
                    if (
                        instance
                        and gm.GroupObjectPermission.objects.filter(
                            group=u,
                            permission=perm,
                            content_type=perm.content_type,
                            object_pk=instance.pk,
                        ).exists()
                    ):
                        yield True
                else:
                    # check user model permission
                    name = f"{perm.content_type.app_label}.{perm.codename}"
                    if u.has_perm(name):
                        yield True
                    # check user object permission
                    if u.has_perm(name, instance):
                        yield True
        yield False

    def conjunction() -> Iterator[bool]:
        for s in perms.lower():
            if any(disjunction(s)):
                yield True
            else:
                yield False

    return all(conjunction())


def clear_permissions():
    LOG.info("clearing permissions...")
    with transaction.atomic():
        Permission.objects.all().delete()
        gm.UserObjectPermission.objects.all().delete()
        gm.GroupObjectPermission.objects.all().delete()
        # We need the logged_in group to survive migration, otherwise users who are using
        # the site when the migration happens would see permission errors after migration.
        Group.objects.exclude(m.Q(name="anyone") | m.Q(name="logged_in")).delete()


def reset_permissions(
    for_classes: List[
        Type["AccessControlled[Any]"]
    ] = AccessControlled.__subclasses__(),
) -> None:
    # set user self permission
    # must be done after all default users are added
    total_model_count = len(for_classes)
    current_model_count = 0
    for model in for_classes:
        current_model_count += 1
        LOG.warn(f"Resetting permissions for model {model.__name__}")
        total = model.objects.count()
        current = 0
        for instance in cast(
            Iterable[AccessControlled[Any]],
            model.objects.all(),
        ):
            current += 1
            percentage = current * 100 / total
            LOG.info(
                f"{current_model_count}/{total_model_count} {model.__name__}({instance.id}) %{percentage:.2f}"
            )
            with transaction.atomic():
                instance.update_perms()
