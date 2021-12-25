from typing import Any

from django.db import models
from guardian.compat import user_model_label as user_model_label
from guardian.ctypes import get_content_type as get_content_type
from guardian.managers import (
    GroupObjectPermissionManager as GroupObjectPermissionManager,
)
from guardian.managers import UserObjectPermissionManager as UserObjectPermissionManager

class BaseObjectPermission(models.Model):
    permission: Any
    class Meta:
        abstract: bool
    def save(self, *args, **kwargs): ...

class BaseGenericObjectPermission(models.Model):
    content_type: Any
    object_pk: Any
    content_object: Any
    class Meta:
        abstract: bool
        indexes: Any

class UserObjectPermissionBase(BaseObjectPermission):
    user: Any
    objects: Any
    class Meta:
        abstract: bool
        unique_together: Any

class UserObjectPermissionAbstract(
    UserObjectPermissionBase, BaseGenericObjectPermission
):
    class Meta(UserObjectPermissionBase.Meta, BaseGenericObjectPermission.Meta):
        abstract: bool
        unique_together: Any

class UserObjectPermission(UserObjectPermissionAbstract):
    class Meta(UserObjectPermissionAbstract.Meta):
        abstract: bool

class GroupObjectPermissionBase(BaseObjectPermission):
    group: Any
    objects: Any
    class Meta:
        abstract: bool
        unique_together: Any

class GroupObjectPermissionAbstract(
    GroupObjectPermissionBase, BaseGenericObjectPermission
):
    class Meta(GroupObjectPermissionBase.Meta, BaseGenericObjectPermission.Meta):
        abstract: bool
        unique_together: Any

class GroupObjectPermission(GroupObjectPermissionAbstract):
    class Meta(GroupObjectPermissionAbstract.Meta):
        abstract: bool
