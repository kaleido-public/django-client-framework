import math
from logging import getLogger
from typing import Any, Dict, List, Optional, Type, cast
from uuid import UUID

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models.base import Model
from django.db.models.query import QuerySet
from django.http.request import QueryDict
from django.utils.functional import cached_property
from ipromise import overrides
from rest_framework.exceptions import MethodNotAllowed, NotFound
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django_client_framework.models.abstract.model import DCFModel
from django_client_framework.models.abstract.user import DCFAbstractUser

from .. import exceptions as e
from .. import permissions as p
from ..models import get_user_model
from ..models.abstract import Searchable
from ..models.abstract.serializable import Serializable
from ..permissions.site_permission import has_perms_shortcut
from ..serializers import Serializer as DCFSerializer

LOG = getLogger(__name__)


class APIPermissionDenied(Exception):
    def __init__(
        self,
        model_or_instance,
        perm,
        field: Optional[str] = None,
    ) -> None:
        self.perm = perm
        self.model_or_instance = model_or_instance
        self.field = field


# see https://www.django-rest-framework.org/api-guide/pagination/
class ApiPagination(PageNumberPagination):
    page_query_param = "_page"
    page_size_query_param = "_limit"
    page_size = 50
    max_page_size = 200

    @overrides(PageNumberPagination)
    def get_paginated_response(self, data):
        assert self.page is not None
        assert self.request is not None
        limit = self.get_page_size(self.request)
        assert limit is not None
        total = self.page.paginator.count
        return Response(
            {
                "page": self.page.number,
                "number": self.page.number,
                "limit": limit,
                "total": self.page.paginator.count,
                "total_objects": self.page.paginator.count,
                "total_pages": math.ceil(total / limit),
                "previous": self.get_previous_link(),
                "next": self.get_next_link(),
                "objects": data,
            }
        )


class BaseModelAPI(APIView):
    """base class for requests to /products or /products/1"""

    models: List[Type[Serializable]] = []

    @cached_property
    def __name_to_model(self) -> Dict[str, Type[Serializable]]:
        return {self.__model_name(model): model for model in self.models}

    @cached_property
    def paginator(self):
        return ApiPagination()

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    @overrides(APIView)
    def dispatch(self, request, *args, **kwargs):
        try:
            if request.method not in self.allowed_methods:
                raise MethodNotAllowed(request.method)
            return super().dispatch(request, *args, **kwargs)
        except APIPermissionDenied as error:
            self.__handle_permission_denied(error)

    def get_request_data(self, request: Request):
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
    def request_data(self):
        """Returns cached self.get_request_data(self.request)"""
        return self.get_request_data(self.request)

    def __filter_queryset_by_param(self, queryset):
        """
        Support generic filtering, eg: /products?name__in[]=abc&name__in[]=def
        """
        querydict = {}
        for key in self.request.query_params:
            if "[]" in key:
                # Could be products?id__in[]=1,2,3 or
                # products?id__in[]=1&id__in[]=2. These are just different ways
                # to encode a list in the query param. They mean the same thing.
                # The querylist could be ["1,2,3", "1", "1"] in this case.
                querylist = self.request.query_params.getlist(key, [])
                normalized_querylist = []  # normalize to [1,2,3]
                # "products?id__in[]=" gets translated to <QueryDict:
                # {'id__in[]': ['']}> this is a compromise we want to make,
                # because there is no way standard way to represent an empty
                # list in the query string.
                if len(querylist) == 1 and querylist[0] == "":
                    normalized_querylist = []
                else:
                    for q in querylist:
                        normalized_querylist += q.split(",")
                querydict[key[:-2]] = normalized_querylist

            elif key == "_fulltext" and (
                searchtext := self.request.query_params.get(key)
            ):
                if issubclass(self.model, Searchable):
                    queryset = self.model.filter_by_text_search(
                        searchtext, queryset=queryset
                    )
                else:
                    raise e.ValidationError(
                        f"{self.model.__name__} does not support full text search"
                    )
            elif key and key[0] != "_":  # ignore pagination keys
                val = self.request.query_params.get(key, None)
                if val == "true":
                    val = True
                elif val == "false":
                    val = False
                querydict[key] = val

        try:
            return queryset.filter(**querydict)
        except Exception as exept:
            raise e.ValidationError({"error": str(exept)})

    def __order_queryset_by_param(self, queryset: QuerySet):
        """
        Support generic filtering, eg: /products?_order_by=name
        """
        by = self.request.query_params.getlist("_order_by", ["-created_at"])
        by_arr = by[0].strip().split(",")
        try:
            return queryset.order_by(*by_arr)
        except Exception as execpt:
            raise e.ValidationError({"error": str(execpt)})

    @overrides(GenericAPIView)
    def filter_queryset(self, queryset):
        return self.__order_queryset_by_param(
            self.__filter_queryset_by_param(
                p.filter_queryset_by_perms_shortcut("r", self.user_object, queryset)
            )
        ).distinct()

    @cached_property
    def model(self) -> Type[Serializable]:
        model_name = self.kwargs["model"]
        if model_name not in self.__name_to_model:
            valid_models = ", ".join(self.__name_to_model.keys())
            raise e.ValidationError(
                f"{model_name} is not a valid model. Valid models are: {valid_models or []}"
            )
        return self.__name_to_model[model_name]

    def __model_name(self, model: Type[Model]) -> str:
        return model._meta.model_name or model._meta.label_lower.split(".")[-1]

    def get_model_field(self, key, default=None):
        try:
            return self.model._meta.get_field(key)
        except FieldDoesNotExist:
            return default

    @cached_property
    def model_object(self) -> Serializable:
        pk = self.kwargs["pk"]
        return get_object_or_404(self.model, pk=pk)

    def get_serializer(
        self, instance: Serializable = None, **kwargs: Any
    ) -> DCFSerializer:
        if instance:
            return instance.get_serializer(
                context=self.get_serializer_context(), **kwargs
            )
        else:
            return self.model.serializer_class()(
                context=self.get_serializer_context(), **kwargs
            )

    def get_serializer_context(self) -> Dict[str, Any]:
        return {
            "request": self.request,
            "view": self,
        }

    @overrides(GenericAPIView)
    def get_queryset(self, *args, **kwargs):
        return self.model.objects.all()

    def __handle_permission_denied(self, error: APIPermissionDenied):
        shortcuts = {
            "r": "read",
            "w": "write",
            "c": "create",
            "d": "delete",
        }
        action = shortcuts[error.perm]
        if isinstance(error.model_or_instance, Model):
            inst: Model = error.model_or_instance
            target = f"{inst._meta.model_name}({inst.pk})"
        else:
            modl: Type[Model] = error.model_or_instance
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
                f"{msg_only_debug}You have no {action} permission on {target}'s {error.field} field."
            )
        else:
            raise e.PermissionDenied(
                f"{msg_only_debug}You have no {action} permission on {target}."
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

    def assert_pks_exist_or_raise_404(self, model: Type[DCFModel], pks: List[UUID]):
        queryset = model.objects.filter(pk__in=pks)
        if queryset.count() != len(pks):
            for pk in pks:
                if not model.objects.filter(pk=pk).exists():
                    raise NotFound(f"Not Found: {model.__name__} ({pk})")
