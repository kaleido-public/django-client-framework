from __future__ import annotations

from typing import *

from django.db.models import QuerySet

from django_client_framework.models import DCFAbstractUser
from django_client_framework.models.abstract.rate_limited import RateLimited

if TYPE_CHECKING:
    from ..serializers.serializer import SerializerContext

default = "60/min"


class DefaultRateManager(RateLimited.RateManager):
    def get_rate_limit(
        self,
        queryset: QuerySet,
        user: DCFAbstractUser,
        action: str,
        version: str | None,
        context: SerializerContext | None,
    ) -> str:
        return default
