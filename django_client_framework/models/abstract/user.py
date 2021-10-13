from __future__ import annotations

from typing import Generic, TypeVar

from django.contrib.auth.models import AbstractUser as DjangoAbstractUser

from .model import DCFModel

T = TypeVar("T")


class DCFAbstractUser(DCFModel, DjangoAbstractUser, Generic[T]):
    class Meta:
        abstract = True

    def get_anonymous(self) -> T:
        raise NotImplementedError()


AbstractUser = DCFAbstractUser
