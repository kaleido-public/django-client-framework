from __future__ import annotations

from typing import TYPE_CHECKING, List

from django.db import models as m
from django.db.models.manager import Manager

from django_client_framework.api import register_api_model
from django_client_framework.models import DCFModel, Serializable
from django_client_framework.serializers import DCFModelSerializer

if TYPE_CHECKING:
    from dcf_test_app.models.product import Product
    from django.db.models.manager import RelatedManager


@register_api_model
class Brand(DCFModel["Brand"], Serializable):
    objects: Manager["Brand"] = Manager()

    name = m.CharField(max_length=100, unique=True, null=True)
    priority = m.IntegerField(default=1)
    products: RelatedManager[Product]

    @classmethod
    def get_serializer_class(cls, version, context):
        return BrandSerializer


class BrandSerializer(DCFModelSerializer):
    class Meta:
        model = Brand
        exclude: List[str] = []
