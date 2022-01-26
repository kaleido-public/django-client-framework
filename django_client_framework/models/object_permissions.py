from __future__ import annotations

from typing import *

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils.translation import gettext_lazy as _

from .abstract import DCFModel

if TYPE_CHECKING:
    from .abstract.user import DCFAbstractUser
user_model_label: Type[DCFAbstractUser] = getattr(
    settings, "AUTH_USER_MODEL", "auth.User"
)

Permission.__repr__ = DCFModel.__repr__  # type:ignore
Permission.__str__ = DCFModel.__str__  # type:ignore


class BaseGenericObjectPermission(DCFModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_pk = models.UUIDField(_("object ID"))
    content_object = GenericForeignKey(fk_field="object_pk")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["content_type", "object_pk"]),
        ]


class UserObjectPermission(BaseGenericObjectPermission):
    user = models.ForeignKey(user_model_label, on_delete=models.CASCADE)

    class Meta:
        indexes = BaseGenericObjectPermission.Meta.indexes
        constraints = [
            UniqueConstraint(
                fields=["user", "permission", "content_type", "object_pk"],
                name="Make sure no duplicated user object permission entry is saved.",
            ),
        ]


class GroupObjectPermission(BaseGenericObjectPermission):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        indexes = BaseGenericObjectPermission.Meta.indexes
        constraints = [
            UniqueConstraint(
                fields=["group", "permission", "content_type", "object_pk"],
                name="Make sure no duplicated group object permission entry is saved.",
            ),
        ]
