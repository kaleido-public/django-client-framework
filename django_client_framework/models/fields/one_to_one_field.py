from __future__ import annotations

from typing import Generic, TypeVar

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import OneToOneField, ReverseOneToOneDescriptor

from ..abstract import DCFModel

T = TypeVar("T", bound=DCFModel)


class UniqueForeignKey(Generic[T], OneToOneField[T]):
    """
    This class fix django's OneToOneField's historical problem, where accessing
    through the reverse relation when the object does not exist would raise an
    ObjectDoesNotExist exception, instead of simply returning None.
    """

    class FixReverseOneToOneDescriptor(ReverseOneToOneDescriptor):
        def __get__(self, *args, **kwargs):
            try:
                return super().__get__(*args, **kwargs)
            except ObjectDoesNotExist:
                return None

    related_accessor_class = FixReverseOneToOneDescriptor
