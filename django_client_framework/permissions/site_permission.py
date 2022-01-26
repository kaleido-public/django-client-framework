from __future__ import annotations

from functools import reduce
from logging import getLogger
from operator import concat
from typing import Any, Iterable, List, Optional, Sequence, Type, TypeVar, cast

from deprecation import deprecated
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models as m
from django.db import transaction
from django.db.models.base import ModelBase
from django.db.models.query import QuerySet

from django_client_framework.models.abstract.model import DCFModel, IDCFModel

from ..models import AccessControlled, GroupObjectPermission, UserObjectPermission
from .groups import default_groups

LOG = getLogger(__name__)

T = TypeVar("T", bound=IDCFModel)
M = TypeVar("M", bound=DCFModel)


def get_permission_for_model(
    shortcut: str,
    model: Type[m.Model],
    *,
    field_name: str | None,
) -> Permission:
    """
    Returns permission object for model and field.
    """
    action_shortcuts = {
        "r": "read",
        "w": "write",
        "c": "create",
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
            content_type=c, codename=f"{action}_{model._meta.model_name}_{field_name}"
        )
    else:
        p, _created = Permission.objects.get_or_create(
            content_type=c, codename=f"{action}_{model._meta.model_name}"
        )
    return p


def filter_queryset_by_perms_shortcut(
    perms: str,
    identity: AbstractUser | Group,
    queryset: QuerySet[M],
    field_name: str | None = None,
) -> QuerySet[M]:
    """Filters queryset by keeping objects that identity has all
    permissions specified by perms. If field_name is specified, additionally
    include objects that identity has field permission on.

    How to visuaize this as a gragh problem: for instance, for group (user is
    analogous)

    There are 4 sets of nodes: groups objects (G), GroupObjectPermission objects
    (GOP), Permission objects (P), and model objects (O).

    Each node in GOP is connect to exactly one of the nodes in G, one of the
    nodes in O, and one of the nodes in P.

    To include model level permissions, edges betwwen (G,P), and edgets betwen
    (O,P) are allowed. Whenever there's an edge between (G,P), the edge's node
    in P is connected to all O nodes.

    A .filter() method can be viewed as finding the maximal subset of nodes by
    the connectivity to any other subset of nodes.

    Given an input containing a subset of G, and a subset of P, then a subset of
    GOP is determined.

    The goal is to find the maximal subset of O such each node is connected to
    every nodes in the input P nodes via one of the determined GOP nodes, or is
    directly connected to P.
    """
    required_permissions: List[List[Permission]] = []
    for s in perms:
        any_of = [get_permission_for_model(s, queryset.model, field_name=None)]
        if field_name is not None:
            any_of.append(
                get_permission_for_model(s, queryset.model, field_name=field_name)
            )
        required_permissions.append(any_of)

    if isinstance(identity, Group):
        return _filter_for_groups(
            required_permissions,
            Group.objects.filter(pk__in=[identity.pk, default_groups.anyone.pk]),
            queryset,
        )
    else:
        if _user_has_superpower(identity):
            return queryset
        qs_user = _filter_for_user(required_permissions, identity, queryset)
        qs_grp = _filter_for_groups(
            required_permissions,
            Group.objects.filter(
                pk__in=[
                    *identity.groups.values_list("pk", flat=True),
                    default_groups.anyone.pk,
                ]
            ),
            queryset,
        )
        return QuerySet(model=queryset.model).filter(
            id__in=qs_user.union(qs_grp).values_list("id", flat=True)
        )


def _filter_for_groups(
    required_perms: Sequence[Sequence[Permission]],
    groups: QuerySet[Group],
    queryset: QuerySet[M],
) -> QuerySet[M]:
    """Build a query for filtering by permission (in conjunctive normal
    form: disjunctive for the nested list, conjunctive for outer list) of
    the groups (disjunctive)."""
    gops = GroupObjectPermission.objects.filter(
        group__in=groups,
        permission__in=reduce(concat, required_perms),
    )  # shouldn't hit db
    check_gop = False
    for pls in required_perms:
        # if user has model level permission then remove the corresponding GOP.
        if groups.filter(permissions__in=pls).exists():
            gops = gops.exclude(permission__in=pls)  # shouldn't hit db
        else:
            check_gop = True
    if check_gop:
        # should hit db once for fetching gops
        return queryset.filter(groupobjectpermissions__in=gops)
    else:
        return queryset


def _filter_for_user(
    required_perms: Sequence[Sequence[Permission]],
    user: AbstractUser,
    queryset: QuerySet[M],
) -> QuerySet[M]:
    """Build a query for filtering by permission (in conjunctive normal
    form: disjunctive for the nested list, conjunctive for outer list) of
    the user."""
    uops = UserObjectPermission.objects.filter(
        user=user,
        permission__in=reduce(concat, required_perms),
    )  # shouldn't hit db
    check_gop = False
    for pls in required_perms:
        # if user has model level permission then remove the corresponding UOP.
        if user.user_permissions.filter(id__in=[p.id for p in pls]).exists():
            uops = uops.exclude(permission__in=pls)  # shouldn't hit db
        else:
            check_gop = True
    if check_gop:
        # should hit db once for fetching uops
        return queryset.filter(userobjectpermissions__in=uops)
    else:
        return queryset


