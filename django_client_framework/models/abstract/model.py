from __future__ import annotations

import base64
from abc import abstractmethod
from typing import (  # type:ignore
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    _ProtocolMeta,
    cast,
)
from uuid import UUID, uuid4

from django.db.models import Model as DjangoModel
from django.db.models.base import ModelBase
from django.db.models.fields import DateTimeField, UUIDField
from django.db.models.manager import BaseManager
from django.db.models.options import Options


T = TypeVar("T", bound="DjangoModel")


class IDCFModel(Generic[T]):
    id: UUIDField
    created_at: DateTimeField
    objects: BaseManager[T]
    _meta: Options[T]
    pk: UUID

    @abstractmethod
    def delete(
        self, using: Any = ..., keep_parents: bool = ...
    ) -> Tuple[int, Dict[str, int]]:
        ...

    @abstractmethod
    def save(
        self,
        force_insert: bool = ...,
        force_update: bool = ...,
        using: Optional[str] = ...,
        update_fields: Optional[Iterable[str]] = ...,
    ) -> None:
        ...

    @abstractmethod
    def refresh_from_db1(
        self: IDCFModel, using: Optional[str] = ..., fields: Optional[List[str]] = ...
    ) -> None:
        ...

    def as_model(self) -> T:
        return cast(T, self)

    @classmethod
    def as_model_type(cls) -> Type[T]:
        return cast(Type[T], cls)


class __implements__:
    """This class doesn't do anything, it is for code redability. The class
    immediately next to implements is the interface implemented by this
    class."""


class DCFModel(DjangoModel, __implements__, IDCFModel[T]):
    class Meta:
        abstract = True

    objects: BaseManager[T]
    id = UUIDField(unique=True, primary_key=True, default=uuid4, editable=False)
    created_at = DateTimeField(auto_now_add=True)

    @classmethod
    def from_model(cls, model: T) -> DCFModel[T]:
        assert isinstance(model, DCFModel)
        return model

    @classmethod
    def from_model_type(cls, model: Type[T]) -> Type[DCFModel[T]]:
        assert issubclass(model, DCFModel)
        return model


def b64str_to_uuid(id: str) -> UUID:
    id += "=" * (4 - (len(id) % 4))
    return UUID(bytes=base64.urlsafe_b64decode(id))


def uuid_to_b64str(id: UUID) -> str:
    return base64.urlsafe_b64encode(id.bytes).decode("utf-8").rstrip("=")
