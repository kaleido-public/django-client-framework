import math
from logging import getLogger
from typing import Any, Dict, List, Optional, Type, cast
from uuid import UUID

import orjson
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models.base import Model
from django.http.request import QueryDict
from django.utils.functional import cached_property
from ipromise import overrides
from rest_framework.exceptions import MethodNotAllowed, NotFound
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder
from rest_framework.views import APIView

from django_client_framework.models.abstract.user import DCFAbstractUser

from .. import exceptions as e
from ..models import get_user_model
from ..models.abstract.serializable import Serializable
from ..permissions.site_permission import has_perms_shortcut
from ..serializers import DCFSerializer
from .filter_backend import DCFFilterBackend

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
                "limit": limit,
                "objects_count": self.page.paginator.count,
                "pages_count": math.ceil(total / limit),
                "objects": data,
            }
        )


class DCFJSONRenderer(JSONRenderer):
    """Adds support for serializing UUID as a dictionary key."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        if data is None:
            return b""

        renderer_context = renderer_context or {}

        ret = orjson.dumps(
            data,
            option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS,
            default=JSONEncoder().default,
        )

        # We always fully escape \u2028 and \u2029 to ensure we output JSON
        # that is a strict javascript subset.
        # See: http://timelessrepo.com/json-isnt-a-javascript-subset
        ret = ret.replace(b"\u2028", b"\\u2028").replace(b"\u2029", b"\\u2029")
        return ret


class BaseModelAPI(GenericAPIView):
    """base class for requests to /products or /products/1"""

    renderer_classes = [DCFJSONRenderer]
    pagination_class = ApiPagination

    models: List[Type[Serializable]] = []
    filter_backends = [DCFFilterBackend]

    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        for key, value in kwargs.items():
            print(key, value)
            setattr(self, key, value)

    @property
    def version(self) -> str:
        return getattr(self, "kwargs", {}).get("version", "default")

    @cached_property
    def __name_to_model(self) -> Dict[str, Type[Serializable[Any]]]:
        return {self.__model_name(model): model for model in self.models}

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

    @cached_property
    def model(self) -> Type[Serializable[Any]]:
        model_name = self.kwargs["model"]
        if model_name not in self.__name_to_model:
            valid_models = ", ".join(self.__name_to_model.keys())
            raise e.NotFound(
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
    def model_object(self) -> Serializable[Any]:
        pk = self.kwargs["pk"]
        return get_object_or_404(self.model, pk=pk)

    def get_serializer_class(self):
        raise NotImplementedError("Must override")

    @property
    def queryset(self):
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

    def assert_pks_exist_or_raise_404(
        self, model: Type[Serializable[Any]], pks: List[UUID]
    ):
        queryset = model.objects.filter(pk__in=pks)
        if queryset.count() != len(pks):
            for pk in pks:
                if not model.objects.filter(pk=pk).exists():
                    raise NotFound(f"Not Found: {model.__name__} ({pk})")

    def get_serializer_context(self) -> Dict[str, Any]:
        context = super().get_serializer_context()
        view = context.get("view")
        locale = "default"
        if kwargs := getattr(view, "kwargs"):
            locale = kwargs.get("locale", "default")
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
