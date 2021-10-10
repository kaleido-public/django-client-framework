from logging import getLogger
from typing import Any, List

from django.db.models.fields.related import ForeignKey
from ipromise import overrides
from rest_framework.response import Response
from rest_framework.views import APIView

from django_client_framework import exceptions as e
from django_client_framework import permissions as p

from .base_model_api import APIPermissionDenied, BaseModelAPI

LOG = getLogger(__name__)


class ModelCollectionAPI(BaseModelAPI):
    """handle request such as GET/POST /products"""

    allowed_methods: List[str] = ["GET", "POST"]

    @overrides(APIView)
    def check_permissions(self, request):
        if request.method == "POST":
            if not p.has_perms_shortcut(self.user_object, self.model, "c"):
                raise e.PermissionDenied("You have no permission to perform POST.")

    def get(self, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        assert self.paginator
        page: Any
        page = self.paginator.paginate_queryset(queryset, self.request, view=self)
        return self.paginator.get_paginated_response(
            [self.get_serializer(obj).data for obj in page]
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request_data)
        serializer.is_valid(raise_exception=True)
        # make sure user write permission to related fields
        for field_name, field_instance in serializer.validated_data.items():
            model_field = self.get_model_field(field_name)
            if model_field and isinstance(model_field, ForeignKey) and field_instance:
                related_name = model_field.related_query_name()
                if not p.has_perms_shortcut(
                    self.user_object, field_instance, "w", field_name=related_name
                ):
                    raise APIPermissionDenied(field_instance, "w", field=related_name)

        instance = serializer.save()
        if p.has_perms_shortcut(self.user_object, instance, "r"):
            return Response(
                self.get_serializer(instance).data,
                status=201,
            )
        else:
            return Response(
                {
                    "success": True,
                    "detail": "The object has been created but you have no permission to view it.",
                },
                status=201,
            )
