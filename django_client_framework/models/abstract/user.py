from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from django.contrib.auth.models import AbstractUser as DjangoAbstractUser
from django.contrib.auth.models import UserManager
from django.db.models.options import Options

from .model import AbstractDCFModel

T = TypeVar("T", bound=DjangoAbstractUser)


class DCFUserManager(UserManager, Generic[T]):
    def create_user(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **extra_fields: Any,
    ) -> T:
        return super().create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

    def create_superuser(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **extra_fields: Any,
    ) -> T:
        return super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )


class DCFAbstractUser(AbstractDCFModel[T], DjangoAbstractUser, Generic[T]):
    class Meta:
        abstract = True

    objects: DCFUserManager[T]
    _meta: Options[T]  # type: ignore

    @classmethod
    def get_anonymous(cls) -> T:
        raise NotImplementedError()
