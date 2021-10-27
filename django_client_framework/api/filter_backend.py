from logging import getLogger
from typing import List

from rest_framework import filters

from .. import exceptions as e
from .. import permissions as p
from ..models.abstract import Searchable

LOG = getLogger(__name__)


class DCFFilterBackend(filters.BaseFilterBackend):
    """
    Implements DRF filter backend.
    See DRF's documentation: https://www.django-rest-framework.org/api-guide/filtering/#custom-generic-filtering
    """

    def filter_queryset(self, request, queryset, view):
        """
        Support generic filtering, eg: /products?name__in[]=abc&name__in[]=def
        """
        queryset = self.__filter_queryset_by_read_perm(request, queryset, view)
        queryset = self.__filter_queryset_by_param(request, queryset, view)
        queryset = self.__order_queryset_by_param(request, queryset, view)
        return queryset.distinct()

    def __order_queryset_by_param(self, request, queryset, view):
        """
        Support generic filtering, eg: /products/?_order_by=name
        """
        by = request.query_params.getlist("_order_by", ["-created_at"])
        by_arr = by[0].strip().split(",")
        try:
            return queryset.order_by(*by_arr)
        except Exception as execpt:
            raise e.ParseError(str(execpt))

    def __filter_queryset_by_read_perm(self, request, queryset, view):
        return p.filter_queryset_by_perms_shortcut("r", view.user_object, queryset)

    def __filter_queryset_by_param(self, request, queryset, view):
        querydict = {}
        for key in request.query_params:
            if "[]" in key:
                # Could be products?id__in[]=1,2,3 or
                # products?id__in[]=1&id__in[]=2. These are just different ways
                # to encode a list in the query param. They mean the same thing.
                # The querylist could be ["1,2,3", "1", "1"] in this case.
                querylist = request.query_params.getlist(key, [])
                normalized_querylist: List[str] = []  # normalize to ["1","2","3"]
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

            elif key == "_fulltext" and (searchtext := request.query_params.get(key)):
                if issubclass(view.model, Searchable):
                    queryset = view.model.filter_by_text_search(
                        searchtext, queryset=queryset
                    )
                else:
                    raise e.ParseError(
                        f"{view.model.__name__} does not support full text search"
                    )
            elif key and key[0] != "_":  # ignore pagination keys
                val = request.query_params.get(key, None)
                if val == "true":
                    val = True
                elif val == "false":
                    val = False
                querydict[key] = val

        try:
            return queryset.filter(**querydict)
        except Exception as exept:
            raise e.ParseError(str(exept))
