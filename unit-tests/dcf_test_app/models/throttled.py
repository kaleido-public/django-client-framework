from __future__ import annotations

from typing import *

from django.db.models.query import QuerySet

from django_client_framework.api import register_api_model
from django_client_framework.models import DCFModel, RateLimited, Serializable
from django_client_framework.models.abstract.user import DCFAbstractUser
from django_client_framework.serializers import DCFModelSerializer


@register_api_model
class ThrottledModel(DCFModel, Serializable, RateLimited):
    class Meta:
        pass

    @classmethod
    def get_serializer_class(
        cls, version: str | None, context: Any
    ) -> Type[ThrottledModelSerializer]:
        return ThrottledModelSerializer

    class RateManager(RateLimited.RateManager):
        def get_rate_limit(
            self,
            queryset: QuerySet,
            user: DCFAbstractUser,
            action: str,
            version: str | None,
            context: Dict[str, Any],
        ) -> str:
            return "10/min"


class ThrottledModelSerializer(DCFModelSerializer):
    class Meta:
        model = ThrottledModel
        fields = [
            "id",
            "type",
            "created_at",
        ]
