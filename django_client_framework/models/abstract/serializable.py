from __future__ import annotations

from abc import abstractmethod
from logging import getLogger
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    TypedDict,
    cast,
    Union,
)

from django.conf import settings
from django.core.cache import cache
from django.db import models as m

from .model import DCFModel, IDCFModel, __implements__

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from ...serializers.serializer import DCFSerializer


D = TypeVar("D")
T = TypeVar("T", bound="ISerializable")


class ISerializable(IDCFModel[DCFModel], Generic[T, D]):
    def to_serializable(self) -> Serializable[T, D]:
        return cast(Serializable[T, D], self)

    @classmethod
    @abstractmethod
    def get_serializer_class(
        cls, *, version: str, context: Dict[str, Any]
    ) -> Type[DCFSerializer[T, D]]:
        ...

    @abstractmethod
    def get_serializer(
        self, *, version: str, context: Dict[str, Any], **kwargs: Any
    ) -> DCFSerializer[T, D]:
        ...

    @abstractmethod
    def json(
        self,
        *,
        version: str,
        context: Dict[str, Any] = {},
        serializer: Optional[DCFSerializer[T, D]] = None,
        ignore_cache: bool = False,
    ) -> D:
        ...

    @abstractmethod
    def get_json(
        self,
        *,
        version: str,
        context: Dict[str, Any] = {},
        serializer: Optional[DCFSerializer[T, D]] = None,
    ) -> D:
        ...


class Serializable(__implements__, ISerializable[T, D]):
    @classmethod
    def get_serializer_class(
        cls, *, version: str, context: Dict[str, Any]
    ) -> Type[DCFSerializer[T, D]]:
        raise NotImplementedError(
            f"{cls} must implement .get_serializer_class(version, context)"
        )

    def get_serializer(
        self, *, version: str, context: Dict[str, Any], **kwargs: Any
    ) -> DCFSerializer[T, D]:
        return self.get_serializer_class(version=version, context=context)(
            instance=self, **kwargs
        )

    def json(
        self,
        *,
        version: str,
        context: Dict[str, Any] = {},
        serializer: Optional[DCFSerializer[T, D]] = None,
        ignore_cache: bool = False,
    ) -> D:
        if ignore_cache or self.get_cache_timeout() == 0:
            return self.get_json(
                version=version,
                context=context,
                serializer=serializer,
            )
        return self.cached_json(
            version=version,
            context=context,
            serializer=serializer,
        )

    def get_json(
        self: T,
        *,
        version: str,
        context: Dict[str, Any] = {},
        serializer: Optional[DCFSerializer[T, D]] = None,
    ) -> D:
        if serializer is None:
            serializer = self.get_serializer(version=version, context=context)
        return serializer.to_representation(instance=self)

    def get_extra_content_to_hash(self) -> List[Any]:
        return []

    def values(self):
        self._meta: Any
        return self._meta.model.objects.filter(pk=self.id).values().first()

    def __repr__(self):
        if settings.DEBUG:
            return f"<<{self.__class__.__name__}:{self.values()}>>"
        else:
            return f"<{self.__class__.__name__}:{self.id}>"

    def __str__(self):
        return f"<{self.__class__.__name__}:{self.id}>"

    def get_cache_timeout(self) -> int:
        """Return how long to cache the serialization in seconds"""
        return 0

    def cached_json(
        self,
        *,
        version: str,
        context: Dict[str, Any] = {},
        serializer: Optional[DCFSerializer[T, D]] = None,
    ) -> Any:
        timeout = self.get_cache_timeout()
        if timeout == 0:
            return self.get_json(
                version=version,
                context=context,
                serializer=serializer,
            )

        if result := cache.get(
            self.get_cache_key_for_serialization(version, context), None
        ):
            return result
        else:
            data = self.get_json(
                version=version,
                context=context,
                serializer=serializer,
            )
            cache.add(
                self.get_cache_key_for_serialization(version, context),
                data,
                timeout=timeout,
            )
            return data

    def get_cache_key_for_serialization(
        self, version: str, context: Dict[str, Any]
    ) -> str:
        # whenver one of the hashed content is changed, the cache misses, and a
        # re-serialization is forced.
        return "serialization_cache_" + str(
            hash(
                [self._meta.model_name, self.id, version, context]
                + self.get_extra_content_to_hash()
            )
        )


def check_integrity():
    from ...serializers import DelegateSerializer, Serializer

    for model in Serializable.__subclasses__():
        if model.__module__ == "__fake__":
            break
        if Serializable not in model.__bases__:
            break
        if m.Model not in model.__bases__:
            break
        i = model.__bases__.index(Serializable)
        j = model.__bases__.index(m.Model)
        if i > j:
            raise AssertionError(
                f"{model} must extend {Serializable} before {m.Model}, current order: {model.__bases__}"
            )

    for model in Serializable.__subclasses__():
        sercls: Type[Serializer] = model.get_serializer_class(
            version="default", context={}
        )
        if not (
            issubclass(sercls, Serializer) or issubclass(sercls, DelegateSerializer)
        ):
            raise NotImplementedError(
                f"{model}.get_serializer_class() does not return a Serialzer class "
            )
