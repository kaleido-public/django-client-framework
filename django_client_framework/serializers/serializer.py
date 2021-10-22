from __future__ import annotations

from typing import Any, Generic, TypeVar

from rest_framework.serializers import Serializer as DRFSerializer

from ..models import DCFModel

T = TypeVar("T", bound=DCFModel)


class DCFSerializer(DRFSerializer, Generic[T]):
    # Every attribute / method in this class must also be added to the
    # DelegateSerializer, otherwise the DelegateSerializer breaks.

    instance: T | None

    def update(self, instance: T, validated_data: Any) -> T:
        return super().update(instance, validated_data)

    def create(self, validated_data: T) -> T:
        return super().create(validated_data)

    def save(self, **kwargs: Any) -> T:
        return super().save(**kwargs)

    def delete(self, instance: T):
        instance.delete()

    def create_obj(self) -> T:
        assert self.validated_data is not None
        return self.create(self.validated_data)

    def update_obj(self) -> T:
        assert self.instance is not None
        assert self.validated_data is not None
        return self.update(self.instance, self.validated_data)

    def delete_obj(self):
        assert self.instance is not None
        self.delete(self.instance)
