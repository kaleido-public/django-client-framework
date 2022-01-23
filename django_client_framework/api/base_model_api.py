from __future__ import annotations

import math
from functools import lru_cache
from logging import getLogger
from typing import Any, Dict, List, Optional, Type, cast
from uuid import UUID

import orjson
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models.base import Model
from django.db.models.fields import Field
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel
from django.db.models.query import QuerySet
from django.http.request import QueryDict
from django.http.response import HttpResponse
from django.utils.functional import cached_property
from ipromise import overrides
from rest_framework.exceptions import MethodNotAllowed, NotFound
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle
from rest_framework.utils.encoders import JSONEncoder
from rest_framework.views import APIView

from django_client_framework import permissions as p
from django_client_framework.api.rate_limit import DefaultRateManager
from django_client_framework.models.abstract.model import IDCFModel
from django_client_framework.models.abstract.user import DCFAbstractUser

from .. import exceptions as e
from ..models import get_user_model
from ..models.abstract.rate_limited import RateLimited
from ..models.abstract.serializable import ISerializable
from ..permissions.site_permission import has_perms_shortcut
from ..serializers import DCFSerializer
from .filter_backend import DCFFilterBackend

LOG = getLogger(__name__)


class APIPermissionDenied(Exception):
    def __init__(
        self,
        model_or_instance: Type[IDCFModel] | IDCFModel,
        perms: str,
        field: Optional[str] = None,
    ) -> None:
        self.perms = perms
        self.model_or_instance = model_or_instance
        self.field = field


# see https://www.django-rest-framework.org/api-guide/pagination/
class ApiPagination(PageNumberPagination):
    page_query_param = "_page"
    page_size_query_param = "_limit"
    page_size = 50
    max_page_size = 200

    @overrides(PageNumberPagination)
    def get_paginated_response(self, data: Any) -> Response:
        assert self.page is not None
        assert self.request is not None
        limit = self.get_page_size(self.request)
        assert limit is not None
        total = self.page.paginator.count
        return Response(
            {
                "page": self.page.number,
                "limit": limit,
                "objects_count": self.page.paginator.count,
                "pages_count": math.ceil(total / limit),
                "objects": data,
            }
        )


class DCFJSONRenderer(JSONRenderer):
    """Adds support for serializing UUID as a dictionary key."""

    def render(
        self,
        data: Any,
        accepted_media_type: Optional[str] = None,
        renderer_context: Any = None,
    ) -> bytes:
        """
        Render `data` into JSON, returning a bytestring.
        """
        if data is None:
            return b""

        renderer_context = renderer_context or {}

        ret = orjson.dumps(
            data,
            option=orjson.OPT_NON_STR_KEYS,
            default=JSONEncoder().default,
        )

        # We always fully escape \u2028 and \u2029 to ensure we output JSON
        # that is a strict javascript subset.
        # See: http://timelessrepo.com/json-isnt-a-javascript-subset
        ret = ret.replace(b"\u2028", b"\\u2028").replace(b"\u2029", b"\\u2029")
        return ret