def add_perms_shortcut(
    identity: AbstractUser | Group,
    instance: Type[m.Model] | m.Model | QuerySet,
    perms: str,
    field_name: Optional[str] = None,
) -> None:
    """
    Adds model or object permission depending on whether instance is a model.
    """
    model: Type[m.Model]
    if isinstance(instance, m.Model):
        model = instance._meta.model
        permissions = [
            get_permission_for_model(p, model, field_name=field_name) for p in perms
        ]
        _add_for_queryset(
            identity,
            queryset=QuerySet(model=model).filter(id=instance.pk),
            perms=permissions,
        )
    elif isinstance(instance, m.QuerySet):
        permissions = [
            get_permission_for_model(p, instance.model, field_name=field_name)
            for p in perms
        ]
        _add_for_queryset(
            identity,
            queryset=instance,
            perms=permissions,
        )
    elif isinstance(instance, ModelBase):
        model = instance  # type: ignore
        permissions = [
            get_permission_for_model(p, model, field_name=field_name) for p in perms
        ]
        _add_for_model(identity, permissions)
    else:
        raise TypeError(f"Unexpected type: {type(instance)}")


def _add_for_queryset(
    identity: AbstractUser | Group,
    queryset: QuerySet,
    perms: Iterable[Permission],
) -> None:
    if isinstance(identity, Group):
        GroupObjectPermission.objects.bulk_create(
            [
                GroupObjectPermission(
                    group=identity,
                    permission=p,
                    content_object=o,
                )
                for o in queryset
                for p in perms
            ],
            ignore_conflicts=True,
        )
    else:
        UserObjectPermission.objects.bulk_create(
            [
                UserObjectPermission(
                    user=identity,  # type:ignore
                    permission=p,
                    content_object=o,
                )
                for o in queryset
                for p in perms
            ],
            ignore_conflicts=True,
        )


def _add_for_model(
    identity: AbstractUser | Group,
    perms: Iterable[Permission],
) -> None:
    if isinstance(identity, Group):
        identity.permissions.add(*perms)
    else:
        identity.user_permissions.add(*perms)


@deprecated(details="use add_perms_shortcut(...) instead")
def set_perms_shortcut(
    identity: AbstractUser | Group,
    model_or_instance_or_queryset: Type[m.Model] | m.Model | QuerySet,
    perms: str,
    field_name: Optional[str] = None,
) -> None:
    return add_perms_shortcut(
        identity, model_or_instance_or_queryset, perms, field_name
    )


def has_perms_shortcut(
    identity: AbstractUser | Group,
    instance: Type[m.Model] | m.Model | QuerySet,
    perms: str,
    field_name: Optional[str] = None,
) -> bool:
    """
    Check if user has all permissions as indicated by perms. For example, when
    perms="rw", returns True only if the user has both read and write
    permissions. Model permission > object permission > field permission.
    """
    model: Type[m.Model]
    if isinstance(instance, ModelBase):
        model = instance  # type: ignore
    elif isinstance(instance, m.Model):
        model = instance._meta.model
    elif isinstance(instance, QuerySet):
        model = instance.model
    else:
        raise TypeError(instance)
    required_permissions: List[List[Permission]] = []
    for s in perms:
        any_of = [get_permission_for_model(s, model, field_name=None)]
        if field_name is not None:
            any_of.append(get_permission_for_model(s, model, field_name=field_name))
        required_permissions.append(any_of)

    if isinstance(instance, ModelBase):
        if isinstance(identity, AbstractUser):
            return (
                _user_has_superpower(identity)
                or _check_model_for_user(
                    identity,
                    required_permissions,
                )
                or _check_model_for_groups(
                    identity.groups.all(),
                    required_permissions,
                )
            )
        elif isinstance(identity, Group):
            return _check_model_for_groups(
                identity,
                required_permissions,
            )
        else:
            raise TypeError(identity)
    else:
        if isinstance(instance, QuerySet):
            input_queryset = instance
        elif isinstance(instance, m.Model):
            input_queryset = QuerySet(model=model).filter(pk=instance.pk)
        else:
            raise TypeError(instance)
        result_queryset = filter_queryset_by_perms_shortcut(
            perms,
            identity,
            input_queryset,
            field_name=field_name,
        )
        return input_queryset.count() == result_queryset.count()


def _user_has_superpower(user: AbstractUser) -> bool:
    return user.is_superuser and user.is_active


def _check_model_for_groups(
    group: Group | QuerySet[Group], perms: List[List[Permission]]
) -> bool:
    if isinstance(group, Group):
        return all([group.permissions.filter(pk__in=ps).exists() for ps in perms])
    else:
        return all([group.filter(permissions__in=ps).exists() for ps in perms])


def _check_model_for_user(user: AbstractUser, perms: List[List[Permission]]) -> bool:
    return all(
        [
            user.user_permissions.filter(id__in=[p.id for p in pls]).exists()
            for pls in perms
        ]
    )


def clear_permissions() -> None:
    LOG.info("clearing permissions...")
    with transaction.atomic():
        Permission.objects.all().delete()
        UserObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()
        # We need the logged_in group to survive migration, otherwise users who are using
        # the site when the migration happens would see permission errors after migration.
        Group.objects.exclude(m.Q(name="anyone") | m.Q(name="logged_in")).delete()


def reset_permissions(
    for_classes: List[Type["AccessControlled"]] = AccessControlled.__subclasses__(),
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
