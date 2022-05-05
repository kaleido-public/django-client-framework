from __future__ import annotations

from typing import Any, List

from django.http import Http404, JsonResponse
from django.http.response import Http404, HttpResponse
from rest_framework.exceptions import APIException, ValidationError
from django_client_framework.api.base_model_api import APIPermissionDenied


def flatten_to_list(data: Any) -> List[str]:
    general_errors: List[str] = []
    todo = [data]
    while todo != []:
        item = todo.pop(0)
        if isinstance(item, str):
            general_errors.append(str(item))
        elif isinstance(item, (list, tuple)):
            todo.extend(list(item))
        elif isinstance(item, dict):
            todo.extend(list(item.values()))
    return general_errors


def dcf_exception_handler(error: Any, context: Any) -> HttpResponse | None:
    if isinstance(error, APIPermissionDenied):
        raise error
    if isinstance(error, ValidationError):
        if isinstance(error.detail, (str, list, tuple)):
            return JsonResponse(
                {
                    "code": "validation_error",
                    "message": "The provided input is invalid.",
                    "fields": {},
                    "non_field": " ".join(flatten_to_list(error.detail)),
                },
                status=400,
            )
        if isinstance(error.detail, dict):
            return JsonResponse(
                {
                    "code": "validation_error",
                    "message": "The provided input is invalid.",
                    "fields": {
                        k: " ".join(flatten_to_list(v)) for k, v in error.detail.items()
                    },
                    "non_field": "",
                },
                status=400,
            )
        return JsonResponse(
            {"code": "validation_error", "message": str(error)}, status=500
        )
    elif isinstance(error, APIException):
        return JsonResponse(error.get_full_details(), status=error.status_code)
    elif isinstance(error, Http404):
        return JsonResponse(
            {"code": "not_found", "message": "The URL does not exist."}, status=404
        )
    else:
        return JsonResponse({"code": "unknown", "message": str(error)}, status=500)


class ConvertAPIExceptionToJsonResponse:
    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request: Any) -> Any:
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response

    def process_exception(self, request: Any, expt: Any) -> JsonResponse | None:
        if isinstance(expt, APIException):
            return JsonResponse(expt.detail, status=expt.status_code, safe=False)
        else:
            return None
