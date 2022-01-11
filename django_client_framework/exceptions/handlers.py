from __future__ import annotations

from typing import Any, List

from django.http import JsonResponse
from django.http.response import HttpResponse
from rest_framework.exceptions import APIException


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
    """
    The client expects a error message matching the schema
    {
       "<field_name>": [
           {
               "code": "<code>",
               "message": "<message>"
           }
       ],
       // errors that are not specific to a field
       "general_errors": ["<message>"]
    }
    """
    if isinstance(error, APIException):
        if isinstance(error.detail, str):
            return JsonResponse(
                {"general_errors": [str(error.detail)]},
                status=error.status_code,
            )
        if isinstance(error.detail, (list, tuple)):
            return JsonResponse(
                {"general_errors": flatten_to_list(error.detail)},
                status=error.status_code,
            )
        if isinstance(error.detail, dict):
            data = error.get_full_details()
            if "general_errors" in error.detail:
                data["general_errors"] = flatten_to_list(error.detail["general_errors"])
            return JsonResponse(data, status=error.status_code)
        return JsonResponse(error.get_full_details(), status=error.status_code)
    else:
        # get default behavior
        from rest_framework.views import exception_handler

        return exception_handler(error, context)


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
