from __future__ import annotations

from typing import ClassVar, Generic, TypeVar

from django.db.models import Model as DjangoModel
from django.db.models.manager import Manager

T = TypeVar("T", bound="DjangoModel", covariant=True)


class DCFModel(Generic[T], DjangoModel):
    class Meta:
        abstract = True

    objects: ClassVar[Manager[T]]
    id: int


Model = DCFModel
