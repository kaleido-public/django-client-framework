from __future__ import annotations

import logging
from typing import *

from django.db.models.manager import Manager

from django_client_framework import models as m
from django_client_framework.api import register_api_model
from django_client_framework.models import DCFModel, Serializable
from django_client_framework.serializers.model_serializer import DCFModelSerializer

from .brand import BrandSerializer

LOG = logging.getLogger(__name__)


@register_api_model
class Product(DCFModel["Product"], Serializable["Product", Any]):
    objects: Manager["Product"] = Manager()

    barcode = m.CharField(max_length=255, blank=True, default="")
    priority = m.IntegerField(default=1)
    brand = m.ForeignKey(
        "Brand", null=True, on_delete=m.SET_NULL, related_name="products"
    )
    brand_id: int

    @classmethod
    def get_serializer_class(
        cls, version: str | None, context: Any
    ) -> Type[ProductSerializer]:
        return ProductSerializer


class ProductSerializer(DCFModelSerializer["Product", Any]):
    class Meta:
        model = Product
        fields = [
            "id",
            "type",
            "created_at",
            "priority",
            "brand_id",
            "barcode",
            "brand__data",
        ]

        deprecated = {
            "some-deprecated-field": "deprecated test",
        }

    brand__data = BrandSerializer(
        read_only=True,
        prefer_cache=True,
    )
