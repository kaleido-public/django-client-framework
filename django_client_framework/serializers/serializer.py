from __future__ import annotations

from typing import *

from deprecation import deprecated
from rest_framework.serializers import Serializer as DRFSerializer
from rest_framework.serializers import empty

from ..models.abstract.model import IDCFModel
from ..models.abstract.serializable import D, Serializable, T

T1 = TypeVar("T1", bound=IDCFModel, covariant=True)
D1 = TypeVar("D1", covariant=True)


class IDCFSerializer(Generic[T1, D1]):
    def to_serializer(self) -> DCFSerializer:
        return cast(DCFSerializer, self)


class DCFSerializer(IDCFSerializer[T, D], DRFSerializer):
    # Every attribute / method in this class must also be added to the
    # DelegateSerializer, otherwise the DelegateSerializer breaks.

    instance: Optional[T]

    def __init__(
        self,
        instance: Optional[T] = None,
        data: Any = empty,
        many: bool = False,
        read_only: bool = False,
        partial: bool = False,
        source: Optional[str] = None,
        context: Any = {},
        prefer_cache: bool = False,
        locale: Optional[str] = None,
    ) -> None:
        super().__init__(
            instance=instance,
            data=data,
            many=many,
            read_only=read_only,
            source=source,  # type: ignore
            partial=partial,
            context=context,
        )
        self.prefer_cache = prefer_cache
        self.locale = locale or context.get("locale")
        context["locale"] = self.locale

    @deprecated(details="Use self.locale instead", deprecated_in="1.2.1")
    def get_locale(self) -> str | None:
        return self.context.get("locale")

    def update(self, instance: T, validated_data: Any) -> T:
        return super().update(instance, validated_data)

    def create(self, validated_data: Any) -> T:
        return super().create(validated_data)

    def save(self, **kwargs: Any) -> T:
        return super().save(**kwargs)

    def to_representation_cached(self, instance: T) -> D:
        if isinstance(instance, Serializable):
            return instance.cached_json(
                version=self.context.get("version"),
                context=self.context,
                # Forces Serializable to use this serialzer. If the cache
                # doesn't exist, .to_representation() will be called by
                # Serializable.
                serializer=self.__class__(
                    instance=cast(T, instance),
                    read_only=True,
                    prefer_cache=False,
                ),
            )
        if instance is None:
            return None
        raise TypeError(
            "Must be a Serializable instance when the serializer is initialized with prefer_cache=True."
        )

    def to_representation(self, instance: T) -> D:
        if self.prefer_cache:
            return self.to_representation_cached(instance)
        else:
            data = super().to_representation(instance)
            if self._get_deprecated() != {}:
                data["@deprecated"] = self._get_deprecated()
            for dk in self._get_deprecated().keys():
                if dk in data:
                    val = data.pop(dk)
                    data[dk + "@deprecated"] = val
            if "type" in data:
                data.move_to_end("type", last=False)
            if "id" in data:
                data.move_to_end("id", last=False)
            if "@deprecated" in data:
                data.move_to_end("@deprecated", last=True)
            return data

    def delete(self, instance: T) -> None:
        instance.delete()

    def create_obj(self) -> T:
        assert self.validated_data is not None
        return self.create(self.validated_data)

    def update_obj(self) -> T:
        assert self.instance is not None
        assert self.validated_data is not None
        return self.update(self.instance, self.validated_data)

    def delete_obj(self) -> None:
        assert self.instance is not None
        self.delete(self.instance)

    def _get_deprecated(self) -> Dict[str, str]:
        if _meta := getattr(self, "Meta", None):
            return getattr(_meta, "deprecated", {})
        return {}