class BaseModelAPI(GenericAPIView):
    """base class for requests to /products or /products/<id>"""

    renderer_classes = [DCFJSONRenderer]
    pagination_class = ApiPagination

    models: List[Type[ISerializable]] = []
    filter_backends = [DCFFilterBackend]

    @property
    def version(self) -> str | None:
        return getattr(self, "kwargs", {}).get("version")

    @cached_property
    def __name_to_model(self) -> Dict[str, Type[ISerializable]]:
        return {self.__model_name(model): model for model in self.models}  # type:ignore

    @overrides(APIView)
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            if request.method not in self.allowed_methods:
                raise MethodNotAllowed(request.method or "")
            return super().dispatch(request, *args, **kwargs)
        except APIPermissionDenied as error:
            self.__handle_permission_denied(error)
            raise NotImplementedError("Not reachable")

    def get_request_data(self, request: Request) -> dict:
        """
        Excludes special keys and returns only the instance related data.
        """
        if isinstance(request.data, QueryDict) or isinstance(request.data, dict):
            data = request.data.copy()
            excluded_keys = [
                "_limit",
                "_order_by",
                "_page",
                "_fulltext",
                "csrfmiddlewaretoken",
            ]
            for key in excluded_keys:
                data.pop(key, None)
            return data
        else:
            return request.data

    @cached_property
    def request_data(self) -> dict:
        """Returns cached self.get_request_data(self.request)"""
        return self.get_request_data(self.request)

    @cached_property
    def model(self) -> Type[ISerializable]:
        model_name = self.kwargs["model"]
        if model_name not in self.__name_to_model:
            valid_models = ", ".join(self.__name_to_model.keys())
            raise e.NotFound(
                f"{model_name} is not a valid model. Valid models are: {valid_models or []}"
            )
        return self.__name_to_model[model_name]

    @lru_cache
    def __model_name(self, model: Type[ISerializable]) -> str:
        return model._meta.model_name or model._meta.label_lower.split(".")[-1]

    @lru_cache
    def get_model_field(self, key: str) -> Field | None:
        return self._get_field(self.model.as_model_type(), key)

    @cached_property
    def model_object(self) -> ISerializable:
        pk = self.kwargs["pk"]
        return get_object_or_404(self.model, pk=pk)  # type: ignore

    def get_serializer_class(self) -> Type[DCFSerializer]:
        raise NotImplementedError("Must override")

    @property
    def queryset(self) -> QuerySet:  # type:ignore[override]
        return QuerySet(model=self.model.as_model_type()).all()

    def __handle_permission_denied(self, error: APIPermissionDenied) -> None:
        shortcuts = {
            "r": "read",
            "w": "write",
            "c": "create",
            "d": "delete",
        }
        actions = [shortcuts[x] for x in error.perms]
        if isinstance(error.model_or_instance, Model):
            inst: Model = error.model_or_instance
            target = f"{inst._meta.model_name}({inst.pk})"
        else:
            modl = cast(Type[IDCFModel], error.model_or_instance)
            target = f"{modl.__name__}"
        if not settings.DEBUG and not has_perms_shortcut(
            self.user_object, error.model_or_instance, "r", field_name=error.field
        ):
            # in live mode, we want to hide the existence of the object/model if
            # the user can't read it
            if isinstance(error.model_or_instance, Model):
                raise NotFound(f"Not Found: {target}")
            else:
                raise NotFound()

        msg_only_debug = "(DEBUG=True) " if settings.DEBUG else ""
        if error.field:
            raise e.PermissionDenied(
                f"{msg_only_debug}You have no {actions} permission on {target}'s {error.field} field."
            )
        else:
            raise e.PermissionDenied(
                f"{msg_only_debug}You have no {actions} permission on {target}."
            )

    @property
    def user_object(self) -> DCFAbstractUser:
        """
        DRF does not know about django-guardian's Anynymous user instance.
        This is a helper method to get the django-guardian version of user
        instances.
        """
        if self.request.user.is_anonymous:
            return self.__anonymous_user
        else:
            return cast(DCFAbstractUser, self.request.user)

    @cached_property
    def __anonymous_user(self) -> DCFAbstractUser:
        return get_user_model().get_anonymous()

    def assert_pks_exist_or_raise_404(
        self, model: Type[ISerializable], pks: List[UUID]
    ) -> None:
        queryset = model.objects.filter(pk__in=pks)
        if queryset.count() != len(pks):
            for pk in pks:
                if not model.objects.filter(pk=pk).exists():
                    raise NotFound(f"Not Found: {model.__name__} ({pk})")

    def get_serializer_context(self) -> Dict[str, Any]:
        context = super().get_serializer_context()
        view = context.get("view")
        locale = None
        if kwargs := getattr(view, "kwargs"):
            locale = kwargs.get("locale")
        context.update(
            {
                "version": self.version,
                "locale": locale,
            }
        )
        return context

    @overrides(GenericAPIView)
    def get_serializer(self, *args: Any, **kwargs: Any) -> DCFSerializer:
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", {})
        kwargs["context"].update(self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    @overrides(APIView)
    def get_throttles(self) -> List[BaseThrottle]:
        if issubclass(self.model, RateLimited):
            return [self.model.get_ratemanager(self.request, self)]
        return [DefaultRateManager(self.model, self.request, self)]

    @classmethod
    def check_3way_permissions(
        cls,
        user: DCFAbstractUser,
        model_object: IDCFModel,
        field_name: str,
        new_vals: QuerySet,
        perms: str,
    ) -> None:
        """Check user's permission on three things:

        1. The object's field (field_name)
        2. Each old related object (field on the reverse side)
        3. Each new related object (field on the reverse side)
        """

        field = cls._get_field(model_object._meta.model, field_name)
        assert isinstance(
            field,
            (
                ManyToManyRel,
                ManyToManyField,
                ManyToOneRel,
                ForeignKey,
            ),
        )

        if not p.has_perms_shortcut(
            user,
            model_object,
            perms,
            field_name=field_name,
        ):
            raise APIPermissionDenied(model_object, perms, field=field_name)

        old_vals = cls._get_field_as_queryset(model_object, field_name)
        diff_remove = old_vals.difference(new_vals)
        diff_add = new_vals.difference(old_vals)
        # Django doesn't support calling .filter() after .union() and
        # .difference()
        symmetric_diff_pks = diff_add.union(diff_remove).values_list("pk")
        diff_queryset: QuerySet = QuerySet(model=field.related_model).filter(
            pk__in=symmetric_diff_pks
        )

        cls.__check_perms_for_each(
            user,
            diff_queryset,
            field_name=field.remote_field.name,
            perms=perms,
        )

    @staticmethod
    def __check_perms_for_each(
        user: DCFAbstractUser, queryset: QuerySet, *, field_name: str, perms: str
    ) -> None:
        """For each object in the queryset, check whether the user has write
        permission on the field."""
        has_perm = p.filter_queryset_by_perms_shortcut(
            perms, user, queryset, field_name
        )
        no_perm = queryset.difference(has_perm).first()
        if no_perm:
            raise APIPermissionDenied(no_perm, perms, field_name)

    @classmethod
    def _get_field_as_queryset(
        cls, model_object: IDCFModel, field_name: str
    ) -> QuerySet:
        """Get the relation field's value of the object as a queryset."""
        field = cls._get_field(model_object._meta.model, field_name)
        if field is None:
            return QuerySet().none()
        elif isinstance(
            field, ForeignKey
        ):  # eg. Product.brand_id, or Product.brand (object)
            field_val = getattr(model_object, field_name)
            if isinstance(field_val, Model):
                field_val = field_val.pk
            return QuerySet(model=field.related_model).filter(pk=field_val)
        elif isinstance(
            field, (ManyToOneRel, ManyToManyField, ManyToManyRel)
        ):  # eg. Brand.products
            field_val = getattr(model_object, field_name)
            return field_val.all()
        else:
            raise NotImplementedError(f"Unknown type {field}.")

    @staticmethod
    @lru_cache
    def _get_field(model: Type[Model], field_name: str) -> Field | None:
        """Gets the field from the model."""
        try:
            return model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return None
