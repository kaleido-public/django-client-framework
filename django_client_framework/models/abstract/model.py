from __future__ import annotations

import base64
from abc import abstractmethod
from typing import *
from uuid import UUID, uuid4

from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Model as DjangoModel
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
    def refresh_from_db(
        self: IDCFModel, using: Optional[str] = ..., fields: Optional[List[str]] = ...
    ) -> None:
        ...

    def as_model(self) -> T:
        return self  # type:ignore

    @classmethod
    def as_model_type(cls) -> Type[T]:
        return cls  # type:ignore


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
    userobjectpermissions = GenericRelation(
        "django_client_framework.UserObjectPermission", object_id_field="object_pk"  # type: ignore
    )
    groupobjectpermissions = GenericRelation(
        "django_client_framework.GroupObjectPermission", object_id_field="object_pk"  # type: ignore
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.pk}>"

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.pk}>"

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
