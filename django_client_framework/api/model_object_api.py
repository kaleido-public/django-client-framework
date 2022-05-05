from __future__ import annotations

from logging import getLogger
from typing import Any, List, Type

from django.db.models import QuerySet
from django.db.models.deletion import ProtectedError
from django.db.models.fields.related import ForeignKey
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from ipromise import overrides
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from django_client_framework import exceptions as e
from django_client_framework import permissions as p
from django_client_framework.models.abstract.model import DCFModel
from django_client_framework.serializers.serializer import DCFSerializer

from .base_model_api import APIPermissionDenied, BaseModelAPI

LOG = getLogger(__name__)


class UpdatedHiddenObject(APIException):
    status_code = 200
    default_detail = (
        "The object has been updated but you have no permission to view it."
    )
    default_code = "success_hidden"


class ModelObjectAPI(BaseModelAPI):
    """handle requests such as GET/DELETE/PATCH /products/1"""

    allowed_methods: List[str] = ["GET", "DELETE", "PATCH"]

    @overrides(APIView)
    def check_permissions(self, request: HttpRequest) -> None:
        pass

    @overrides(APIView)
    def check_object_permissions(self, request: HttpRequest, obj: DCFModel) -> None:
        pass

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not p.has_perms_shortcut(self.user_object, self.model_object, "r"):
            raise APIPermissionDenied(self.model_object, "r")
        serializer = self.get_serializer(instance=self.model_object)
        return Response(serializer.data)

    def patch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # permission check deferred to .perform_update()
        instance = self.model_object
        has_read_permissions = False
        if p.has_perms_shortcut(self.user_object, instance, "r"):
            has_read_permissions = True

        serializer = self.get_serializer(
            instance=instance,
            data=self.request_data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        # User must have write permission on the field being modified.
        for field_name, field_val in serializer.validated_data.items():
            # Note that in case field_name is a foreign key, there are two
            # cases:
            #   1. brand
            #   2. brand_id
            # If the field_name is brand then field_val is usually a brand
            # object. If the field name is brand_id, then field val is UUID.
            field = self.get_model_field(field_name)
            if not field:
                continue
            # For foreign keys, user must have 3-way permissions. See
            # .check_3way_permissions().
            if isinstance(field, ForeignKey):
                field_name = field.name  # this removes "_id"
                if isinstance(field_val, DCFModel):
                    field_val_pk = field_val.pk
                else:
                    field_val_pk = field_val
                new_related_obj: QuerySet = QuerySet(model=field.related_model).filter(
                    pk=field_val_pk
                )
                if not new_related_obj.exists():
                    raise e.NotFound(f"Related object {field_val_pk} does not exist.")
                self.check_3way_permissions(
                    self.user_object,
                    self.model_object,
                    field_name,
                    new_related_obj,
                    "w",
                )
            elif not p.has_perms_shortcut(
                self.user_object, self.model_object, "w", field_name
            ):
                raise APIPermissionDenied(self.model_object, "w", field=field_name)
        # when permited
        serializer.save()

        if has_read_permissions:
            p.add_perms_shortcut(self.user_object, instance, "r")
        if p.has_perms_shortcut(self.user_object, instance, "r"):
            return Response(
                self.get_serializer(instance=instance).data,
                status=200,
            )
        else:
            raise UpdatedHiddenObject()

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not p.has_perms_shortcut(self.user_object, self.model_object, "d"):
            raise APIPermissionDenied(self.model_object, "d")
        try:
            serializer = self.get_serializer(self.model_object, data=self.request_data)
            if hasattr(serializer, "delete_obj"):
                serializer.delete_obj()
            else:
                self.model_object.delete()
        except ProtectedError as excpt:
            raise e.ValidationError(str(excpt))
        else:
            return Response(status=204)

    @overrides(GenericAPIView)
    def get_serializer_class(self) -> Type[DCFSerializer]:
        return self.model.get_serializer_class(
            version=self.version,
            context=self.get_serializer_context(),
        )
