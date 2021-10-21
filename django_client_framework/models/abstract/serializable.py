from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Type, TypeVar

from django.conf import settings
from django.core.cache import cache
from django.db import models as m

from .model import DCFModel

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from ...serializers.serializer import DCFSerializer


T = TypeVar("T", bound=DCFModel)


class Serializable(DCFModel[T], Generic[T]):
    class Meta:
        abstract = True

    @classmethod
    def get_serializer_class(
        cls, version: str, context: Dict[str, Any]
    ) -> Type[DCFSerializer]:
        raise NotImplementedError(f"{cls} must implement .get_serializer_class()")

    def get_serializer(
        self, version: str, context: Dict[str, Any], **kwargs
    ) -> DCFSerializer[T]:
        return self.get_serializer_class(version, context)(instance=self, **kwargs)

    def json(
        self,
        *,
        version: str,
        context: Dict[str, Any] = {},
        serializer: DCFSerializer = None,
        ignore_cache=False,
    ) -> Any:
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
        self,
        *,
        version: str,
        context: Dict[str, Any] = {},
        serializer: DCFSerializer = None,
    ) -> Any:
        if serializer:
            return serializer.to_representation(self)
        else:
            return dict(self.get_serializer(version, context).data)

    def get_extra_content_to_hash(self) -> List[Any]:
        return []

    def values(self):
        return self.objects.filter(pk=self.id).values().first()

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
        version,
        context: Dict[str, Any] = {},
        serializer: DCFSerializer = None,
    ):
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
        sercls = model.get_serializer_class(version="default", context={})
        if not (
            issubclass(sercls, Serializer) or issubclass(sercls, DelegateSerializer)
        ):
            raise NotImplementedError(
                f"{model}.serializer_class() does not return a Serialzer class "
            )
