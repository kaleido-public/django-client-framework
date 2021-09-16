from __future__ import annotations

from typing import Generic, TypeVar

from django.contrib.auth.models import AbstractUser as DjangoAbstractUser

T = TypeVar("T")


class DCFAbstractUser(Generic[T], DjangoAbstractUser):
    class Meta:
        abstract = True

    def get_anonymous(self) -> T:
        raise NotImplementedError()


AbstractUser = DCFAbstractUser
