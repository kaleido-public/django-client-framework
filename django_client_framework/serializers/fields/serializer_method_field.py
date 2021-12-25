from typing import TYPE_CHECKING, Any, Generic, TypeVar
from rest_framework import serializers as s
from rest_framework.fields import Field


_IN = TypeVar("_IN")  # Instance Type
_VT = TypeVar("_VT")  # Value Type
_DT = TypeVar("_DT")  # Data Type
_RP = TypeVar("_RP")  # Representation Type


class TypedSerializerMethodField(s.SerializerMethodField, Generic[_IN, _VT, _DT, _RP]):
    if TYPE_CHECKING:

        def __init__(self, type: Field[_IN, _VT, _DT, _RP], *args: Any, **kwargs: Any):
            self.type = type
            super().__init__(*args, **kwargs)

    else:

        def __init__(self, type: Field, *args: Any, **kwargs: Any):
            self.type = type
            super().__init__(*args, **kwargs)
