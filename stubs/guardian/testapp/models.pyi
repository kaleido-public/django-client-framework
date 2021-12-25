from typing import Any

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import AbstractBaseUser, AbstractUser
from django.db import models
from guardian.mixins import GuardianUserMixin as GuardianUserMixin
from guardian.models import GroupObjectPermissionBase as GroupObjectPermissionBase
from guardian.models import UserObjectPermissionBase as UserObjectPermissionBase

class Post(models.Model):
    title: Any

class DynamicAccessor:
    def __init__(self) -> None: ...
    def __getattr__(self, key): ...

class ProjectUserObjectPermission(UserObjectPermissionBase):
    content_object: Any

class ProjectGroupObjectPermission(GroupObjectPermissionBase):
    content_object: Any

class Project(models.Model):
    name: Any
    created_at: Any
    class Meta:
        get_latest_by: str

class MixedGroupObjectPermission(GroupObjectPermissionBase):
    content_object: Any

class Mixed(models.Model):
    name: Any

class ReverseMixedUserObjectPermission(UserObjectPermissionBase):
    content_object: Any

class ReverseMixed(models.Model):
    name: Any

class LogEntryWithGroup(LogEntry):
    group: Any
    objects: Any

class CharPKModel(models.Model):
    char_pk: Any

class UUIDPKModel(models.Model):
    uuid_pk: Any

class CustomUser(AbstractUser, GuardianUserMixin):
    custom_id: Any

class CustomUsernameUser(AbstractBaseUser, GuardianUserMixin):
    email: Any
    USERNAME_FIELD: str
    def get_full_name(self): ...
    def get_short_name(self): ...

class ParentTestModel(models.Model):
    created_on: Any

class ChildTestModel(ParentTestModel):
    parent_id: Any
    name: Any
