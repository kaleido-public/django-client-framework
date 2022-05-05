from __future__ import annotations

from logging import getLogger
from typing import Any, Iterable, List, Type, cast
from uuid import UUID

from django.db.models.fields import Field, related_descriptors
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import (
    ManyToManyRel,
    ManyToOneRel,
    OneToOneRel,
)
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.functional import cached_property
from ipromise import overrides
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from django_client_framework import exceptions as e
from django_client_framework import permissions as p
from django_client_framework.models.abstract.serializable import (
    ISerializable,
    Serializable,
)
from django_client_framework.serializers.serializer import DCFSerializer

from .base_model_api import APIPermissionDenied, BaseModelAPI

LOG = getLogger(__name__)


class ActionSuccessHiddenObject(APIException):
    status_code = 200
    default_detail = (
        "Action was successful but you have no permission to view the result."
    )
    default_code = "success_hidden"


class RelatedModelAPI(BaseModelAPI):
    """handle requests such as GET/POST/PATCH /products/<id>/images"""

    @property
    def allowed_methods(self) -> List[str]:
        if self.is_related_object_api:
            return ["GET", "PATCH"]
        else:
            return ["GET", "DELETE", "POST", "PATCH"]

    @cached_property
    def __body_pk_ls(self) -> List[UUID]:
        data = self.request_data
        if isinstance(data, list):
            if len(data) > 0:
                for item in data:
                    if type(item) is not str:
                        raise e.ParseError(
                            "Expected a list of model pk in the request body,"
                            f" but one of the list item received is {type(item)}: {item}"
                        )
            try:
                return list(map(UUID, data))
            except ValueError as err:
                raise e.ParseError(str(err))
        else:
            raise e.ParseError(
                "Expected a list of object pk in the request body,"
                f" but received {type(data).__name__}: {data}"
            )

    @cached_property
    def __body_pk(self) -> UUID | None:
        """Returns the request body as a UUID, or None (when json is null)."""
        data = self.request_data
        if data is None:
            return None
        elif isinstance(data, str):
            try:
                return UUID(data)
            except ValueError as err:
                raise e.ParseError(str(err))
        else:
            raise e.ParseError(
                "Expected an object pk in the request body,"
                f" but received {type(data).__name__}: {data}"
            )

    @cached_property
    def __body_pk_queryset(self) -> QuerySet:
        """Returns the QuerySet from pks in the request body."""
        if self.is_related_object_api:
            if self.__body_pk is None:
                queryset = self.field_model.objects.none()
            else:
                queryset = self.field_model.objects.filter(pk=self.__body_pk)
        else:
            queryset = self.field_model.objects.filter(pk__in=self.__body_pk_ls)
        return queryset

    @cached_property
    def __field_val_queryset(self) -> QuerySet:
        """Returns the current route's object's field value as a QuerySet."""
        return self._get_field_as_queryset(self.model_object, self.field_name)

    def __return_get_result_if_permitted(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """Checks for the user's read permission of the current route's model
        object. If no read permission, Responses with error, otherwise handles
        as a GET request.
        """
        if p.has_perms_shortcut(
            self.user_object, self.model_object, "r", field_name=self.field_name
        ):
            return self.get(request, *args, **kwargs)
        else:
            raise ActionSuccessHiddenObject()

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handles GET request."""
        if not p.has_perms_shortcut(
            self.user_object, self.model_object, "r", self.field_name
        ):
            raise APIPermissionDenied(self.model_object, "r", self.field_name)
        if self.is_related_object_api:
            if self.field_val:
                if not p.has_perms_shortcut(self.user_object, self.field_val, "r"):
                    raise APIPermissionDenied(self.field_val, "r")
                serializer = self.get_serializer(instance=self.field_val)
                return Response(serializer.data)
            else:
                raise e.NotFound()
        else:
            queryset = self.filter_queryset(self.queryset)
            assert self.paginator
            page: Iterable[Serializable] = self.paginator.paginate_queryset(
                queryset, self.request, view=self
            )
            serializer = self.get_serializer()
            return self.paginator.get_paginated_response(
                [
                    data.json(
                        version=self.version,
                        context=self.get_serializer_context(),
                        serializer=serializer,
                    )
                    for data in page
                ]
            )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handles POST request."""
        self.assert_pks_exist_or_raise_404(self.field_model, self.__body_pk_ls)
        self.check_3way_permissions(
            self.user_object,
            self.model_object,
            self.field_name,
            new_vals=self.__body_pk_queryset,
            perms="w",
        )
        self.field_val.add(*self.__body_pk_queryset)
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def patch_related_object(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """Handles PATCH request when the route is Related Object API."""
        if self.__body_pk is not None:
            self.assert_pks_exist_or_raise_404(self.field_model, [self.__body_pk])
        setattr(self.model_object, self.field_name, self.__body_pk_queryset.first())
        self.field_val.save()
        self.model_object.save()
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def patch_related_collection(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """Handles PATCH request when the route is Related Collection API."""
        self.assert_pks_exist_or_raise_404(self.field_model, self.__body_pk_ls)
        self.field_val.set(self.__body_pk_queryset)
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    def patch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handles PATCH request."""
        if self.is_related_object_api:
            if self.__body_pk is not None:
                self.assert_pks_exist_or_raise_404(self.field_model, [self.__body_pk])
        else:
            self.assert_pks_exist_or_raise_404(self.field_model, self.__body_pk_ls)
        self.check_3way_permissions(
            self.user_object,
            self.model_object,
            self.field_name,
            new_vals=self.__body_pk_queryset,
            perms="w",
        )
        if self.is_related_object_api:
            return self.patch_related_object(request, *args, **kwargs)
        else:
            return self.patch_related_collection(request, *args, **kwargs)

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handles DELETE request."""
        self.check_3way_permissions(
            self.user_object,
            self.model_object,
            self.field_name,
            new_vals=self.__field_val_queryset.difference(self.__body_pk_queryset),
            perms="w",
        )
        if not hasattr(self.field_val, "remove"):
            raise e.ValidationError(
                f"Cannot remove {self.field_name} from {self.model.__name__} due to non-null constraints."
            )
        # silently ignore invalid pks
        selected_products = self.field_model.objects.filter(
            id__in=self.__body_pk_ls
        ).intersection(self.field_val.all())
        self.field_val.remove(*selected_products)
        return self.__return_get_result_if_permitted(request, *args, **kwargs)

    @cached_property
    def field_name(self) -> str:
        """Returns the field_name part from the request url: "/<model_name>/<id>/<field_name>" """
        field_name = self.kwargs["target_field"]
        self.check_field_name(field_name)
        return field_name

    def check_field_name(self, field_name: str) -> str:
        """Checks to see if field_name is actually a field on the model."""
        # only when related_name is set on field, the field becomes a key on
        # model, otherwise it becomes fieldname_set
        if not hasattr(self.model, field_name):
            raise e.ValidationError(
                {
                    "error": f'"{field_name}" is not a property name on {self.model.__name__}'
                }
            )
        target_field = self.get_model_field(field_name)
        if (
            target_field
            and isinstance(
                target_field,
                (
                    ManyToManyRel,
                    ManyToManyField,
                    ManyToOneRel,
                    ForeignKey,
                ),
            )
            and isinstance(
                getattr(self.model, field_name, None),
                (
                    related_descriptors.ForwardManyToOneDescriptor,
                    related_descriptors.ForwardOneToOneDescriptor,
                    related_descriptors.ReverseOneToOneDescriptor,
                    related_descriptors.ReverseManyToOneDescriptor,
                    related_descriptors.ManyToManyDescriptor,
                ),
            )
        ):
            return field_name
        else:
            raise e.ValidationError(
                f"Property {field_name} on {self.model.__name__} is not a valid relation."
            )

    @cached_property
    def field(self) -> Field:
        """Returns the field instance of the Model."""
        return self.model._meta.get_field(self.field_name)

    @property
    def field_val(self) -> Any:
        """Returns the field's value of the model object."""
        return getattr(self.model_object, self.field_name)

    @cached_property
    def field_model(self) -> Type[ISerializable]:
        """Returns the model of field. For example, on route
        "/product/<id>/brand", this is the Brand model."""
        return cast(Type[ISerializable], self.field.related_model)

    @property
    def queryset(self) -> QuerySet:  # type:ignore[override]
        """Provides the list or object in the HTTP response."""
        return self.__field_val_queryset

    @cached_property
    def is_related_object_api(self) -> bool:
        """Return True if the current url is to a Related Object API."""
        return isinstance(self.field, ForeignKey) or isinstance(
            self.field, OneToOneRel  # OneToOneRel is used by UniqueForeignKey
        )

    @cached_property
    def is_related_collection_api(self) -> bool:
        """Return True if the current url is to a Related Collection API."""
        return not self.is_related_object_api

    @overrides(BaseModelAPI)
    def get_serializer_class(self) -> Type[DCFSerializer]:
        """Provides the serializer class for the HTTP response."""
        return self.field_model.get_serializer_class(
            version=self.version,
            context=self.get_serializer_context(),
        )
