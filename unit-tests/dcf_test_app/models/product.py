import logging

from django_client_framework import models as m
from django_client_framework.api import register_api_model
from django_client_framework.models import Serializable
from django_client_framework.serializers.model_serializer import DCFModelSerializer

from .brand import Brand

LOG = logging.getLogger(__name__)


@register_api_model
class Product(Serializable["Product"]):
    barcode = m.CharField(max_length=255, blank=True, default="")
    priority = m.IntegerField(default=1)
    brand = m.ForeignKey(
        Brand, null=True, on_delete=m.SET_NULL, related_name="products"
    )
    brand_id: int

    @classmethod
    def serializer_class(cls):
        return ProductSerializer


class ProductSerializer(DCFModelSerializer["Product"]):
    class Meta:
        model = Product
        fields = ["id", "priority", "brand_id", "barcode"]
