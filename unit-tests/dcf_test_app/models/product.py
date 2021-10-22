import logging

from django_client_framework import models as m
from django_client_framework.api import register_api_model
from django_client_framework.models import Serializable
from django_client_framework.models.abstract.model import DCFModel
from django_client_framework.serializers.model_serializer import DCFModelSerializer

LOG = logging.getLogger(__name__)


@register_api_model
class Product(DCFModel, Serializable):
    class Meta:
        pass

    barcode = m.CharField(max_length=255, blank=True, default="")
    priority = m.IntegerField(default=1)
    brand = m.ForeignKey(
        "Brand", null=True, on_delete=m.SET_NULL, related_name="products"
    )
    brand_id: int

    @classmethod
    def get_serializer_class(cls, version, context):
        return ProductSerializer


class ProductSerializer(DCFModelSerializer["Product"]):
    class Meta:
        model = Product
        fields = ["id", "priority", "brand_id", "barcode"]
