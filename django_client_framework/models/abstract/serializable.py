from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, Dict, Generic, Type, TypeVar

from django.conf import settings
from django.core.cache import cache
from django.db import models as m
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.functional import cached_property

from .model import Model as DCFModel

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from django_client_framework.serializers.serializer import DCFSerializer

T = TypeVar("T", bound=DCFModel, covariant=True)


class Serializable(Generic[T], DCFModel[T]):
    class Meta:
        abstract = True

    @classmethod
    def serializer_class(cls) -> Type[DCFSerializer]:
        raise NotImplementedError(f"{cls} must implement .serializer_class()")

    @cached_property
    def serializer(self) -> DCFSerializer[T]:
        return self.get_serializer()

    def get_serializer(self, **kwargs) -> DCFSerializer[T]:
        return self.serializer_class()(instance=self, **kwargs)

    def json(self, *, context: Dict[str, Any]) -> Any:
        return dict(self.get_serializer(context=context).data)

    def __repr__(self):
        if settings.DEBUG:
            return f"<<{self.__class__.__name__}:{self.serializer.data}>>"
        else:
            return f"<{self.__class__.__name__}:{self.pk}>"

    def __str__(self):
        return f"<{self.__class__.__name__}:{self.pk}>"

    def get_serialization_cache_timeout(self) -> int:
        """Return how long to cache the serialization in seconds"""
        return 0

    def cached_json(self, *, context: Dict[str, Any]):
        timeout = self.get_serialization_cache_timeout()
        if timeout == 0:
            return self.json(context=context)

        if result := cache.get(self.cache_key_for_serialization, None):
            return result
        else:
            data = self.json(context=context)
            cache.add(
                self.cache_key_for_serialization,
                data,
                timeout=timeout,
            )
            return data

    @cached_property
    def cache_key_for_serialization(self):
        return f"serialization_{self._meta.model_name}_{self.pk}"

    def invalidate_serialization_cache(self):
        cache.delete(self.cache_key_for_serialization)


@receiver(post_save)
def auto_invalidate_cached_serialization_post_save(sender, instance, created, **kwargs):
    if not created and isinstance(instance, Serializable):
        LOG.debug(f"invalidate cache for {instance}")
        instance.invalidate_serialization_cache()


@receiver(post_delete)
def auto_invalidate_cached_serialization_post_delete(sender, instance, **kwargs):
    if isinstance(instance, Serializable):
        LOG.debug(f"delete cache for {instance}")
        instance.invalidate_serialization_cache()


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
        sercls = model.serializer_class()
        if not (
            issubclass(sercls, Serializer) or issubclass(sercls, DelegateSerializer)
        ):
            raise NotImplementedError(
                f"{model}.serializer_class() does not return a Serialzer class "
            )
