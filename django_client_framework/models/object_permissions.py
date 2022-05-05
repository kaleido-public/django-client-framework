from __future__ import annotations

from functools import cached_property
from typing import *

from django.apps import apps
from django.conf import settings
from django.db import models as m
from django.utils.translation import gettext_lazy as _

from .abstract import DCFModel


class DCFPermission(DCFModel):
    app_name = m.CharField(max_length=32)
    model_name = m.CharField(max_length=32)
    action = m.CharField(max_length=32)
    field_name = m.CharField(max_length=32, null=True)

    class Meta:
        constraints = [
            m.UniqueConstraint(
                fields=["model_name", "action", "field_name"],
                name="Make sure no duplicated permission entry is saved.",
            ),
        ]


class UserGroup(DCFModel):
    name = m.CharField(max_length=32, unique=True)
    model_permissions = m.ManyToManyField(DCFPermission)


class BaseGenericObjectPermission(DCFModel):
    class Meta:
        abstract = True

    object_pk = m.UUIDField(_("object ID"))
    permission = m.ForeignKey(DCFPermission, on_delete=m.CASCADE)

    @cached_property
    def content_object(self) -> Any:
        p = self.permission
        model = apps.get_model(f"{p.app_name}.{p.model_name}")
        return m.QuerySet(model=model).get(pk=self.object_pk)


class UserObjectPermission(BaseGenericObjectPermission):
    user = m.ForeignKey(settings.AUTH_USER_MODEL, on_delete=m.CASCADE)

    class Meta:
        constraints = [
            m.UniqueConstraint(
                fields=["user", "permission", "object_pk"],
                name="Make sure no duplicated user object permission entry is saved.",
            ),
        ]


class GroupObjectPermission(BaseGenericObjectPermission):
    group = m.ForeignKey(UserGroup, on_delete=m.CASCADE)

    class Meta:
        constraints = [
            m.UniqueConstraint(
                fields=["group", "permission", "object_pk"],
                name="Make sure no duplicated group object permission entry is saved.",
            ),
        ]
