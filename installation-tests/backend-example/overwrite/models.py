# type: ignore

from django.db.models import CASCADE, CharField, ForeignKey

from django_client_framework.api import register_api_model
from django_client_framework.models import AccessControlled, DCFModel, Serializable
from django_client_framework.permissions import add_perms_shortcut, default_groups
from django_client_framework.serializers import DCFModelSerializer


@register_api_model
class Brand(DCFModel, Serializable, AccessControlled):
    name = CharField(max_length=16)

    @classmethod
    def get_serializer_class(cls, version, context):
        return BrandSerializer

    class PermissionManager(AccessControlled.PermissionManager):
        def add_perms(self, brand):
            add_perms_shortcut(default_groups.anyone, brand, "r")


class BrandSerializer(DCFModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "type", "created_at", "name"]


@register_api_model
class Product(DCFModel, Serializable, AccessControlled):
    barcode = CharField(max_length=32)
    brand = ForeignKey("Brand", related_name="products", on_delete=CASCADE, null=True)

    @classmethod
    def get_serializer_class(cls, version, context):
        return ProductSerializer

    class PermissionManager(AccessControlled.PermissionManager):
        def add_perms(self, product):
            add_perms_shortcut(default_groups.anyone, product, "r")


class ProductSerializer(DCFModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "type", "created_at", "barcode", "brand_id"]
