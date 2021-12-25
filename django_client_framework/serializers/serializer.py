from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Optional

from rest_framework.serializers import Serializer as DRFSerializer

from ..models.abstract.model import T
from ..models.abstract.serializable import D

if TYPE_CHECKING:
    pass


class DCFSerializer(DRFSerializer, Generic[T, D]):
    # Every attribute / method in this class must also be added to the
    # DelegateSerializer, otherwise the DelegateSerializer breaks.

    instance: Optional[T]
    data: D  # type: ignore

    def update(self, instance: T, validated_data: Any) -> T:
        return super().update(instance, validated_data)

    def create(self, validated_data: Any) -> T:
        return super().create(validated_data)

    def save(self, **kwargs: Any) -> T:
        return super().save(**kwargs)

    def delete(self, instance: T) -> None:
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
