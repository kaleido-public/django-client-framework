from __future__ import annotations

import base64
from typing import Any, ClassVar, Generic, TypeVar
from uuid import UUID, uuid4

from django.db.models import Model as DjangoModel
from django.db.models.base import ModelBase
from django.db.models.fields import DateTimeField, UUIDField
from django.db.models.manager import Manager
from django.db.models.options import Options


T = TypeVar("T", bound="DjangoModel")


class AbstractDCFModel(DjangoModel, Generic[T]):
    class Meta:
        abstract = True

    objects: ClassVar[Manager[DjangoModel]]
    id: UUIDField
    _meta: Options[T]


class DCFModel(AbstractDCFModel[T]):
    class Meta:
        abstract = True

    id = UUIDField(unique=True, primary_key=True, default=uuid4, editable=False)
    created_at = DateTimeField(auto_now_add=True)


def b64str_to_uuid(id: str) -> UUID:
    id += "=" * (4 - (len(id) % 4))
    return UUID(bytes=base64.urlsafe_b64decode(id))


def uuid_to_b64str(id: UUID) -> str:
    return base64.urlsafe_b64encode(id.bytes).decode("utf-8").rstrip("=")
