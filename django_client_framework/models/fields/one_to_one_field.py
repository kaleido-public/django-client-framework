from __future__ import annotations

from typing import *

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.models.fields.related import OneToOneField, ReverseOneToOneDescriptor

# __set__ value type
_ST = TypeVar("_ST", bound=Model)
# __get__ return type
_GT = TypeVar("_GT", bound=Model)


class UniqueForeignKey(OneToOneField[_ST, _GT]):
    """
    This class fix django's OneToOneField's historical problem, where accessing
    through the reverse relation when the object does not exist would raise an
    ObjectDoesNotExist exception, instead of simply returning None.
    """

    def __init__(
        self,
        to: Type[_GT] | str,
        on_delete: Any,
        to_field: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        return super().__init__(to, on_delete, to_field=None, **kwargs)

    class FixReverseOneToOneDescriptor(ReverseOneToOneDescriptor):
        def __get__(self, *args, **kwargs):
            try:
                return super().__get__(*args, **kwargs)
            except ObjectDoesNotExist:
                return None

    related_accessor_class = FixReverseOneToOneDescriptor
