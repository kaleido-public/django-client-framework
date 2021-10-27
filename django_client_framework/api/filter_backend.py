from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, Dict, List, Type

from django.core.exceptions import FieldDoesNotExist
from django.db.models.base import Model
from django.db.models.fields.related import RelatedField
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from rest_framework import filters

from django_client_framework.models.abstract.user import DCFAbstractUser

from .. import exceptions as e
from .. import permissions as p
from ..models.abstract import Searchable

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from rest_framework.request import Request

    from .base_model_api import BaseModelAPI


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
        queryset = self.__filter_by_visible_relations(request, queryset, view)
        queryset = self.__order_queryset_by_param(request, queryset, view)
        return queryset.distinct()

    def __order_queryset_by_param(
        self, request: Request, queryset: QuerySet, view: BaseModelAPI
    ) -> QuerySet:
        """
        Support generic filtering, eg: /products/?_order_by=name
        """
        by = request.query_params.getlist("_order_by", ["-created_at"])
        by_arr = by[0].strip().split(",")
        try:
            return queryset.order_by(*by_arr)
        except Exception as execpt:
            raise e.ParseError(str(execpt))

    def __filter_queryset_by_read_perm(
        self, request: Request, queryset: QuerySet, view: BaseModelAPI
    ) -> QuerySet:
        return p.filter_queryset_by_perms_shortcut("r", view.user_object, queryset)

    def __filter_queryset_by_param(
        self, request: Request, queryset: QuerySet, view: BaseModelAPI
    ) -> QuerySet:
        querydict = self.__build_query_dict(request, queryset, view)
        try:
            return queryset.filter(**querydict)
        except Exception as exept:
            raise e.ParseError(str(exept))

    def __build_query_dict(
        self, request: Request, queryset: QuerySet, view: BaseModelAPI
    ) -> Dict[str, Any]:
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
                val: Any = request.query_params.get(key, None)
                if val == "true":
                    val = True
                elif val == "false":
                    val = False
                querydict[key] = val
        return querydict

    def __filter_by_visible_relations(
        self, request: Request, queryset: QuerySet, view: BaseModelAPI
    ) -> QuerySet:
        """
        When searching a publicly readable resource such as Product, anyone can
        filter the result by using a related query name, such as "seller__user".
        This immediately poses a security threat, because anyone can filter by a
        query name such as "seller__user__token__key__startwith=abc", and
        simply observe the length of the result, to poke the user's auth token.
        (If the product result is non-empty, then you know the user's token
        starts with abc.)

        This is a safety feature that ensures the users can only filter a public
        resource via visible relations.

            Product.objects.filter(seller__user__token__key__startwith="abc")
            becomes Product.objects.filter(
                Q(seller__user__token__key__startwith="abc") &
                Q(seller__in=visible_sellers) &
                Q(seller__user__in=visible_users) &
                Q(seller__user__token__in=visible_tokens)
            )
        """

        def build_queries(
            user: DCFAbstractUser,
            queryset: QuerySet,
            # query is Query(Product)
            # optimization
            original: List[str],
            # original is ["seller", "user", "token", "startwith"]
        ) -> Q:
            node = Q()
            cur_model: Type[Model] = queryset.model
            # cur_model is Product, Seller, User, Token...
            for i in range(len(original)):
                prefix = "__".join(original[: i + 1])
                # prefix is "seller", "seller__user", "seller__user__auth", ...
                try:
                    field = cur_model._meta.get_field(original[i])
                    # for Product, field is "seller", for Seller, field is
                    # "user"
                except FieldDoesNotExist:
                    # when original[i] is startwith, it's not a field but a
                    # lookup.
                    return node
                else:
                    if isinstance(field, ForeignObjectRel) or isinstance(
                        field, RelatedField
                    ):
                        assert field.related_model is not None
                        cur_model = field.related_model  # set cur_model to Seller
                        visible: QuerySet = p.filter_queryset_by_perms_shortcut(
                            "r", user, QuerySet(model=cur_model).all()
                        )
                        node &= Q(**{prefix + "__in": visible})
                        # adds Q(seller__in=visible_sellers)
            return node

        user = view.user_object
        querydict = self.__build_query_dict(request, queryset, view)
        node = Q()
        for key in querydict.keys():
            node &= build_queries(user, queryset, key.split("__"))
        return queryset.filter(node)
