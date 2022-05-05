from __future__ import annotations

from typing import *

from django.db.models import CASCADE, CharField, ForeignKey

from django_client_framework.api import register_api_model
from django_client_framework.models import (
    AccessControlled,
    DCFAbstractUser,
    DCFModel,
    Serializable,
)
from django_client_framework.permissions import add_perms_shortcut, default_groups
from django_client_framework.serializers import DCFModelSerializer


@register_api_model
class Brand(DCFModel, Serializable, AccessControlled):
    class Meta:
        pass

    name = CharField(max_length=16, blank=True)

    @classmethod
    def get_serializer_class(cls, version: str, context: Any) -> Type[BrandSerializer]:
        return BrandSerializer

    class PermissionManager(AccessControlled.PermissionManager):
        def add_perms(self, brand: Brand) -> None:
            add_perms_shortcut(default_groups.anyone, brand, "rwcd")


class BrandSerializer(DCFModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "type", "created_at", "name"]


@register_api_model
class Product(DCFModel, Serializable, AccessControlled):
    class Meta:
        pass

    barcode = CharField(max_length=32, blank=True, null=True)
    brand = ForeignKey("Brand", related_name="products", on_delete=CASCADE, null=True)

    @classmethod
    def get_serializer_class(
        cls, version: str, context: Any
    ) -> Type[ProductSerializer]:
        return ProductSerializer

    class PermissionManager(AccessControlled.PermissionManager):
        def add_perms(self, product: Product) -> None:
            add_perms_shortcut(default_groups.anyone, product, "rwcd")


class ProductSerializer(DCFModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "type", "created_at", "barcode", "brand_id"]


class User(DCFModel, DCFAbstractUser):
    pass
