from __future__ import annotations

from typing import Generic, TypeVar

from django.contrib.auth.models import AbstractUser as DjangoAbstractUser

from .model import AbstractDCFModel, DCFModel

T = TypeVar("T", bound=DCFModel)


class DCFAbstractUser(AbstractDCFModel[T], DjangoAbstractUser, Generic[T]):
    class Meta:
        abstract = True

    @classmethod
    def get_anonymous(cls) -> T:
        raise NotImplementedError()
