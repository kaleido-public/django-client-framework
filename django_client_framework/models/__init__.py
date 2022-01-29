from typing import Any, Type, TypeVar, cast

from deprecation import deprecated
from django.db.models import *

from .abstract import (
    AccessControlled,
    DCFAbstractUser,
    DCFModel,
    DjangoModel,
    RateLimited,
    Searchable,
    Serializable,
    get_dcf_user_model,
    get_user_model,
)
from .fields import UniqueForeignKey
from .lookup import *
from .object_permissions import (
    DCFPermission,
    GroupObjectPermission,
    UserGroup,
    UserObjectPermission,
)
from .search_feature import SearchFeature


def check_integrity() -> None:
    from . import abstract

    abstract.check_integrity()
