from __future__ import annotations

from typing import Type, TypeVar

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.db.models import CharField, EmailField, ManyToManyField
from django.db.models.options import Options
from django.utils.translation import gettext_lazy as _

from ..object_permissions import DCFPermission, UserGroup
from .model import IDCFModel, __implements__

T = TypeVar("T", bound="DCFAbstractUser")


class DCFAbstractUser(AbstractBaseUser, __implements__, IDCFModel[T]):
    class Meta:
        abstract = True

    _meta: Options[T]  # type: ignore
    model_permissions = ManyToManyField(DCFPermission)
    groups = ManyToManyField(UserGroup)

    username = CharField(_("username"), max_length=64, blank=False, unique=True)
    email = EmailField(_("email address"), blank=True)

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"

    @classmethod
    def get_anonymous(cls) -> T:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.pk}>"

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.pk}>"


def get_dcf_user_model() -> Type[DCFAbstractUser]:
    return apps.get_model(settings.AUTH_USER_MODEL, require_ready=False)


def get_user_model() -> Type[DCFAbstractUser]:
    return get_dcf_user_model()  # type: ignore
