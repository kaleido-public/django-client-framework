from __future__ import annotations

from logging import getLogger
from typing import Any, Iterable, List, Type

from django.db.models import QuerySet
from django.db.models.fields.related import ForeignKey
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from ipromise import overrides
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from django_client_framework import exceptions as e
from django_client_framework import permissions as p
from django_client_framework.models import DCFModel
from django_client_framework.models.abstract.serializable import Serializable
from django_client_framework.serializers.serializer import DCFSerializer

from .base_model_api import APIPermissionDenied, BaseModelAPI

LOG = getLogger(__name__)


class CreatedHiddenObject(APIException):
    status_code = 201
    default_detail = (
        "The object has been created but you have no permission to view it."
    )
    default_code = "success_hidden"


class DCFCollectionSchema(AutoSchema):
    pass


class ModelCollectionAPI(BaseModelAPI):
    """handle request such as GET/POST /products/"""

    schema = DCFCollectionSchema()

    allowed_methods: List[str] = ["GET", "POST"]

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
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
        if not p.has_perms_shortcut(self.user_object, self.model.as_model_type(), "c"):
            raise e.PermissionDenied("You have no permission to perform POST.")
        serializer = self.get_serializer(data=self.request_data)
        serializer.is_valid(raise_exception=True)
        # Make sure user has related field's write permission for each related
        # object
        for field_name, field_value in serializer.validated_data.items():
            field = self.get_model_field(field_name)
            if field and isinstance(field, ForeignKey) and field_value:
                # Note that in case field_name is a foreign key, there are two
                # cases:
                #   1. brand
                #   2. brand_id
                # If the field_name is brand then field_val is usually a brand
                # object. If the field name is brand_id, then field val is UUID.
                new_related_obj: None | DCFModel
                if isinstance(field_value, DCFModel):
                    new_related_obj = field_value
                else:
                    new_related_obj = (
                        QuerySet(model=field.related_model)
                        .filter(pk=field_value)
                        .first()
                    )
                if new_related_obj is None:
                    raise e.NotFound(f"Related object {field_value} does not exist.")
                else:
                    # Make sure the related object's related name can be
                    # written. For example, for product/<id>/brand, this is
                    # checking if brand.products can be written.
                    if not p.has_perms_shortcut(
                        self.user_object,
                        new_related_obj,
                        "w",
                        field_name=field.remote_field.name,
                    ):
                        raise APIPermissionDenied(
                            new_related_obj, "w", field=field.remote_field.name
                        )

        instance = serializer.save()
        if p.has_perms_shortcut(self.user_object, instance, "r"):
            return Response(
                self.get_serializer(instance).data,
                status=201,
            )
        else:
            raise CreatedHiddenObject()

    @overrides(GenericAPIView)
    def get_serializer_class(self) -> Type[DCFSerializer]:
        return self.model.get_serializer_class(
            version=self.version,
            context=self.get_serializer_context(),
        )
