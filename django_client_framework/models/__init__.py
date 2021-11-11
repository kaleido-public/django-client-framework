from typing import Any, Type, TypeVar, cast

from django.contrib.auth import get_user_model as django_get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.postgres.fields import *
from django.db.models import *

from django_client_framework.models.abstract.user import DCFAbstractUser

from .abstract import (
    AccessControlled,
    DCFModel,
    DjangoModel,
    RateLimited,
    Searchable,
    Serializable,
)
from .fields import PriceField, UniqueForeignKey
from .lookup import *
from .search_feature import SearchFeature


def get_user_model() -> Type[DCFAbstractUser]:
    return cast(Any, django_get_user_model())


def check_integrity():
    from . import abstract

    abstract.check_integrity()
