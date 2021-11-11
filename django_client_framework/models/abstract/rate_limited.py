from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, Type, TypeVar

from django.db.models.base import Model
from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from django_client_framework.models.abstract.model import AbstractDCFModel, DCFModel

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...api import BaseModelAPI
    from .user import DCFAbstractUser

T = TypeVar("T", bound="DCFModel")


class RateLimited(AbstractDCFModel[T], Generic[T]):
    class Meta:
        abstract = True

    class RateManager(SimpleRateThrottle):
        def __init__(
            self, model: Type[Model], request: Request, view: BaseModelAPI
        ) -> None:
            self.model = model
            self.request = request
            self.view = view
            super().__init__()

        def get_rate_limit(
            self,
            queryset: QuerySet,
            user: DCFAbstractUser,
            action: str,
            version: str,
            context: Dict[str, Any],
        ) -> str:
            raise NotImplementedError(
                f"{self.model}.RateManager must overwrite .get_rate_limit(...)"
            )

        def get_rate(self) -> Optional[str]:
            return self.get_rate_limit(
                queryset=self.view.queryset,
                user=self.view.user_object,
                action=self.get_action(self.request),
                version=self.view.version,
                context=self.view.get_serializer_context(),
            )

        def get_record_key(
            self,
            queryset: QuerySet,
            user: DCFAbstractUser,
            ipid: str,
            action: str,
            version: str,
            context: Dict[str, Any],
        ) -> str:
            return str(hash((queryset.model, user, ipid, action)))

        def get_action(self, request: Request) -> str:
            assert request.method
            action = {
                "POST": "create",
                "GET": "read",
                "PATCH": "write",
                "DELETE": "delete",
            }.get(request.method)
            assert action
            return action

        def get_cache_key(self, request: Request, view: APIView) -> Optional[str]:
            from ...api import BaseModelAPI

            assert isinstance(view, BaseModelAPI)
            return "ratemanager_" + self.get_record_key(
                queryset=view.queryset,
                user=view.user_object,
                ipid=self.get_ident(request),
                action=self.get_action(request),
                version=view.version,
                context=view.get_serializer_context(),
            )

    @classmethod
    def get_ratemanager(cls, request: Request, view: BaseModelAPI) -> RateManager:
        ratemanager = getattr(cls, "RateManager", None)
        if not ratemanager:
            raise TypeError(f"Expect a nested class named RateManager in {cls}")
        if not issubclass(ratemanager, RateLimited.RateManager):
            raise TypeError(
                f"{ratemanager} should inherit from RateLimtied.RateManager"
            )
        return ratemanager(cls, request, view)
